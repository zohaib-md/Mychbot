import logging
from apps.chat.application.interfaces.i_conversation_repository import IConversationRepository
from apps.chat.application.interfaces.i_ai_provider import IAIProvider
from apps.chat.application.services.state_machine import ConversationStateMachine
from apps.chat.application.services.domain_filter import DomainFilter
from apps.chat.application.services.intent_classifier import IntentClassifier
from apps.chat.domain.entities import ChatResponse, DiagnosisResult
from apps.chat.domain.enums import ConversationState

logger = logging.getLogger(__name__)

REJECTION_MESSAGE = (
    "I'm specialised in automotive issues only. "
    "Please describe a problem with your vehicle and I'll be happy to help."
)


class ChatService:
    """
    Orchestrates the full message processing pipeline.
    Open/Closed: adding new intents or states doesn't require modifying this class.
    """

    def __init__(
        self,
        state_machine: ConversationStateMachine,
        domain_filter: DomainFilter,
        intent_classifier: IntentClassifier,
        conversation_repo: IConversationRepository,
        ai_provider: IAIProvider,
        diagnosis_repo,
    ):
        self.state_machine = state_machine
        self.domain_filter = domain_filter
        self.intent_classifier = intent_classifier
        self.conversation_repo = conversation_repo
        self.ai_provider = ai_provider
        self.diagnosis_repo = diagnosis_repo

    def process_message(self, session_id: str, message: str) -> ChatResponse:
        # 1. Load conversation context
        context = self.conversation_repo.get_or_create(session_id)

        # 2. Save user message
        self.conversation_repo.append_message(session_id, "user", message)

        # 3. Domain filter — early exit, zero AI cost
        if not self.domain_filter.is_automotive(message, context):
            self.conversation_repo.append_message(session_id, "bot", REJECTION_MESSAGE)
            return ChatResponse(
                message=REJECTION_MESSAGE,
                state=ConversationState.REJECTED.value,
                requires_booking=False,
            )

        # 4. Classify intent — pure regex, zero AI cost
        intent = self.intent_classifier.classify(message, context)
        logger.debug("Session %s: intent=%s state=%s", session_id, intent, context.state)

        # 5. State machine transition — zero AI cost
        transition = self.state_machine.transition(context.state, intent, context, message)

        # 6. Conditional AI invocation — ONLY when state machine authorizes it
        diagnosis: DiagnosisResult | None = None
        if transition.requires_ai_call:
            logger.info("Session %s: invoking Gemini diagnosis", session_id)
            diagnosis = self.ai_provider.diagnose(transition.updated_context)
            self.diagnosis_repo.save(session_id, diagnosis)
            response_text = self._format_diagnosis(diagnosis)
            transition.updated_context.state = ConversationState.PRESENTING_DIAGNOSIS
        else:
            response_text = transition.response_template

        # 7. Persist updated context and bot response
        self.conversation_repo.update(transition.updated_context)
        self.conversation_repo.append_message(session_id, "bot", response_text)

        return ChatResponse(
            message=response_text,
            state=transition.updated_context.state.value,
            requires_booking=(
                transition.updated_context.state == ConversationState.PRESENTING_DIAGNOSIS
            ),
            diagnosis=diagnosis,
        )

    def _format_diagnosis(self, diagnosis: DiagnosisResult) -> str:
        urgency_labels = {
            "GREEN": "🟢 SAFE TO DRIVE",
            "YELLOW": "🟡 CAUTION — LIMIT DRIVING",
            "RED": "🔴 STOP DRIVING IMMEDIATELY",
        }
        causes = "\n".join(f"  • {c}" for c in diagnosis.probable_causes)
        return (
            f"**Diagnosis Complete**\n\n"
            f"**Urgency:** {urgency_labels.get(diagnosis.urgency_level, diagnosis.urgency_level)}\n\n"
            f"**Probable Causes:**\n{causes}\n\n"
            f"**Recommended Service:** {diagnosis.recommended_service}\n"
            f"**Estimated Cost:** {diagnosis.estimated_cost_range}\n\n"
            f"**Mechanic Notes:** {diagnosis.mechanic_notes}\n\n"
            f"Would you like to book a verified Instant Mechanic for an on-site inspection?"
        )
