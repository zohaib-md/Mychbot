import os
import logging
from apps.chat.domain.exceptions import MediaValidationError

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".mp3", ".wav", ".mp4"}
ALLOWED_MIME_TYPES: set[str] = {
    "image/jpeg", "image/png",
    "audio/mpeg", "audio/wav",
    "video/mp4",
}
MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB

EXTENSION_TO_MEDIA_TYPE: dict[str, str] = {
    ".jpg": "image", ".jpeg": "image", ".png": "image",
    ".mp3": "audio", ".wav": "audio",
    ".mp4": "video",
}


class MediaHandler:
    """Validates and stores uploaded media files. Never calls Gemini."""

    def validate_and_store(self, uploaded_file, conversation):
        from apps.chat.models import Media

        self._validate(uploaded_file)

        ext = os.path.splitext(uploaded_file.name)[1].lower()
        media_type = EXTENSION_TO_MEDIA_TYPE.get(ext, "image")

        media = Media(
            conversation=conversation,
            media_type=media_type,
            gemini_file_uri="",  # Populated only during diagnosis
        )
        media.file = uploaded_file
        media.save()
        logger.info("Media stored: id=%s type=%s", media.id, media_type)
        return media

    def _validate(self, uploaded_file) -> None:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise MediaValidationError(
                f"File type '{ext}' is not supported. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        content_type = getattr(uploaded_file, "content_type", "")
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            raise MediaValidationError(
                f"MIME type '{content_type}' is not supported."
            )

        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            raise MediaValidationError(
                f"File size {uploaded_file.size / (1024 * 1024):.1f} MB exceeds 20 MB limit."
            )
