import pytest
from apps.chat.application.services.domain_filter import DomainFilter
from apps.chat.application.services.intent_classifier import IntentClassifier
from apps.chat.domain.entities import ConversationContext
from apps.chat.domain.enums import ConversationState, Intent


@pytest.fixture
def domain_filter():
    return DomainFilter()


@pytest.fixture
def classifier():
    return IntentClassifier()


@pytest.fixture
def idle_context():
    return ConversationContext(session_id="test", state=ConversationState.IDLE)


class TestDomainFilter:
    def test_automotive_overheating(self, domain_filter):
        assert domain_filter.is_automotive("my engine is overheating") is True

    def test_rejects_weather(self, domain_filter):
        assert domain_filter.is_automotive("what's the weather like today") is False

    def test_rejects_recipe(self, domain_filter):
        assert domain_filter.is_automotive("tell me a recipe for pasta") is False

    def test_toyota_noise(self, domain_filter):
        assert domain_filter.is_automotive("my Toyota is making a strange noise") is True

    def test_rejects_stocks(self, domain_filter):
        assert domain_filter.is_automotive("what are the best stocks to buy") is False

    def test_generic_car_term(self, domain_filter):
        assert domain_filter.is_automotive("my car won't start") is True

    def test_brake_issue(self, domain_filter):
        assert domain_filter.is_automotive("brakes are grinding when I stop") is True

    def test_long_follow_up_accepted_mid_conversation(self, domain_filter):
        # No car keyword and > 8 words, but we're answering a follow-up question
        ctx = ConversationContext(session_id="test", state=ConversationState.COLLECTING_SYMPTOMS)
        msg = "it started last week and gets worse at high speed"
        assert domain_filter.is_automotive(msg, ctx) is True

    def test_long_keywordless_message_rejected_at_start(self, domain_filter, idle_context):
        msg = "it started last week and gets worse at high speed"
        assert domain_filter.is_automotive(msg, idle_context) is False

    def test_hard_reject_applies_mid_conversation(self, domain_filter):
        ctx = ConversationContext(session_id="test", state=ConversationState.COLLECTING_SYMPTOMS)
        assert domain_filter.is_automotive("what are the best stocks to buy", ctx) is False

    def test_rejects_cricket(self, domain_filter):
        assert domain_filter.is_automotive("who won the cricket match today") is False


class TestIntentClassifier:
    def test_greeting_hi(self, classifier, idle_context):
        assert classifier.classify("hi there", idle_context) == Intent.GREETING

    def test_greeting_hello(self, classifier, idle_context):
        assert classifier.classify("hello!", idle_context) == Intent.GREETING

    def test_book_mechanic(self, classifier, idle_context):
        assert classifier.classify("I want to book a mechanic", idle_context) == Intent.BOOK_MECHANIC

    def test_schedule_appointment(self, classifier, idle_context):
        assert classifier.classify("can I schedule an appointment?", idle_context) == Intent.BOOK_MECHANIC

    def test_upload_media(self, classifier, idle_context):
        assert classifier.classify("let me attach a photo", idle_context) == Intent.UPLOAD_MEDIA

    def test_send_video(self, classifier, idle_context):
        assert classifier.classify("I'll send a video", idle_context) == Intent.UPLOAD_MEDIA

    def test_report_issue(self, classifier, idle_context):
        assert classifier.classify("my brakes are making a grinding noise", idle_context) == Intent.REPORT_ISSUE

    def test_farewell(self, classifier, idle_context):
        assert classifier.classify("thanks, bye!", idle_context) == Intent.FAREWELL

    def test_context_aware_collecting_symptoms(self, classifier):
        ctx = ConversationContext(session_id="test", state=ConversationState.COLLECTING_SYMPTOMS)
        # Plain description without explicit issue keywords treated as REPORT_ISSUE in symptom state
        assert classifier.classify("it happens when I brake at high speed", ctx) == Intent.REPORT_ISSUE

    def test_context_aware_greeting_handled(self, classifier):
        ctx = ConversationContext(session_id="test", state=ConversationState.GREETING_HANDLED)
        assert classifier.classify("my Toyota makes a clicking sound", ctx) == Intent.REPORT_ISSUE
