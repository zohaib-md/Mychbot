import logging
from apps.chat.application.interfaces.i_ai_provider import IAIProvider
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository
from apps.diagnosis.infrastructure.repositories.diagnosis_repository import DjangoDiagnosisRepository
from apps.chat.domain.entities import DiagnosisResult
from apps.chat.domain.enums import ConversationState
from apps.chat.domain.exceptions import ConversationStateError

logger = logging.getLogger(__name__)


class DiagnosisService:
    """Manual diagnosis trigger — for explicit POST /api/diagnosis/ calls."""

    def __init__(
        self,
        ai_provider: IAIProvider,
        conversation_repo: DjangoConversationRepository,
        diagnosis_repo: DjangoDiagnosisRepository,
    ):
        self.ai_provider = ai_provider
        self.conversation_repo = conversation_repo
        self.diagnosis_repo = diagnosis_repo

    def run_diagnosis(self, session_id: str) -> DiagnosisResult:
        context = self.conversation_repo.get_or_create(session_id)

        if not context.symptom_description:
            raise ConversationStateError(
                "No symptoms collected yet. Please describe your vehicle issue via /api/chat/ first."
            )

        # Return cached result if diagnosis already exists
        existing = self.diagnosis_repo.get_by_session(session_id)
        if existing:
            return DiagnosisResult(
                probable_causes=existing.probable_causes,
                urgency_level=existing.urgency_level,
                estimated_cost_range=existing.estimated_cost_range,
                recommended_service=existing.recommended_service,
                mechanic_notes=existing.mechanic_notes,
            )

        context.state = ConversationState.DIAGNOSING_ISSUE
        result = self.ai_provider.diagnose(context)
        self.diagnosis_repo.save(session_id, result)

        context.state = ConversationState.PRESENTING_DIAGNOSIS
        self.conversation_repo.update(context)

        logger.info("Manual diagnosis completed for session %s", session_id)
        return result
