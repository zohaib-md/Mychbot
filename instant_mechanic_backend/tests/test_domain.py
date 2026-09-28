import pytest
from apps.chat.domain.enums import ConversationState, Intent
from apps.chat.domain.entities import ConversationContext, DiagnosisResult
from apps.chat.application.interfaces.i_ai_provider import IAIProvider


def test_conversation_state_values_are_strings():
    for state in ConversationState:
        assert isinstance(state.value, str)


def test_intent_values_are_strings():
    for intent in Intent:
        assert isinstance(intent.value, str)


def test_conversation_context_defaults():
    ctx = ConversationContext(session_id="abc", state=ConversationState.IDLE)
    assert ctx.vehicle_make is None
    assert ctx.vehicle_model is None
    assert ctx.symptom_description is None
    assert ctx.follow_up_rounds == 0
    assert ctx.pending_media_uris == []
    assert ctx.pending_media_paths == []


def test_diagnosis_result_fields():
    d = DiagnosisResult(
        probable_causes=["Battery failure"],
        urgency_level="RED",
        estimated_cost_range="₹1,800 - ₹3,500",
        recommended_service="Battery Replacement",
        mechanic_notes="Engine clicks.",
    )
    assert d.urgency_level == "RED"
    assert len(d.probable_causes) == 1
    assert d.probable_causes[0] == "Battery failure"


def test_ai_provider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        IAIProvider()


def test_conversation_state_idle_value():
    assert ConversationState.IDLE.value == "idle"


def test_conversation_state_diagnosing_value():
    assert ConversationState.DIAGNOSING_ISSUE.value == "diagnosing_issue"
