from django.conf import settings
from apps.chat.application.interfaces.i_ai_provider import IAIProvider
from apps.chat.application.services.chat_service import ChatService
from apps.chat.application.services.state_machine import ConversationStateMachine
from apps.chat.application.services.domain_filter import DomainFilter
from apps.chat.application.services.intent_classifier import IntentClassifier
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository
from apps.chat.infrastructure.ai.gemini_provider import GeminiProvider
from apps.chat.infrastructure.ai.deepseek_provider import DeepSeekProvider
from apps.diagnosis.infrastructure.repositories.diagnosis_repository import DjangoDiagnosisRepository


def get_ai_provider() -> IAIProvider:
    """Select the LLM backend from settings.AI_PROVIDER ("gemini" | "deepseek")."""
    if settings.AI_PROVIDER == "deepseek":
        return DeepSeekProvider(
            api_key=settings.DEEPSEEK_API_KEY,
            model_name=settings.DEEPSEEK_MODEL,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
    return GeminiProvider(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL,
    )


def get_chat_service() -> ChatService:
    return ChatService(
        state_machine=ConversationStateMachine(),
        domain_filter=DomainFilter(),
        intent_classifier=IntentClassifier(),
        conversation_repo=DjangoConversationRepository(),
        ai_provider=get_ai_provider(),
        diagnosis_repo=DjangoDiagnosisRepository(),
    )
