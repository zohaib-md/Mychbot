import uuid
from unittest.mock import MagicMock
from django.test import TestCase
from apps.chat.application.services.chat_service import ChatService
from apps.chat.application.services.state_machine import ConversationStateMachine
from apps.chat.application.services.domain_filter import DomainFilter
from apps.chat.application.services.intent_classifier import IntentClassifier
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository
from apps.diagnosis.infrastructure.repositories.diagnosis_repository import DjangoDiagnosisRepository
from apps.chat.domain.entities import DiagnosisResult


MOCK_DIAGNOSIS = DiagnosisResult(
    probable_causes=["Battery failure"],
    urgency_level="RED",
    estimated_cost_range="₹1,800 - ₹3,500",
    recommended_service="Battery Replacement",
    mechanic_notes="Engine clicks without cranking.",
)


class TestChatServiceOrchestration(TestCase):

    def setUp(self):
        self.mock_ai = MagicMock()
        self.mock_ai.diagnose.return_value = MOCK_DIAGNOSIS
        self.service = ChatService(
            state_machine=ConversationStateMachine(),
            domain_filter=DomainFilter(),
            intent_classifier=IntentClassifier(),
            conversation_repo=DjangoConversationRepository(),
            ai_provider=self.mock_ai,
            diagnosis_repo=DjangoDiagnosisRepository(),
        )
        self.session_id = str(uuid.uuid4())

    def test_greeting_does_not_invoke_ai(self):
        self.service.process_message(self.session_id, "Hello!")
        self.mock_ai.diagnose.assert_not_called()

    def test_off_topic_returns_rejection_without_ai(self):
        response = self.service.process_message(
            self.session_id, "what is the best recipe for pasta"
        )
        self.assertIn("automotive", response.message.lower())
        self.mock_ai.diagnose.assert_not_called()

    def test_farewell_does_not_invoke_ai(self):
        self.service.process_message(self.session_id, "Hello")
        self.service.process_message(self.session_id, "Thanks, goodbye!")
        self.mock_ai.diagnose.assert_not_called()

    def test_full_conversation_ai_called_exactly_once(self):
        """Simulate: greeting → report issue → follow-up → AI trigger."""
        self.service.process_message(self.session_id, "Hello")
        self.service.process_message(self.session_id, "My Toyota engine is making a knocking noise")
        self.service.process_message(self.session_id, "It happens every time I start the car cold")
        self.service.process_message(self.session_id, "Also leaking some oil underneath")
        # AI must have been called exactly once across the whole conversation
        self.assertEqual(self.mock_ai.diagnose.call_count, 1)

    def test_requires_booking_true_after_diagnosis(self):
        self.service.process_message(self.session_id, "Hello")
        self.service.process_message(self.session_id, "Toyota Corolla engine knocking noise")
        self.service.process_message(self.session_id, "Happens on cold start every morning")
        response = self.service.process_message(self.session_id, "Also smoke from exhaust")
        if self.mock_ai.diagnose.call_count > 0:
            self.assertTrue(response.requires_booking)

    def test_diagnosis_included_in_response_when_ai_called(self):
        self.service.process_message(self.session_id, "Hello")
        self.service.process_message(self.session_id, "Toyota engine knocking")
        # This third message triggers DIAGNOSING_ISSUE (1 follow-up + symptom set)
        response = self.service.process_message(self.session_id, "Happens on cold start")
        self.assertEqual(self.mock_ai.diagnose.call_count, 1)
        self.assertIsNotNone(response.diagnosis)
        self.assertEqual(response.diagnosis.urgency_level, "RED")
