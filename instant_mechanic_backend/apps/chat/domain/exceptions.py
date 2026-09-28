class DomainException(Exception):
    pass


class OffTopicQueryError(DomainException):
    pass


class ConversationStateError(DomainException):
    pass


class MediaValidationError(DomainException):
    pass
