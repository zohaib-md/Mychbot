# Re-export the domain exceptions so there is a single class hierarchy.
# Services raise these from apps.chat.domain.exceptions; the DRF exception
# handler imports them from here — both must refer to the same classes.
from apps.chat.domain.exceptions import (  # noqa: F401
    DomainException,
    OffTopicQueryError,
    MediaValidationError,
    ConversationStateError,
)
