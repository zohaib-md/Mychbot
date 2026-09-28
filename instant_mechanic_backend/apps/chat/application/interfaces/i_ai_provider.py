from abc import ABC, abstractmethod
from apps.chat.domain.entities import ConversationContext, DiagnosisResult


class IAIProvider(ABC):

    @abstractmethod
    def diagnose(self, context: ConversationContext) -> DiagnosisResult:
        ...

    @abstractmethod
    def upload_media(self, file_path: str, mime_type: str) -> str:
        """Upload file to Gemini File API, return URI."""
        ...
