import logging
from dataclasses import asdict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from apps.chat.presentation.serializers import (
    ChatMessageSerializer,
    ChatResponseSerializer,
    MediaUploadSerializer,
    MediaUploadResponseSerializer,
)
from apps.chat.application.services.dependencies import get_chat_service
from apps.chat.application.services.media_service import MediaService
from apps.chat.infrastructure.media.media_handler import MediaHandler
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository

logger = logging.getLogger(__name__)


class ChatView(APIView):
    """
    POST /api/chat/
    Routes message through State Machine gatekeeper.
    Gemini invoked ONLY when conversation reaches DIAGNOSING_ISSUE state.
    """

    @extend_schema(
        request=ChatMessageSerializer,
        responses={200: ChatResponseSerializer},
        description=(
            "Send a chat message. Routes through State Machine — "
            "Gemini is only invoked when conversation state reaches DIAGNOSING_ISSUE. "
            "Greetings, rejections, and booking flow are handled by deterministic rules."
        ),
    )
    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_chat_service()
        response = service.process_message(
            session_id=str(serializer.validated_data["session_id"]),
            message=serializer.validated_data["message"],
        )

        diagnosis_data = asdict(response.diagnosis) if response.diagnosis else None

        return Response({
            "message": response.message,
            "state": response.state,
            "requires_booking": response.requires_booking,
            "diagnosis": diagnosis_data,
        })


class UploadView(APIView):
    """
    POST /api/upload/
    Validates and stores media file. Does NOT call Gemini.
    Gemini File API upload is deferred until diagnosis.
    """

    @extend_schema(
        request=MediaUploadSerializer,
        responses={201: MediaUploadResponseSerializer},
        description=(
            "Upload an image (.jpg, .png), audio (.mp3, .wav), or video (.mp4) file. "
            "File is validated and stored locally. "
            "Gemini File API upload is deferred until diagnosis is triggered."
        ),
    )
    def post(self, request):
        serializer = MediaUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = MediaService(
            media_handler=MediaHandler(),
            conversation_repo=DjangoConversationRepository(),
        )
        result = service.handle_upload(
            session_id=str(serializer.validated_data["session_id"]),
            uploaded_file=request.FILES["file"],
        )

        return Response(
            {"media_id": result.media_id, "status": result.status},
            status=status.HTTP_201_CREATED,
        )
