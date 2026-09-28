import json
import logging
from apps.chat.application.interfaces.i_ai_provider import IAIProvider
from apps.chat.domain.entities import ConversationContext, DiagnosisResult

logger = logging.getLogger(__name__)

DIAGNOSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "probable_causes": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
        "urgency_level": {
            "type": "STRING",
            "enum": ["GREEN", "YELLOW", "RED"],
        },
        "estimated_cost_range": {"type": "STRING"},
        "recommended_service": {"type": "STRING"},
        "mechanic_notes": {"type": "STRING"},
    },
    "required": [
        "probable_causes",
        "urgency_level",
        "estimated_cost_range",
        "recommended_service",
        "mechanic_notes",
    ],
}

FALLBACK_RESPONSE = DiagnosisResult(
    probable_causes=["Unable to determine — manual inspection required"],
    urgency_level="YELLOW",
    estimated_cost_range="Contact mechanic for estimate",
    recommended_service="On-site inspection by verified Instant Mechanic",
    mechanic_notes=(
        "Our AI service is experiencing high load. Based on your symptoms, "
        "we recommend booking a verified Instant Mechanic for an on-site inspection."
    ),
)


class GeminiProvider(IAIProvider):
    """
    Concrete implementation of IAIProvider using Google Gemini.
    Single Responsibility: AI communication only.
    Fallback handler ensures graceful degradation under rate limits / timeouts.
    """

    def __init__(self, api_key: str, model_name: str):
        import google.generativeai as genai
        self._genai = genai
        genai.configure(api_key=api_key)
        self._model_name = model_name
        self._model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=DIAGNOSIS_SCHEMA,
            ),
        )

    def upload_media(self, file_path: str, mime_type: str) -> str:
        """Upload file to Gemini File API. Called ONLY during DIAGNOSING_ISSUE."""
        try:
            uploaded = self._genai.upload_file(path=file_path, mime_type=mime_type)
            logger.info("Uploaded media to Gemini: %s", uploaded.uri)
            return uploaded.uri
        except Exception as e:
            logger.error("Gemini media upload failed: %s", e)
            raise

    def diagnose(self, context: ConversationContext) -> DiagnosisResult:
        """
        Entry point for diagnosis. Catches all Gemini errors and returns
        FALLBACK_RESPONSE so the booking CTA always remains reachable.
        """
        try:
            return self._call_gemini(context)
        except Exception as e:
            error_name = type(e).__name__
            logger.warning(
                "Gemini diagnosis failed (%s): %s — returning fallback response",
                error_name,
                e,
            )
            return FALLBACK_RESPONSE

    def _call_gemini(self, context: ConversationContext) -> DiagnosisResult:
        """Build prompt, attach media if present, call Gemini, parse structured response."""
        content_parts = [self._build_prompt(context)]

        # Attach already-uploaded Gemini URIs
        for uri in context.pending_media_uris:
            content_parts.append({"file_data": {"file_uri": uri}})

        # Upload local files staged during this session
        for file_path in context.pending_media_paths:
            try:
                mime_type = self._infer_mime_type(file_path)
                uri = self.upload_media(file_path, mime_type)
                content_parts.append({"file_data": {"file_uri": uri}})
            except Exception as e:
                logger.warning("Skipping media file %s due to upload error: %s", file_path, e)

        response = self._model.generate_content(content_parts)
        data = json.loads(response.text)

        return DiagnosisResult(
            probable_causes=data["probable_causes"],
            urgency_level=data["urgency_level"],
            estimated_cost_range=data["estimated_cost_range"],
            recommended_service=data["recommended_service"],
            mechanic_notes=data["mechanic_notes"],
        )

    def _build_prompt(self, context: ConversationContext) -> str:
        vehicle = (
            f"{context.vehicle_make or 'Unknown make'} "
            f"{context.vehicle_model or 'Unknown model'}".strip()
        )
        return (
            f"You are a senior automotive technician for Instant Mechanic, "
            f"an on-demand car repair service.\n\n"
            f"Vehicle: {vehicle}\n"
            f"Reported issue: {context.symptom_description or 'Not specified'}\n\n"
            f"Based on the above information and any attached media, provide a structured diagnosis.\n"
            f"Be specific about probable causes. Set urgency_level to:\n"
            f"  GREEN  = safe to drive, schedule service soon\n"
            f"  YELLOW = caution, limit driving, book within 48h\n"
            f"  RED    = stop driving immediately, safety risk\n"
            f"Provide estimated_cost_range in Indian Rupees (₹).\n"
            f"Respond ONLY with valid JSON matching the required schema."
        )

    def _infer_mime_type(self, file_path: str) -> str:
        ext = file_path.lower().rsplit(".", 1)[-1]
        return {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "mp4": "video/mp4",
        }.get(ext, "application/octet-stream")
