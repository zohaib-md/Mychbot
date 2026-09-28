import logging
from apps.chat.domain.entities import BookingPayload, BookingConfirmation, BookingDetail
from apps.booking.infrastructure.repositories.booking_repository import DjangoBookingRepository
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository
from apps.chat.domain.enums import ConversationState
from apps.chat.domain.exceptions import ConversationStateError

logger = logging.getLogger(__name__)


class BookingService:
    """
    Orchestrates booking creation and retrieval.
    Validates conversation is in an allowed state before creating a booking.
    """

    ALLOWED_BOOKING_STATES = {
        ConversationState.PRESENTING_DIAGNOSIS,
        ConversationState.BOOKING_INITIATED,
        ConversationState.COLLECTING_BOOKING_DETAILS,
        ConversationState.COLLECTING_SYMPTOMS,
        ConversationState.IDLE,
    }

    def __init__(
        self,
        booking_repo: DjangoBookingRepository,
        conversation_repo: DjangoConversationRepository,
    ):
        self.booking_repo = booking_repo
        self.conversation_repo = conversation_repo

    def create_booking(self, session_id: str, payload: BookingPayload) -> BookingConfirmation:
        context = self.conversation_repo.get_or_create(session_id)

        if context.state not in self.ALLOWED_BOOKING_STATES:
            raise ConversationStateError(
                f"Cannot book from state '{context.state}'. "
                "Please complete the diagnosis first."
            )

        booking = self.booking_repo.create(session_id, payload)

        context.state = ConversationState.BOOKING_CONFIRMED
        self.conversation_repo.update(context)

        logger.info("Booking created: %s for session %s", booking.booking_id, session_id)
        return BookingConfirmation(
            booking_id=str(booking.booking_id),
            status="confirmed",
            message=(
                f"Booking confirmed! Your reference ID is {booking.booking_id}. "
                "A verified Instant Mechanic will contact you shortly."
            ),
        )

    def get_booking(self, booking_id: str) -> BookingDetail:
        booking = self.booking_repo.get_by_id(booking_id)
        return BookingDetail(
            booking_id=str(booking.booking_id),
            customer_name=booking.customer_name,
            phone_number=booking.phone_number,
            preferred_slot=booking.preferred_slot.isoformat(),
            status=booking.status,
            created_at=booking.created_at.isoformat(),
        )
