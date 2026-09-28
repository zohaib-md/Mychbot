from apps.chat.domain.enums import Intent, ConversationState
from apps.chat.domain.entities import ConversationContext
from common.utils.regex_patterns import (
    COMPILED_GREETINGS,
    COMPILED_FAREWELLS,
    COMPILED_BOOKINGS,
    COMPILED_UPLOADS,
    COMPILED_ISSUES,
    COMPILED_HARD_REJECTS,
)


class IntentClassifier:
    """
    Single Responsibility: Classify user message intent using rule-based patterns.
    Context-aware: adapts classification based on current conversation state.
    Zero LLM calls.
    """

    def classify(self, message: str, context: ConversationContext) -> Intent:
        normalized = message.lower().strip()

        # 1. Greeting — highest priority
        if any(p.search(normalized) for p in COMPILED_GREETINGS):
            return Intent.GREETING

        # 2. Farewell
        if any(p.search(normalized) for p in COMPILED_FAREWELLS):
            return Intent.FAREWELL

        # 3. Off-topic hard reject
        if any(p.search(normalized) for p in COMPILED_HARD_REJECTS):
            return Intent.OFF_TOPIC

        # 4. Booking intent
        if any(p.search(normalized) for p in COMPILED_BOOKINGS):
            return Intent.BOOK_MECHANIC

        # 5. Upload intent
        if any(p.search(normalized) for p in COMPILED_UPLOADS):
            return Intent.UPLOAD_MEDIA

        # 6. Issue / symptom report
        if any(p.search(normalized) for p in COMPILED_ISSUES):
            return Intent.REPORT_ISSUE

        # 7. Context-aware fallback:
        # If we're already collecting symptoms, plain text = more symptom info
        if context.state in (
            ConversationState.COLLECTING_SYMPTOMS,
            ConversationState.GREETING_HANDLED,
        ):
            return Intent.REPORT_ISSUE

        return Intent.UNCLEAR
