import uuid
from django.test import TestCase
from apps.chat.models import Conversation
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository
from apps.diagnosis.infrastructure.repositories.diagnosis_repository import DjangoDiagnosisRepository
from apps.chat.domain.entities import DiagnosisResult
from apps.chat.domain.enums import ConversationState


class TestConversationRepository(TestCase):

    def setUp(self):
        self.repo = DjangoConversationRepository()
        self.session_id = str(uuid.uuid4())

    def test_get_or_create_new_session(self):
        ctx = self.repo.get_or_create(self.session_id)
        self.assertEqual(str(ctx.session_id), self.session_id)
        self.assertEqual(ctx.state, ConversationState.IDLE)

    def test_get_or_create_existing_session_returns_same(self):
        self.repo.get_or_create(self.session_id)
        self.repo.get_or_create(self.session_id)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_update_persists_state(self):
        ctx = self.repo.get_or_create(self.session_id)
        ctx.state = ConversationState.COLLECTING_SYMPTOMS
        ctx.vehicle_make = "Toyota"
        self.repo.update(ctx)
        updated = Conversation.objects.get(session_id=uuid.UUID(self.session_id))
        self.assertEqual(updated.state, "collecting_symptoms")
        self.assertEqual(updated.vehicle_make, "Toyota")

    def test_update_persists_follow_up_rounds(self):
        ctx = self.repo.get_or_create(self.session_id)
        ctx.follow_up_rounds = 3
        self.repo.update(ctx)
        updated = Conversation.objects.get(session_id=uuid.UUID(self.session_id))
        self.assertEqual(updated.follow_up_rounds, 3)

    def test_append_message_creates_correct_role(self):
        self.repo.get_or_create(self.session_id)
        self.repo.append_message(self.session_id, "user", "My engine is knocking")
        self.repo.append_message(self.session_id, "bot", "Can you describe when it occurs?")
        from apps.chat.models import Message
        messages = list(Message.objects.filter(
            conversation__session_id=uuid.UUID(self.session_id)
        ).order_by("created_at"))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[1].role, "bot")
        self.assertEqual(messages[0].content, "My engine is knocking")


class TestDiagnosisRepository(TestCase):

    def setUp(self):
        self.repo = DjangoDiagnosisRepository()
        self.conv_repo = DjangoConversationRepository()
        self.session_id = str(uuid.uuid4())
        self.conv_repo.get_or_create(self.session_id)

    def test_save_and_get_by_session(self):
        result = DiagnosisResult(
            probable_causes=["Battery failure"],
            urgency_level="RED",
            estimated_cost_range="₹1,800",
            recommended_service="Battery Replacement",
            mechanic_notes="Engine clicks.",
        )
        self.repo.save(self.session_id, result)
        fetched = self.repo.get_by_session(self.session_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.urgency_level, "RED")
        self.assertEqual(fetched.probable_causes, ["Battery failure"])

    def test_get_by_session_returns_none_when_missing(self):
        result = self.repo.get_by_session(str(uuid.uuid4()))
        self.assertIsNone(result)

    def test_save_is_idempotent(self):
        result = DiagnosisResult(
            probable_causes=["Cause 1"],
            urgency_level="GREEN",
            estimated_cost_range="₹500",
            recommended_service="Inspection",
            mechanic_notes="Minor issue.",
        )
        self.repo.save(self.session_id, result)
        # Update — should not create duplicate
        result2 = DiagnosisResult(
            probable_causes=["Cause 2"],
            urgency_level="YELLOW",
            estimated_cost_range="₹1,000",
            recommended_service="Service",
            mechanic_notes="Needs attention.",
        )
        self.repo.save(self.session_id, result2)
        from apps.diagnosis.models import Diagnosis
        count = Diagnosis.objects.filter(
            conversation__session_id=uuid.UUID(self.session_id)
        ).count()
        self.assertEqual(count, 1)
