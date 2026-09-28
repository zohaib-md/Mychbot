from django.conf import settings
from apps.chat.application.services.chat_service import ChatService
from apps.chat.application.services.state_machine import ConversationStateMachine
from apps.chat.application.services.domain_filter import DomainFilter
from apps.chat.application.services.intent_classifier import IntentClassifier
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository
from apps.chat.infrastructure.ai.gemini_provider import GeminiProvider
from apps.diagnosis.infrastructure.repositories.diagnosis_repository import DjangoDiagnosisRepository


def get_chat_service() -> ChatService:
    return ChatService(
        state_machine=ConversationStateMachine(),
        domain_filter=DomainFilter(),
        intent_classifier=IntentClassifier(),
        conversation_repo=DjangoConversationRepository(),
        ai_provider=GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL,
        ),
        diagnosis_repo=DjangoDiagnosisRepository(),
    )
