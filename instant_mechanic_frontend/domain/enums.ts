export enum ConversationState {
  IDLE = "idle",
  GREETING_HANDLED = "greeting_handled",
  COLLECTING_SYMPTOMS = "collecting_symptoms",
  AWAITING_MEDIA = "awaiting_media",
  DIAGNOSING_ISSUE = "diagnosing_issue",
  PRESENTING_DIAGNOSIS = "presenting_diagnosis",
  BOOKING_INITIATED = "booking_initiated",
  COLLECTING_BOOKING_DETAILS = "collecting_booking_details",
  BOOKING_CONFIRMED = "booking_confirmed",
  REJECTED = "rejected",
}

export enum UrgencyLevel {
  GREEN = "GREEN",
  YELLOW = "YELLOW",
  RED = "RED",
}
