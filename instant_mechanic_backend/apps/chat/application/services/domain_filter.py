from common.utils.regex_patterns import AUTOMOTIVE_KEYWORDS, COMPILED_HARD_REJECTS


class DomainFilter:
    """
    Single Responsibility: Determine if a message is automotive-related.
    Zero LLM calls. Zero Django imports.
    """

    def is_automotive(self, message: str) -> bool:
        """
        Returns False if the message matches hard-reject off-topic patterns.
        Returns True if at least one automotive keyword is present.
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

        # Benefit of the doubt for short/ambiguous messages
        # (e.g., "it won't start" has no keyword but is likely automotive)
        return len(normalized.split()) <= 8
