from apps.chat.domain.entities import ConversationContext
from apps.chat.domain.enums import ConversationState
from common.utils.regex_patterns import AUTOMOTIVE_KEYWORDS, COMPILED_HARD_REJECTS

# States where the user is already mid-flow (answering our follow-up questions or
# giving booking details). Their replies often carry no car keyword
# ("it started last week and gets worse at speed"), so we trust the context.
IN_CONVERSATION_STATES = {
    ConversationState.COLLECTING_SYMPTOMS,
    ConversationState.AWAITING_MEDIA,
    ConversationState.PRESENTING_DIAGNOSIS,
    ConversationState.BOOKING_INITIATED,
    ConversationState.COLLECTING_BOOKING_DETAILS,
}


class DomainFilter:
    """
    Single Responsibility: Determine if a message is automotive-related.
    Zero LLM calls. Zero Django imports.
    """

    def is_automotive(
        self, message: str, context: ConversationContext | None = None
    ) -> bool:
        """
        Returns False if the message matches hard-reject off-topic patterns.
        Returns True if at least one automotive keyword is present.
        Returns True for any follow-up inside an active automotive conversation.
        Defaults to True (benefit of the doubt) for short/ambiguous messages.
        """
        normalized = message.lower().strip()

        # Fast path: hard reject on known off-topic domains
        for pattern in COMPILED_HARD_REJECTS:
            if pattern.search(normalized):
                return False

        # Keyword signal scoring
        score = sum(1 for kw in AUTOMOTIVE_KEYWORDS if kw in normalized)
        if score >= 1:
            return True

        # Follow-up answers within an ongoing automotive conversation
        if context is not None and context.state in IN_CONVERSATION_STATES:
            return True

        # Benefit of the doubt for short/ambiguous messages
        # (e.g., "it won't start" has no keyword but is likely automotive)
        return len(normalized.split()) <= 8
