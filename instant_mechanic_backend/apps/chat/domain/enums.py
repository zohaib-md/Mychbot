from enum import Enum


class ConversationState(str, Enum):
    IDLE = "idle"
    GREETING_HANDLED = "greeting_handled"
    COLLECTING_SYMPTOMS = "collecting_symptoms"
    AWAITING_MEDIA = "awaiting_media"
    DIAGNOSING_ISSUE = "diagnosing_issue"
    PRESENTING_DIAGNOSIS = "presenting_diagnosis"
    BOOKING_INITIATED = "booking_initiated"
    COLLECTING_BOOKING_DETAILS = "collecting_booking_details"
    BOOKING_CONFIRMED = "booking_confirmed"
    REJECTED = "rejected"


class Intent(str, Enum):
    GREETING = "greeting"
    REPORT_ISSUE = "report_issue"
    UPLOAD_MEDIA = "upload_media"
    BOOK_MECHANIC = "book_mechanic"
    FAREWELL = "farewell"
    OFF_TOPIC = "off_topic"
    UNCLEAR = "unclear"
