import uuid
from datetime import datetime, timezone
from django.test import TestCase
from apps.chat.models import Conversation, Message, Media
from apps.diagnosis.models import Diagnosis
from apps.booking.models import Booking


class ConversationModelTest(TestCase):
    def test_creates_with_idle_state(self):
        conv = Conversation.objects.create()
        self.assertEqual(conv.state, "idle")

    def test_session_id_is_uuid(self):
        conv = Conversation.objects.create()
        self.assertIsInstance(conv.session_id, uuid.UUID)

    def test_str_representation(self):
        conv = Conversation.objects.create()
        self.assertIn("idle", str(conv))


class BookingModelTest(TestCase):
    def setUp(self):
        self.conv = Conversation.objects.create()

    def test_booking_id_is_uuid(self):
        b = Booking.objects.create(
            conversation=self.conv,
            customer_name="Test User",
            phone_number="9999999999",
            preferred_slot=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        self.assertIsInstance(b.booking_id, uuid.UUID)

    def test_default_status_is_pending(self):
        b = Booking.objects.create(
            conversation=self.conv,
            customer_name="Test",
            phone_number="1234567890",
            preferred_slot=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(b.status, "pending")


class DiagnosisModelTest(TestCase):
    def setUp(self):
        self.conv = Conversation.objects.create()

    def test_json_field_round_trips(self):
        causes = ["Battery failure", "Starter motor issue"]
        d = Diagnosis.objects.create(
            conversation=self.conv,
            probable_causes=causes,
            urgency_level="RED",
            estimated_cost_range="₹1,800 - ₹3,500",
            recommended_service="Battery Replacement",
            mechanic_notes="Engine clicks without cranking.",
        )
        d.refresh_from_db()
        self.assertEqual(d.probable_causes, causes)

    def test_urgency_level_choices(self):
        for level in ["GREEN", "YELLOW", "RED"]:
            d = Diagnosis.objects.create(
                conversation=Conversation.objects.create(),
                probable_causes=[],
                urgency_level=level,
                estimated_cost_range="₹500",
                recommended_service="Test",
                mechanic_notes="Test notes",
            )
            self.assertEqual(d.urgency_level, level)
