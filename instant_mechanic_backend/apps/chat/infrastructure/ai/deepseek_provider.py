import json
import logging
import urllib.error
import urllib.request
from apps.chat.application.interfaces.i_ai_provider import IAIProvider
from apps.chat.domain.entities import ConversationContext, DiagnosisResult
from apps.chat.infrastructure.ai.gemini_provider import FALLBACK_RESPONSE

logger = logging.getLogger(__name__)

URGENCY_LEVELS = {"GREEN", "YELLOW", "RED"}

SYSTEM_PROMPT = (
    "You are a senior automotive technician for Instant Mechanic, "
    "an on-demand car repair service. You always answer with a single JSON object "
    "and nothing else, using exactly these keys:\n"
    '{"probable_causes": [string, ...], '
    '"urgency_level": "GREEN" | "YELLOW" | "RED", '
    '"estimated_cost_range": string, '
    '"recommended_service": string, '
    '"mechanic_notes": string}'
)


class DeepSeekProvider(IAIProvider):
    """
    Concrete implementation of IAIProvider using DeepSeek's OpenAI-compatible
    Chat Completions API in JSON mode. Uses only the standard library.
    Text-only: attached media is mentioned in the prompt but not analysed.
    Same fallback contract as GeminiProvider: never raises from diagnose().
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        base_url: str = "https://api.deepseek.com",
        timeout: float = 60.0,
    ):
        self._api_key = api_key
        self._model_name = model_name
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._timeout = timeout

    def upload_media(self, file_path: str, mime_type: str) -> str:
        raise NotImplementedError("DeepSeek chat models do not accept media uploads.")

    def diagnose(self, context: ConversationContext) -> DiagnosisResult:
        """
        Entry point for diagnosis. Catches all API errors and returns
        FALLBACK_RESPONSE so the booking CTA always remains reachable.
        """
        try:
            return self._call_deepseek(context)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:300]
            logger.warning(
                "DeepSeek diagnosis failed (HTTP %s): %s — returning fallback response",
                e.code,
                body,
            )
        except Exception as e:
            logger.warning(
                "DeepSeek diagnosis failed (%s): %s — returning fallback response",
                type(e).__name__,
                e,
            )
        return FALLBACK_RESPONSE

    def _call_deepseek(self, context: ConversationContext) -> DiagnosisResult:
        # DeepSeek's JSON mode occasionally returns empty content; retry once.
        content = self._request_completion(context) or self._request_completion(context)
        return self._parse(json.loads(content))

    def _request_completion(self, context: ConversationContext) -> str:
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self._build_prompt(context)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 800,
        }
        request = urllib.request.Request(
            self._url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            body = json.loads(response.read().decode("utf-8"))

        content = (body["choices"][0]["message"].get("content") or "").strip()
        if not content:
            logger.info("DeepSeek returned empty content (finish_reason=%s)",
                        body["choices"][0].get("finish_reason"))
        return content

    def _parse(self, data: dict) -> DiagnosisResult:
        """Validate the model's JSON — JSON mode guarantees syntax, not our schema."""
        causes = data["probable_causes"]
        if isinstance(causes, str):
            causes = [causes]
        urgency = str(data["urgency_level"]).upper()
        if urgency not in URGENCY_LEVELS:
            raise ValueError(f"Invalid urgency_level: {urgency!r}")

        return DiagnosisResult(
            probable_causes=[str(c) for c in causes],
            urgency_level=urgency,
            estimated_cost_range=str(data["estimated_cost_range"]),
            recommended_service=str(data["recommended_service"]),
            mechanic_notes=str(data["mechanic_notes"]),
        )

    def _build_prompt(self, context: ConversationContext) -> str:
        vehicle = (
            f"{context.vehicle_make or 'Unknown make'} "
            f"{context.vehicle_model or 'Unknown model'}".strip()
        )
        media_count = len(context.pending_media_paths) + len(context.pending_media_uris)
        media_note = (
            f"The customer also attached {media_count} photo/audio/video file(s), "
            f"which you cannot see; mention in mechanic_notes that a mechanic will review them.\n"
            if media_count
            else ""
        )
        return (
            f"Vehicle: {vehicle}\n"
            f"Reported issue: {context.symptom_description or 'Not specified'}\n"
            f"{media_note}\n"
            f"Provide a structured diagnosis as JSON.\n"
            f"Be specific about probable causes (2-4 items). Set urgency_level to:\n"
            f"  GREEN  = safe to drive, schedule service soon\n"
            f"  YELLOW = caution, limit driving, book within 48h\n"
            f"  RED    = stop driving immediately, safety risk\n"
            f"Provide estimated_cost_range in Indian Rupees (₹), e.g. \"₹2,000 - ₹4,500\"."
        )
