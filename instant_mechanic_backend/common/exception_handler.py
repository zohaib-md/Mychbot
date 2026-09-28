import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from common.exceptions import (
    DomainException,
    OffTopicQueryError,
    MediaValidationError,
    ConversationStateError,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler mapping domain exceptions to structured JSON responses.
    Falls through to DRF default handler for standard HTTP exceptions.
    """

    if isinstance(exc, OffTopicQueryError):
        logger.info("Off-topic query rejected: %s", exc)
        return Response(
            {"error": str(exc), "code": "off_topic"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, MediaValidationError):
        logger.warning("Media validation error: %s", exc)
        return Response(
            {"error": str(exc), "code": "invalid_media"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, ConversationStateError):
        logger.warning("Conversation state error: %s", exc)
        return Response(
            {"error": str(exc), "code": "invalid_state"},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, DomainException):
        logger.error("Unclassified domain exception: %s", exc)
        return Response(
            {"error": str(exc), "code": "domain_error"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Fall through to DRF default handler for HTTP exceptions (404, 405, etc.)
    return drf_exception_handler(exc, context)
