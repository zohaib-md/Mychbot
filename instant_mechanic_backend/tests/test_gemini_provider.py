import json
import pytest
from unittest.mock import MagicMock, patch
from apps.chat.infrastructure.ai.gemini_provider import GeminiProvider, FALLBACK_RESPONSE
from apps.chat.domain.entities import ConversationContext
from apps.chat.domain.enums import ConversationState


@pytest.fixture
def mock_provider():
    """Create a GeminiProvider with mocked internals — no real API calls."""
    with patch.object(GeminiProvider, "__init__", return_value=None):
        provider = GeminiProvider.__new__(GeminiProvider)
        provider._genai = MagicMock()
        provider._model_name = "gemini-1.5-flash"
        provider._model = MagicMock()
        yield provider


@pytest.fixture
def sample_context():
    return ConversationContext(
        session_id="test",
        state=ConversationState.DIAGNOSING_ISSUE,
        vehicle_make="Toyota",
        vehicle_model="Corolla",
        symptom_description="Engine knocking on startup",
        follow_up_rounds=1,
    )


VALID_RESPONSE_JSON = {
    "probable_causes": ["Starter motor failure", "Weak battery"],
    "urgency_level": "RED",
    "estimated_cost_range": "₹1,800 - ₹3,500",
    "recommended_service": "Battery Replacement",
    "mechanic_notes": "Engine clicks without cranking.",
}


class TestGeminiProviderFallback:
    def test_returns_fallback_on_generic_exception(self, mock_provider, sample_context):
        mock_provider._model.generate_content.side_effect = Exception("Rate limit exceeded")
        result = mock_provider.diagnose(sample_context)
        assert result == FALLBACK_RESPONSE

    def test_returns_fallback_on_timeout(self, mock_provider, sample_context):
        mock_provider._model.generate_content.side_effect = TimeoutError("Connection timed out")
        result = mock_provider.diagnose(sample_context)
        assert result == FALLBACK_RESPONSE

    def test_fallback_has_yellow_urgency(self):
        assert FALLBACK_RESPONSE.urgency_level == "YELLOW"

    def test_fallback_message_contains_booking_cta(self):
        assert "booking" in FALLBACK_RESPONSE.mechanic_notes.lower()

    def test_fallback_never_raises(self, mock_provider, sample_context):
        mock_provider._model.generate_content.side_effect = RuntimeError("Unexpected failure")
        result = mock_provider.diagnose(sample_context)
        assert result is not None


class TestGeminiProviderSuccess:
    def test_parses_valid_json_response(self, mock_provider, sample_context):
        mock_response = MagicMock()
        mock_response.text = json.dumps(VALID_RESPONSE_JSON)
        mock_provider._model.generate_content.return_value = mock_response

        result = mock_provider._call_gemini(sample_context)

        assert result.urgency_level == "RED"
        assert "Starter motor failure" in result.probable_causes
        assert result.estimated_cost_range == "₹1,800 - ₹3,500"

    def test_upload_media_not_called_when_no_pending_media(self, mock_provider, sample_context):
        mock_response = MagicMock()
        mock_response.text = json.dumps(VALID_RESPONSE_JSON)
        mock_provider._model.generate_content.return_value = mock_response
        mock_provider.upload_media = MagicMock()

        mock_provider._call_gemini(sample_context)

        mock_provider.upload_media.assert_not_called()

    def test_upload_media_called_for_pending_paths(self, mock_provider):
        mock_response = MagicMock()
        mock_response.text = json.dumps(VALID_RESPONSE_JSON)
        mock_provider._model.generate_content.return_value = mock_response
        mock_provider.upload_media = MagicMock(return_value="https://gemini.uri/file123")

        ctx = ConversationContext(
            session_id="test",
            state=ConversationState.DIAGNOSING_ISSUE,
            symptom_description="Engine knocking",
            follow_up_rounds=1,
            pending_media_paths=["/tmp/engine.jpg"],
        )
        mock_provider._call_gemini(ctx)

        mock_provider.upload_media.assert_called_once_with("/tmp/engine.jpg", "image/jpeg")
