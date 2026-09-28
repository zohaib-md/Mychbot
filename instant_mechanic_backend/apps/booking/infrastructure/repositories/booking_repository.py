import uuid
from django.shortcuts import get_object_or_404
from apps.chat.domain.entities import BookingPayload


class DjangoBookingRepository:
    """Persists and retrieves Booking records via Django ORM."""

    def create(self, session_id: str, payload: BookingPayload):
        from apps.chat.models import Conversation
        from apps.booking.models import Booking
        conv = Conversation.objects.get(session_id=uuid.UUID(str(session_id)))
        return Booking.objects.create(
            conversation=conv,
            customer_name=payload.customer_name,
            phone_number=payload.phone_number,
            preferred_slot=payload.preferred_slot,
            status="confirmed",
        )

    def get_by_id(self, booking_id: str):
        from apps.booking.models import Booking
        return get_object_or_404(Booking, booking_id=uuid.UUID(str(booking_id)))
