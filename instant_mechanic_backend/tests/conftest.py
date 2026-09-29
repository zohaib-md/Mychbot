import pytest


@pytest.fixture(autouse=True)
def _default_ai_provider(settings):
    # Tests mock GeminiProvider; don't let a developer's .env
    # (e.g. AI_PROVIDER=deepseek) route tests to a real API.
    settings.AI_PROVIDER = "gemini"
