class DomainException(Exception):
    """Base class for all domain exceptions."""
    pass


class OffTopicQueryError(DomainException):
    """Raised when a message is not automotive-related."""
    pass


class MediaValidationError(DomainException):
    """Raised when an uploaded file fails validation."""
    pass


class ConversationStateError(DomainException):
    """Raised when an operation is invalid for the current conversation state."""
    pass
