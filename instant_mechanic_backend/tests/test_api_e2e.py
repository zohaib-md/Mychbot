import uuid
from unittest.mock import MagicMock, patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from apps.chat.domain.entities import DiagnosisResult


MOCK_DIAGNOSIS = DiagnosisResult(
    probable_causes=["Battery failure", "Starter motor issue"],
    urgency_level="RED",
    estimated_cost_range="₹1,800 - ₹3,500",
    recommended_service="Battery Replacement",
    mechanic_notes="Engine clicks without cranking.",
)


class TestFullConversationFlow(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.session_id = str(uuid.uuid4())

    @patch("apps.chat.application.services.dependencies.GeminiProvider")
    def test_greeting_returns_200(self, MockGemini):
        MockGemini.return_value = MagicMock()
        r = self.client.post(
            "/api/chat/",
            {"session_id": self.session_id, "message": "Hello"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["requires_booking"])
        self.assertIn("state", r.data)

    @patch("apps.chat.application.services.dependencies.GeminiProvider")
    def test_off_topic_rejected_gracefully(self, MockGemini):
        MockGemini.return_value = MagicMock()
        r = self.client.post(
            "/api/chat/",
            {"session_id": self.session_id, "message": "tell me a recipe"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("automotive", r.data["message"].lower())

    def test_invalid_uuid_returns_400(self):
        r = self.client.post(
            "/api/chat/",
            {"session_id": "not-a-uuid", "message": "hello"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    def test_booking_create_and_retrieve(self):
        # Create booking directly (no need to go through full chat flow)
        r_create = self.client.post("/api/booking/", {
            "session_id": self.session_id,
            "customer_name": "Test User",
            "phone_number": "9999999999",
            "preferred_slot": "2025-01-15T10:00:00Z",
        }, format="json")
        self.assertEqual(r_create.status_code, 201)
        booking_id = r_create.data["booking_id"]
        self.assertIsNotNone(booking_id)
        self.assertEqual(r_create.data["status"], "confirmed")

        # Retrieve booking
        r_get = self.client.get(f"/api/booking/{booking_id}/")
        self.assertEqual(r_get.status_code, 200)
        self.assertEqual(r_get.data["customer_name"], "Test User")
        self.assertEqual(r_get.data["status"], "confirmed")

    def test_get_nonexistent_booking_returns_404(self):
        fake_id = str(uuid.uuid4())
        r = self.client.get(f"/api/booking/{fake_id}/")
        self.assertEqual(r.status_code, 404)

    @patch("apps.chat.application.services.dependencies.GeminiProvider")
    def test_full_e2e_flow(self, MockGemini):
        mock_provider = MagicMock()
        mock_provider.diagnose.return_value = MOCK_DIAGNOSIS
        MockGemini.return_value = mock_provider

        # Step 1: Greeting
        r1 = self.client.post("/api/chat/", {
            "session_id": self.session_id, "message": "Hello"
        }, format="json")
        self.assertEqual(r1.status_code, 200)

        # Step 2: Report issue
        r2 = self.client.post("/api/chat/", {
            "session_id": self.session_id,
            "message": "My Toyota engine is knocking"
        }, format="json")
        self.assertEqual(r2.status_code, 200)

        # Step 3: Follow-up
        r3 = self.client.post("/api/chat/", {
            "session_id": self.session_id,
            "message": "It happens on cold starts every morning"
        }, format="json")
        self.assertEqual(r3.status_code, 200)

        # Step 4: Book mechanic
        r4 = self.client.post("/api/booking/", {
            "session_id": self.session_id,
            "customer_name": "Test User",
            "phone_number": "9999999999",
            "preferred_slot": "2025-01-15T10:00:00Z",
        }, format="json")
        self.assertEqual(r4.status_code, 201)
        booking_id = r4.data["booking_id"]

        # Step 5: Retrieve booking
        r5 = self.client.get(f"/api/booking/{booking_id}/")
        self.assertEqual(r5.status_code, 200)
        self.assertEqual(r5.data["status"], "confirmed")

    @patch("apps.chat.application.services.dependencies.GeminiProvider")
    def test_keywordless_follow_up_reaches_diagnosis(self, MockGemini):
        mock_provider = MagicMock()
        mock_provider.diagnose.return_value = MOCK_DIAGNOSIS
        MockGemini.return_value = mock_provider

        self.client.post("/api/chat/", {
            "session_id": self.session_id,
            "message": "my Honda City makes a grinding noise when braking",
        }, format="json")
        r = self.client.post("/api/chat/", {
            "session_id": self.session_id,
            "message": "it started last week and gets worse at high speed",
        }, format="json")

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["state"], "presenting_diagnosis")
        self.assertTrue(r.data["requires_booking"])
        self.assertEqual(r.data["diagnosis"]["urgency_level"], "RED")
        mock_provider.diagnose.assert_called_once()


class TestErrorHandling(TestCase):

    def setUp(self):
        self.client = APIClient()

    @patch("apps.chat.application.services.dependencies.GeminiProvider")
    def test_off_topic_message_returns_rejection_not_500(self, MockGemini):
        MockGemini.return_value = MagicMock()
        session_id = str(uuid.uuid4())
        response = self.client.post(
            "/api/chat/",
            {"session_id": session_id, "message": "what is the best recipe for pasta"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("automotive", response.data["message"].lower())

    def test_invalid_session_uuid_returns_400(self):
        response = self.client.post(
            "/api/chat/",
            {"session_id": "not-a-uuid", "message": "hello"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_get_nonexistent_booking_returns_404(self):
        fake_id = str(uuid.uuid4())
        response = self.client.get(f"/api/booking/{fake_id}/")
        self.assertEqual(response.status_code, 404)


class TestDomainErrorsMapToJson(TestCase):
    """Domain exceptions must become structured 4xx JSON, never a 500."""

    def setUp(self):
        self.client = APIClient()
        self.session_id = str(uuid.uuid4())

    def test_invalid_media_type_returns_400(self):
        f = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
        r = self.client.post("/api/upload/", {"session_id": self.session_id, "file": f})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["code"], "invalid_media")

    def test_double_booking_returns_409(self):
        payload = {
            "session_id": self.session_id,
            "customer_name": "Test User",
            "phone_number": "9999999999",
            "preferred_slot": "2026-01-15T10:00:00Z",
        }
        first = self.client.post("/api/booking/", payload, format="json")
        self.assertEqual(first.status_code, 201)
        r = self.client.post("/api/booking/", payload, format="json")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["code"], "invalid_state")
