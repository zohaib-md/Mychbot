import pytest
from apps.chat.application.services.state_machine import ConversationStateMachine
from apps.chat.domain.enums import ConversationState, Intent
from apps.chat.domain.entities import ConversationContext


@pytest.fixture
def sm():
    return ConversationStateMachine()


@pytest.fixture
def idle_ctx():
    return ConversationContext(session_id="test-session", state=ConversationState.IDLE)


class TestTransitionTable:
    def test_idle_greeting_goes_to_greeting_handled(self, sm, idle_ctx):
        result = sm.transition(ConversationState.IDLE, Intent.GREETING, idle_ctx)
        assert result.next_state == ConversationState.GREETING_HANDLED

    def test_idle_off_topic_goes_to_rejected(self, sm, idle_ctx):
        result = sm.transition(ConversationState.IDLE, Intent.OFF_TOPIC, idle_ctx)
        assert result.next_state == ConversationState.REJECTED
        assert result.requires_ai_call is False

    def test_idle_report_issue_goes_to_collecting(self, sm, idle_ctx):
        result = sm.transition(ConversationState.IDLE, Intent.REPORT_ISSUE, idle_ctx)
        assert result.next_state == ConversationState.COLLECTING_SYMPTOMS

    def test_greeting_handled_report_issue_goes_to_collecting(self, sm):
        ctx = ConversationContext(session_id="s", state=ConversationState.GREETING_HANDLED)
        result = sm.transition(ConversationState.GREETING_HANDLED, Intent.REPORT_ISSUE, ctx)
        assert result.next_state == ConversationState.COLLECTING_SYMPTOMS

    def test_presenting_diagnosis_book_goes_to_booking_initiated(self, sm):
        ctx = ConversationContext(session_id="s", state=ConversationState.PRESENTING_DIAGNOSIS)
        result = sm.transition(ConversationState.PRESENTING_DIAGNOSIS, Intent.BOOK_MECHANIC, ctx)
        assert result.next_state == ConversationState.BOOKING_INITIATED

    def test_collecting_symptoms_upload_media_goes_to_awaiting(self, sm):
        ctx = ConversationContext(session_id="s", state=ConversationState.COLLECTING_SYMPTOMS)
        result = sm.transition(ConversationState.COLLECTING_SYMPTOMS, Intent.UPLOAD_MEDIA, ctx)
        assert result.next_state == ConversationState.AWAITING_MEDIA


class TestAICallGuard:
    def test_requires_ai_only_for_diagnosing(self, sm):
        ctx = ConversationContext(
            session_id="s",
            state=ConversationState.COLLECTING_SYMPTOMS,
            symptom_description="Engine knocking on startup",
            follow_up_rounds=1,
        )
        result = sm.transition(ConversationState.COLLECTING_SYMPTOMS, Intent.REPORT_ISSUE, ctx, "more detail")
        assert result.requires_ai_call is True
        assert result.next_state == ConversationState.DIAGNOSING_ISSUE

    def test_rejected_state_never_requires_ai(self, sm, idle_ctx):
        result = sm.transition(ConversationState.IDLE, Intent.OFF_TOPIC, idle_ctx)
        assert result.requires_ai_call is False

    def test_greeting_never_requires_ai(self, sm, idle_ctx):
        result = sm.transition(ConversationState.IDLE, Intent.GREETING, idle_ctx)
        assert result.requires_ai_call is False

    def test_booking_never_requires_ai(self, sm, idle_ctx):
        result = sm.transition(ConversationState.IDLE, Intent.BOOK_MECHANIC, idle_ctx)
        assert result.requires_ai_call is False


class TestSymptomsSufficient:
    def test_insufficient_when_no_symptoms(self, sm):
        ctx = ConversationContext(session_id="s", state=ConversationState.COLLECTING_SYMPTOMS)
        assert sm._symptoms_sufficient(ctx) is False

    def test_insufficient_when_zero_follow_ups(self, sm):
        ctx = ConversationContext(
            session_id="s",
            state=ConversationState.COLLECTING_SYMPTOMS,
            symptom_description="Knocking noise",
            follow_up_rounds=0,
        )
        assert sm._symptoms_sufficient(ctx) is False

    def test_sufficient_with_all_fields(self, sm):
        ctx = ConversationContext(
            session_id="s",
            state=ConversationState.COLLECTING_SYMPTOMS,
            vehicle_make="Toyota",
            symptom_description="Knocking noise on startup",
            follow_up_rounds=1,
        )
        assert sm._symptoms_sufficient(ctx) is True

    def test_sufficient_without_vehicle_make(self, sm):
        # vehicle_make is not required — symptoms + follow-up is enough
        ctx = ConversationContext(
            session_id="s",
            state=ConversationState.COLLECTING_SYMPTOMS,
            symptom_description="Engine making grinding noise",
            follow_up_rounds=1,
        )
        assert sm._symptoms_sufficient(ctx) is True


class TestVehicleExtraction:
    def test_extracts_toyota(self, sm, idle_ctx):
        result = sm.transition(
            ConversationState.IDLE, Intent.REPORT_ISSUE, idle_ctx,
            "my Toyota is making noise"
        )
        assert result.updated_context.vehicle_make == "Toyota"

    def test_extracts_bmw(self, sm, idle_ctx):
        result = sm.transition(
            ConversationState.IDLE, Intent.REPORT_ISSUE, idle_ctx,
            "BMW engine knocking problem"
        )
        assert result.updated_context.vehicle_make == "Bmw"
