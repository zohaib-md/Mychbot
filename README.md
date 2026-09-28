# Instant Mechanic — AI Car Diagnostic Chatbot

A chat assistant that triages car problems like a senior technician: it collects symptoms, accepts photos / audio / video of the fault, produces a structured diagnosis with an urgency rating (🟢 / 🟡 / 🔴) and a cost estimate, and books a mechanic visit.

The main design goal is **cost control**. It runs on the Gemini free tier, and a deterministic state machine decides whether a message needs the LLM at all. Gemini is called **once per conversation**, at the point where there's enough information to diagnose. Greetings, off-topic messages, follow-up questions and booking never reach the LLM.

| Layer | Stack |
|---|---|
| Backend | Django 5.1, Django REST Framework, SQLite, Google Gemini (`gemini-2.5-flash`), drf-spectacular |
| Frontend | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS |
| Deployment | Docker + Gunicorn on AWS EC2 (free tier), host Nginx + Let's Encrypt, frontend on Vercel |

**API docs:** Swagger UI at [`/api/docs/`](http://localhost:8000/api/docs/). The raw OpenAPI 3 schema is at `/api/schema/`.

---

## Contents

1. [Quick start (local)](#1-quick-start-local)
2. [Architecture](#2-architecture)
3. [How the state machine minimises Gemini calls](#3-how-the-state-machine-minimises-gemini-calls)
4. [API reference](#4-api-reference)
5. [Deployment (EC2 + Nginx + Vercel)](#5-deployment)
6. [Testing](#6-testing)
7. [Design decisions & trade-offs](#7-design-decisions--trade-offs)

---

## 1. Quick start (local)

### Prerequisites
- Python 3.12+
- Node.js 18.18+ (20 LTS recommended)
- A free Gemini API key from <https://aistudio.google.com/app/apikey>. This is optional: without one, diagnosis returns a safe fallback result and the rest of the app still works.

### Backend

```bash
cd instant_mechanic_backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # then set GEMINI_API_KEY
python manage.py migrate
python manage.py runserver      # http://localhost:8000
```

`manage.py` defaults to `config.settings.development`, which sets `DEBUG=True` and allows all CORS origins.

Open <http://localhost:8000/api/docs/> to try every endpoint from the browser.

### Frontend

```bash
cd instant_mechanic_frontend
npm install
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev                     # http://localhost:3000
```

### Running the production image locally (optional)

```bash
cd instant_mechanic_backend
cp .env.example .env            # set DJANGO_SECRET_KEY and GEMINI_API_KEY
docker compose up --build       # http://localhost:8000/api/docs/
```

`docker-compose.yml` runs the **production** settings over plain HTTP (with `SECURE_SSL_REDIRECT=False`) and allows CORS from `http://localhost:3000`. Migrations run automatically on container start.

### Environment variables (backend)

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | prod | dev-only key | Django signing key. Production refuses to start without it. |
| `GEMINI_API_KEY` | for AI | `""` | Gemini API key. If it's empty, diagnosis returns the fallback result. |
| `GEMINI_MODEL` | no | `gemini-2.5-flash` | Any Gemini model that supports JSON-schema output |
| `ALLOWED_HOSTS` | prod | `*` (dev) | Comma-separated, e.g. `13.233.10.20.nip.io` |
| `CORS_ALLOWED_ORIGINS` | prod | Vercel URL | Comma-separated frontend origins |
| `DATABASE_URL` | no | `sqlite:///db.sqlite3` | The Docker image sets `sqlite:////app/data/db.sqlite3` (on a volume) |
| `SECURE_SSL_REDIRECT` | no | `True` | Set to `False` until certbot has issued a certificate |

---

## 2. Architecture

### System overview

```
┌──────────────────────┐   HTTPS (JSON / multipart)   ┌──────────────────────────── AWS EC2 (t2/t3.micro) ───────────────────────────┐
│  Next.js on Vercel   │ ───────────────────────────▶ │  Nginx :443 (Let's Encrypt, 25 MB body limit, 120 s proxy timeout)           │
│  React chat UI       │                              │        │  /api/*, /health/                                                    │
└──────────────────────┘                              │        ▼                                                                      │
                                                      │  Docker: Gunicorn (2 workers) ─▶ Django + DRF                                 │
                                                      │        │                          │                                           │
                                                      │   volume: /app/data (SQLite)   volume: /app/media (uploads)                   │
                                                      └────────┼─────────────────────────────────────────────────────────────────────┘
                                                               │ only in DIAGNOSING_ISSUE
                                                               ▼
                                                       Google Gemini API (File API + structured JSON output)
```

### Backend: Clean Architecture

Each Django app (`chat`, `diagnosis`, `booking`) is split into four layers. Dependencies only point inwards.

```
presentation/     DRF views + serializers: HTTP in/out, validation, OpenAPI annotations
      │
application/      Use-case services (ChatService, DiagnosisService, BookingService, MediaService),
      │           the StateMachine, IntentClassifier, DomainFilter, and interfaces (IAIProvider,
      │           IConversationRepository). No Django ORM, no HTTP.
      ▼
domain/           Pure Python: dataclass entities (ConversationContext, DiagnosisResult, …),
                  enums (ConversationState, Intent), and domain exceptions. Zero dependencies.
      ▲
infrastructure/   Implementations of the interfaces: Django ORM repositories, GeminiProvider,
                  MediaHandler (file validation and storage).
```

- The state machine, intent classifier and domain filter import **no Django and no LLM code**. They're plain functions over dataclasses, so they're unit-tested in milliseconds.
- `GeminiProvider` implements `IAIProvider`. Switching to another LLM, or to a mock in tests, means writing one class and changing `application/services/dependencies.py`.
- Domain exceptions (`MediaValidationError`, `ConversationStateError`, …) are converted to structured JSON (`{"error", "code"}` with 400 or 409) in one place: `common/exception_handler.py`.

### Frontend: the same layering

```
app/                      Next.js App Router entry (page.tsx renders <ChatShell/>)
presentation/components/  chat/ (ChatShell, MessageList, MessageBubble, InputBar, TypingIndicator)
                          diagnosis/ (DiagnosisCard, UrgencyBadge), booking/ (BookingCTA, BookingModal)
application/              hooks: useChat, useUpload, useBooking; services/api.ts (typed API facade)
domain/                   TypeScript types mirroring the backend contracts
infrastructure/http/      fetch wrapper (apiClient.ts) with typed ApiError
```

Components never call `fetch` themselves. They use hooks, the hooks use `chatApi`, and `chatApi` uses `apiClient`. The UI checks file type and the 20 MB size limit before uploading, and the server checks them again.

---

## 3. How the state machine minimises Gemini calls

A naive chatbot sends **every** message to the LLM. On the Gemini free tier, with its requests-per-minute and requests-per-day limits, that uses up the quota on "hi", "thanks" and off-topic questions, and makes every reply slow.

Instant Mechanic puts a **three-stage deterministic pipeline** in front of the LLM (`apps/chat/application/services/chat_service.py`):

```
 user message
     │
     ▼
 ① DomainFilter ── off-topic? ──────────────▶ canned rejection            (0 LLM calls)
     │  regex hard-rejects (stocks, recipes, sports…) + automotive keyword scoring;
     │  context-aware: follow-up answers mid-conversation get the benefit of the doubt
     ▼
 ② IntentClassifier ── regex → GREETING / REPORT_ISSUE / UPLOAD_MEDIA / BOOK_MECHANIC / FAREWELL / OFF_TOPIC / UNCLEAR
     │
     ▼
 ③ ConversationStateMachine ── lookup table: (current_state, intent) → next_state
     │                          + templated reply for that state        (0 LLM calls)
     │
     │  guard: _symptoms_sufficient()  =  symptom text present AND ≥ 1 follow-up round
     ▼
   requires_ai_call = (next_state == DIAGNOSING_ISSUE)   ◀── the ONLY way to reach Gemini
     │
     ▼
 GeminiProvider.diagnose()  → one structured-JSON call (text + any uploaded media)
     │                        → result persisted, state → PRESENTING_DIAGNOSIS
     ▼
 booking CTA shown (requires_booking = true)
```

### The states

| State | Entered when | Reply source |
|---|---|---|
| `idle` | new session / farewell | template |
| `greeting_handled` | "hi", "hello"… | template |
| `rejected` | off-topic | template |
| `collecting_symptoms` | first symptom report | template: asks for make/model and when it happens |
| `awaiting_media` | "I'll send a photo" | template |
| **`diagnosing_issue`** | **guard passes** | **Gemini** |
| `presenting_diagnosis` | after diagnosis | Gemini result, formatted |
| `booking_initiated` / `collecting_booking_details` | "book a mechanic" | template |
| `booking_confirmed` | `POST /api/booking/` succeeds | template |

The transition table is a plain `dict` (`TRANSITION_TABLE` in `state_machine.py`), so adding a state or intent means adding a row, not an `if` branch. Unknown `(state, intent)` pairs fall back conservatively: the conversation stays in the current state or returns to `idle`, and the LLM is never called.

### Why this saves money

For a typical conversation:

| # | User says | Naive bot | Instant Mechanic |
|---|---|---|---|
| 1 | "Hi" | 1 LLM call | template |
| 2 | "My Honda makes a grinding noise when braking" | 1 | template (asks a follow-up) |
| 3 | "Started last week, worse at high speed" | 1 | **1 Gemini call**, structured diagnosis |
| 4 | "Can I book a mechanic?" | 1 | template |
| 5 | "What's the best stock to buy?" | 1 | regex rejection |
| | **Total** | **5** | **1 (-80%)** |

More savings on top of the state machine:

- **Uploads don't call Gemini.** `POST /api/upload/` only validates the file and stores it on disk. It is sent to the Gemini File API **later, during the single diagnosis call**, so abandoned conversations never use Gemini quota.
- **Structured output.** Gemini is called with `response_mime_type="application/json"` and a `response_schema`, so the answer parses in one shot. There's no retry loop to fix malformed output and no second summarisation call.
- **Diagnosis caching.** `POST /api/diagnosis/` returns the stored result if the session already has one.
- **Graceful degradation.** If Gemini times out, hits a rate limit or has no key, `GeminiProvider.diagnose()` returns a safe 🟡 "manual inspection" result. The user can still book a mechanic, and the API never returns a 500 because of the LLM.
- **Guard before cost.** `_symptoms_sufficient()` requires at least one follow-up round. This avoids spending a call on a vague one-liner, and the diagnosis is better because it has more context.

---

## 4. API reference

Interactive docs: **`/api/docs/`** (Swagger UI, generated by drf-spectacular from the serializers and `@extend_schema` annotations).

| Method | Path | Description | LLM? |
|---|---|---|---|
| `POST` | `/api/chat/` | `{session_id: uuid, message}` → `{message, state, requires_booking, diagnosis \| null}` | only in `diagnosing_issue` |
| `POST` | `/api/upload/` | multipart `session_id`, `file` (jpg/png/mp3/wav/mp4, ≤ 20 MB) → `{media_id, status}` | never |
| `POST` | `/api/diagnosis/` | `{session_id}` → diagnosis (cached if one exists) | if not cached |
| `POST` | `/api/booking/` | `{session_id, customer_name, phone_number, preferred_slot (ISO 8601)}` → `{booking_id, status, message}` | never |
| `GET` | `/api/booking/{uuid}/` | booking details | never |
| `GET` | `/health/` | liveness probe → `{"status": "ok"}` | never |
| `GET` | `/api/schema/` · `/api/docs/` | OpenAPI 3 schema · Swagger UI | — |

**Errors** are always JSON: validation errors return `400` with DRF field errors. Domain errors return `{"error": "...", "code": "invalid_media" | "invalid_state" | ...}` with status `400` or `409`. An unknown booking returns `404`.

The session is a client-generated UUID v4 (`crypto.randomUUID()`), so no auth or cookies are needed.

---

## 5. Deployment

### 5.1 Backend on AWS EC2 (free tier)

**1. Launch an instance.** Use Ubuntu 24.04 on a t2.micro or t3.micro. In the security group, open **22** (your IP only), **80** and **443**. Keep 8000 closed, because Gunicorn only binds to `127.0.0.1`.

**2. Install Docker, Nginx and Certbot.**

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx git
sudo usermod -aG docker $USER && newgrp docker

# t2.micro has 1 GB RAM: add swap so the image build doesn't get OOM-killed
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**3. Clone and configure.**

```bash
git clone https://github.com/zohaib-md/Mychbot.git && cd Mychbot/instant_mechanic_backend
cp .env.example .env
nano .env
```

Production `.env` (replace `13.233.10.20` with your instance's public IP; [nip.io](https://nip.io) gives a free hostname for it, which Let's Encrypt needs):

```ini
DJANGO_SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(50))">
GEMINI_API_KEY=<your key>
GEMINI_MODEL=gemini-2.5-flash
ALLOWED_HOSTS=13.233.10.20.nip.io
CORS_ALLOWED_ORIGINS=https://<your-app>.vercel.app
SECURE_SSL_REDIRECT=False        # flip to True after step 6
```

**4. Start the API.**

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps        # should become "healthy"
curl http://127.0.0.1:8000/health/                  # {"status": "ok"}
```

The container runs `migrate` automatically on start. SQLite lives on the `sqlite_data` volume and uploads live on the `media_data` volume, so both survive rebuilds.

**5. Configure Nginx.**

```bash
sudo cp ../deployment/nginx.conf /etc/nginx/sites-available/instant_mechanic
sudo sed -i 's/server_name _;/server_name 13.233.10.20.nip.io;/' /etc/nginx/sites-available/instant_mechanic
sudo ln -s /etc/nginx/sites-available/instant_mechanic /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

**6. Enable HTTPS, then turn on the SSL redirect.**

```bash
sudo certbot --nginx -d 13.233.10.20.nip.io --redirect --agree-tos -m you@example.com
sed -i 's/^SECURE_SSL_REDIRECT=.*/SECURE_SSL_REDIRECT=True/' .env
docker compose -f docker-compose.prod.yml up -d      # recreate with the new env
```

Check <https://13.233.10.20.nip.io/api/docs/>. Certbot sets up automatic renewal (`systemctl list-timers | grep certbot`).

> **Why the SSL redirect waits until step 6:** Django's `SECURE_SSL_REDIRECT` redirects any request that doesn't arrive with `X-Forwarded-Proto: https`. Turning it on before a certificate exists sends every request into a redirect to a port that isn't serving yet. `/health/` is exempt, so Docker's healthcheck works either way.

**Updating the deployment:**

```bash
git pull && docker compose -f docker-compose.prod.yml up -d --build
```

### 5.2 Frontend on Vercel

1. Import the GitHub repo into Vercel and set **Root Directory** to `instant_mechanic_frontend`. The framework (Next.js) is detected automatically.
2. Add an environment variable: `NEXT_PUBLIC_API_BASE_URL=https://13.233.10.20.nip.io`, with no trailing slash.
3. Deploy, then copy the Vercel URL into the backend's `CORS_ALLOWED_ORIGINS` and run `docker compose -f docker-compose.prod.yml up -d`.

> The `NEXT_PUBLIC_*` variable is baked in at build time, so if you change it, redeploy on Vercel.

### 5.3 Deployment files

| File | Purpose |
|---|---|
| `instant_mechanic_backend/Dockerfile` | `python:3.12-slim`, non-root user, `HEALTHCHECK` on `/health/`, Gunicorn with 2 workers and a 120 s timeout |
| `instant_mechanic_backend/entrypoint.sh` | Runs `migrate --noinput`, then starts Gunicorn |
| `instant_mechanic_backend/docker-compose.yml` | Local run of the production image over HTTP |
| `instant_mechanic_backend/docker-compose.prod.yml` | EC2: binds only to `127.0.0.1:8000`, `restart: always`, log rotation |
| `deployment/nginx.conf` | Reverse proxy for `/api/` and `/health/`, 25 MB upload limit, 120 s read timeout |

---

## 6. Testing

```bash
cd instant_mechanic_backend && source .venv/bin/activate
pytest                          # full suite; runs in about a second, Gemini is mocked
```

| File | Covers |
|---|---|
| `test_state_machine.py` | Every transition, the diagnosis guard, and the fallback behaviour |
| `test_domain_filter.py` | Off-topic rejection, keyword matching, context-aware follow-ups, intent classification |
| `test_chat_service.py` | Pipeline orchestration: that Gemini is called only when authorised |
| `test_gemini_provider.py` | Prompt building, JSON parsing, fallback on errors and rate limits |
| `test_repositories.py`, `test_models.py`, `test_domain.py` | Persistence and entities |
| `test_api_e2e.py` | Full HTTP flows: greeting → symptoms → diagnosis → booking, and error mapping (400 / 404 / 409) |

Frontend checks:

```bash
cd instant_mechanic_frontend && npm run lint && npx tsc --noEmit && npm run build
```

---

## 7. Design decisions & trade-offs

- **Regex plus a state machine instead of an LLM router.** Routing is deterministic, free, fast (microseconds) and fully unit-testable. The trade-off is that unusual phrasing can be misclassified. That is mitigated by context-aware fallbacks: while symptoms are being collected, any plain text counts as more symptom detail.
- **SQLite in production.** It's enough for a demo on a single free-tier instance with 2 Gunicorn workers, and it needs no managed database. The data lives on a Docker volume. Moving to Postgres means setting `DATABASE_URL`, because the settings already use `dj-database-url`.
- **Media is not served publicly.** Uploads are only read server-side and forwarded to Gemini during diagnosis, so Nginx deliberately doesn't expose `/media/`.
- **No auth or CSRF.** The API is stateless JSON with no cookies, and a session is an unguessable UUID v4. `manage.py check --deploy` still reports W003 (CSRF middleware) and W004 (HSTS). Both are deliberate: CSRF doesn't apply without cookie auth, and HSTS is risky to turn on for a throwaway nip.io hostname.
- **Server-side CORS instead of a Next.js proxy.** The browser talks to the API directly, which keeps Vercel function time and cost at zero. Django allows only the configured origins.
