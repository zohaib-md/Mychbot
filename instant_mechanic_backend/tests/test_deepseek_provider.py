import io
import json
import urllib.error
from unittest.mock import MagicMock, patch
import pytest
from apps.chat.application.services.dependencies import get_ai_provider
from apps.chat.domain.entities import ConversationContext
from apps.chat.domain.enums import ConversationState
from apps.chat.infrastructure.ai.deepseek_provider import DeepSeekProvider
from apps.chat.infrastructure.ai.gemini_provider import FALLBACK_RESPONSE, GeminiProvider

URLOPEN = "apps.chat.infrastructure.ai.deepseek_provider.urllib.request.urlopen"

VALID = {
    "probable_causes": ["Worn brake pads", "Scored rotors"],
    "urgency_level": "yellow",
    "estimated_cost_range": "₹2,000 - ₹4,500",
    "recommended_service": "Brake inspection",
    "mechanic_notes": "Grinding usually means metal-on-metal contact.",
}


def api_response(content: dict | None) -> MagicMock:
    text = json.dumps(content) if content is not None else ""
    body = {"choices": [{"message": {"content": text}, "finish_reason": "stop"}]}
    response = MagicMock()
    response.read.return_value = json.dumps(body).encode("utf-8")
    response.__enter__.return_value = response
    return response


@pytest.fixture
def provider():
    return DeepSeekProvider(api_key="test-key", model_name="deepseek-flash")


@pytest.fixture
def context():
    return ConversationContext(
        session_id="test",
        state=ConversationState.DIAGNOSING_ISSUE,
        vehicle_make="Honda",
        symptom_description="grinding noise when braking | worse at high speed",
    )


class TestDeepSeekProviderSuccess:
    def test_parses_and_normalises_response(self, provider, context):
        with patch(URLOPEN, return_value=api_response(VALID)):
            result = provider.diagnose(context)
        assert result.urgency_level == "YELLOW"
        assert result.probable_causes == ["Worn brake pads", "Scored rotors"]
        assert result.estimated_cost_range == "₹2,000 - ₹4,500"

    def test_sends_json_mode_request_with_auth(self, provider, context):
        with patch(URLOPEN, return_value=api_response(VALID)) as urlopen:
            provider.diagnose(context)
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        assert request.full_url == "https://api.deepseek.com/chat/completions"
        assert request.get_header("Authorization") == "Bearer test-key"
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["thinking"] == {"type": "disabled"}
        assert "grinding noise" in payload["messages"][1]["content"]

    def test_mentions_attached_media_in_prompt(self, provider, context):
        context.pending_media_paths = ["/app/media/brake.mp4"]
        assert "attached 1" in provider._build_prompt(context)


class TestDeepSeekEmptyContentRetry:
    def test_retries_once_on_empty_content(self, provider, context):
        with patch(URLOPEN, side_effect=[api_response(None), api_response(VALID)]) as urlopen:
            result = provider.diagnose(context)
        assert urlopen.call_count == 2
        assert result.urgency_level == "YELLOW"

    def test_falls_back_after_two_empty_responses(self, provider, context):
        with patch(URLOPEN, side_effect=[api_response(None), api_response(None)]) as urlopen:
            assert provider.diagnose(context) == FALLBACK_RESPONSE
        assert urlopen.call_count == 2

    def test_no_retry_when_first_response_is_valid(self, provider, context):
        with patch(URLOPEN, return_value=api_response(VALID)) as urlopen:
            provider.diagnose(context)
        assert urlopen.call_count == 1


class TestDeepSeekProviderFallback:
    def test_http_error_returns_fallback(self, provider, context):
        error = urllib.error.HTTPError(
            "url", 402, "Payment Required", {}, io.BytesIO(b'{"error":"Insufficient Balance"}')
        )
        with patch(URLOPEN, side_effect=error):
            assert provider.diagnose(context) == FALLBACK_RESPONSE

    def test_timeout_returns_fallback(self, provider, context):
        with patch(URLOPEN, side_effect=TimeoutError()):
            assert provider.diagnose(context) == FALLBACK_RESPONSE

    def test_invalid_urgency_returns_fallback(self, provider, context):
        with patch(URLOPEN, return_value=api_response({**VALID, "urgency_level": "PURPLE"})):
            assert provider.diagnose(context) == FALLBACK_RESPONSE

    def test_missing_key_returns_fallback(self, provider, context):
        incomplete = {k: v for k, v in VALID.items() if k != "mechanic_notes"}
        with patch(URLOPEN, return_value=api_response(incomplete)):
            assert provider.diagnose(context) == FALLBACK_RESPONSE


class TestProviderSelection:
    def test_deepseek_selected_from_settings(self, settings):
        settings.AI_PROVIDER = "deepseek"
        assert isinstance(get_ai_provider(), DeepSeekProvider)

    def test_gemini_is_default(self, settings):
        settings.AI_PROVIDER = "gemini"
        with patch.object(GeminiProvider, "__init__", return_value=None):
            assert isinstance(get_ai_provider(), GeminiProvider)
