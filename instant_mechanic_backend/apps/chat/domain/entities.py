from dataclasses import dataclass, field
from .enums import ConversationState


@dataclass
class ConversationContext:
    session_id: str
    state: ConversationState
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    symptom_description: str | None = None
    follow_up_rounds: int = 0
    pending_media_paths: list[str] = field(default_factory=list)
    pending_media_uris: list[str] = field(default_factory=list)


@dataclass
class StateTransitionResult:
    next_state: ConversationState
    requires_ai_call: bool
    response_template: str
    updated_context: ConversationContext


@dataclass
class DiagnosisResult:
    probable_causes: list[str]
    urgency_level: str  # GREEN | YELLOW | RED
    estimated_cost_range: str
    recommended_service: str
    mechanic_notes: str


@dataclass
class ChatResponse:
    message: str
    state: str
    requires_booking: bool
    diagnosis: DiagnosisResult | None = None


@dataclass
class MediaUploadResponse:
    media_id: int
    status: str


@dataclass
class BookingPayload:
    session_id: str
    customer_name: str
    phone_number: str
    preferred_slot: str


@dataclass
class BookingConfirmation:
    booking_id: str
    status: str
    message: str


@dataclass
class BookingDetail:
    booking_id: str
    customer_name: str
    phone_number: str
    preferred_slot: str
    status: str
    created_at: str
