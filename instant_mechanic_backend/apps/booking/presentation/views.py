import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from apps.booking.presentation.serializers import (
    CreateBookingSerializer,
    BookingConfirmationSerializer,
    BookingDetailSerializer,
)
from apps.booking.application.services.booking_service import BookingService
from apps.booking.infrastructure.repositories.booking_repository import DjangoBookingRepository
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository
from apps.chat.domain.entities import BookingPayload

logger = logging.getLogger(__name__)


def get_booking_service() -> BookingService:
    return BookingService(
        booking_repo=DjangoBookingRepository(),
        conversation_repo=DjangoConversationRepository(),
    )


class BookingView(APIView):
    """POST /api/booking/ — Create a new mechanic booking."""

    @extend_schema(
        tags=["booking"],
        request=CreateBookingSerializer,
        responses={201: BookingConfirmationSerializer},
        description="Create a mechanic booking. Returns a UUID booking reference and confirmed status.",
    )
    def post(self, request):
        serializer = CreateBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_booking_service()
        payload = BookingPayload(
            session_id=str(serializer.validated_data["session_id"]),
            customer_name=serializer.validated_data["customer_name"],
            phone_number=serializer.validated_data["phone_number"],
            preferred_slot=serializer.validated_data["preferred_slot"].isoformat(),
        )
        result = service.create_booking(
            session_id=str(serializer.validated_data["session_id"]),
            payload=payload,
        )
        return Response(
            {"booking_id": result.booking_id, "status": result.status, "message": result.message},
            status=status.HTTP_201_CREATED,
        )


class BookingDetailView(APIView):
    """GET /api/booking/{id}/ — Retrieve booking by UUID."""

    @extend_schema(
        tags=["booking"],
        responses={200: BookingDetailSerializer},
        description="Retrieve booking details by UUID. Returns 404 if not found.",
    )
    def get(self, request, booking_id):
        service = get_booking_service()
        result = service.get_booking(str(booking_id))
        return Response({
            "booking_id": result.booking_id,
            "customer_name": result.customer_name,
            "phone_number": result.phone_number,
            "preferred_slot": result.preferred_slot,
            "status": result.status,
            "created_at": result.created_at,
        })
