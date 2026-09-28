import uuid
import logging
from apps.chat.infrastructure.media.media_handler import MediaHandler
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository
from apps.chat.domain.entities import MediaUploadResponse
from apps.chat.domain.enums import ConversationState

logger = logging.getLogger(__name__)


class MediaService:
    """
    Orchestrates media upload: validate → store → update conversation state.
    No Gemini calls here — file URI is populated only at diagnosis time.
    """

    def __init__(
        self,
        media_handler: MediaHandler,
        conversation_repo: DjangoConversationRepository,
    ):
        self.media_handler = media_handler
        self.conversation_repo = conversation_repo

    def handle_upload(self, session_id: str, uploaded_file) -> MediaUploadResponse:
        context = self.conversation_repo.get_or_create(session_id)

        from apps.chat.models import Conversation
        conv = Conversation.objects.get(session_id=uuid.UUID(str(session_id)))

        media = self.media_handler.validate_and_store(uploaded_file, conv)

        # Transition state to AWAITING_MEDIA if not already past that point
        if context.state in (
            ConversationState.IDLE,
            ConversationState.GREETING_HANDLED,
            ConversationState.COLLECTING_SYMPTOMS,
        ):
            context.state = ConversationState.AWAITING_MEDIA
            context.pending_media_paths.append(media.file.path)
            self.conversation_repo.update(context)

        logger.info("Media upload handled: media_id=%s session=%s", media.id, session_id)
        return MediaUploadResponse(media_id=media.id, status="staged")
