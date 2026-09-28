from abc import ABC, abstractmethod
from apps.chat.domain.entities import ConversationContext


class IConversationRepository(ABC):

    @abstractmethod
    def get_or_create(self, session_id: str) -> ConversationContext:
        ...

    @abstractmethod
    def update(self, context: ConversationContext) -> None:
        ...

    @abstractmethod
    def append_message(self, session_id: str, role: str, content: str) -> None:
        ...
