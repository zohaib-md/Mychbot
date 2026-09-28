import re
import copy
from apps.chat.domain.enums import ConversationState, Intent
from apps.chat.domain.entities import ConversationContext, StateTransitionResult

# Regex to extract vehicle make from user messages
VEHICLE_MAKE_PATTERN = re.compile(
    r"\b(toyota|honda|hyundai|kia|ford|bmw|mercedes|audi|vw|volkswagen|nissan|"
    r"mazda|subaru|suzuki|maruti|tata|mahindra|renault|skoda|jeep|chevrolet)\b",
    re.IGNORECASE,
)


class ConversationStateMachine:
    """
    Single Responsibility: Determine next conversation state and whether AI is needed.
    Open/Closed: add new states/intents to the tables without modifying this class.
    Zero Django imports. Zero LLM calls.
    """

    TRANSITION_TABLE: dict[tuple[ConversationState, Intent], ConversationState] = {
        # From IDLE
        (ConversationState.IDLE, Intent.GREETING): ConversationState.GREETING_HANDLED,
        (ConversationState.IDLE, Intent.REPORT_ISSUE): ConversationState.COLLECTING_SYMPTOMS,
        (ConversationState.IDLE, Intent.OFF_TOPIC): ConversationState.REJECTED,
        (ConversationState.IDLE, Intent.UPLOAD_MEDIA): ConversationState.AWAITING_MEDIA,
        (ConversationState.IDLE, Intent.BOOK_MECHANIC): ConversationState.BOOKING_INITIATED,
        (ConversationState.IDLE, Intent.FAREWELL): ConversationState.IDLE,
        (ConversationState.IDLE, Intent.UNCLEAR): ConversationState.IDLE,
        # From GREETING_HANDLED
        (ConversationState.GREETING_HANDLED, Intent.REPORT_ISSUE): ConversationState.COLLECTING_SYMPTOMS,
        (ConversationState.GREETING_HANDLED, Intent.UPLOAD_MEDIA): ConversationState.AWAITING_MEDIA,
        (ConversationState.GREETING_HANDLED, Intent.BOOK_MECHANIC): ConversationState.BOOKING_INITIATED,
        (ConversationState.GREETING_HANDLED, Intent.FAREWELL): ConversationState.IDLE,
        (ConversationState.GREETING_HANDLED, Intent.OFF_TOPIC): ConversationState.REJECTED,
        (ConversationState.GREETING_HANDLED, Intent.UNCLEAR): ConversationState.GREETING_HANDLED,
        # From COLLECTING_SYMPTOMS
        (ConversationState.COLLECTING_SYMPTOMS, Intent.REPORT_ISSUE): ConversationState.COLLECTING_SYMPTOMS,
        (ConversationState.COLLECTING_SYMPTOMS, Intent.UPLOAD_MEDIA): ConversationState.AWAITING_MEDIA,
        (ConversationState.COLLECTING_SYMPTOMS, Intent.BOOK_MECHANIC): ConversationState.BOOKING_INITIATED,
        (ConversationState.COLLECTING_SYMPTOMS, Intent.FAREWELL): ConversationState.IDLE,
        (ConversationState.COLLECTING_SYMPTOMS, Intent.OFF_TOPIC): ConversationState.REJECTED,
        (ConversationState.COLLECTING_SYMPTOMS, Intent.UNCLEAR): ConversationState.COLLECTING_SYMPTOMS,
        # From AWAITING_MEDIA
        (ConversationState.AWAITING_MEDIA, Intent.UPLOAD_MEDIA): ConversationState.AWAITING_MEDIA,
        (ConversationState.AWAITING_MEDIA, Intent.REPORT_ISSUE): ConversationState.COLLECTING_SYMPTOMS,
        (ConversationState.AWAITING_MEDIA, Intent.FAREWELL): ConversationState.IDLE,
        (ConversationState.AWAITING_MEDIA, Intent.UNCLEAR): ConversationState.AWAITING_MEDIA,
        # From PRESENTING_DIAGNOSIS
        (ConversationState.PRESENTING_DIAGNOSIS, Intent.BOOK_MECHANIC): ConversationState.BOOKING_INITIATED,
        (ConversationState.PRESENTING_DIAGNOSIS, Intent.FAREWELL): ConversationState.IDLE,
        (ConversationState.PRESENTING_DIAGNOSIS, Intent.UNCLEAR): ConversationState.PRESENTING_DIAGNOSIS,
        (ConversationState.PRESENTING_DIAGNOSIS, Intent.REPORT_ISSUE): ConversationState.COLLECTING_SYMPTOMS,
        # From BOOKING_INITIATED
        (ConversationState.BOOKING_INITIATED, Intent.REPORT_ISSUE): ConversationState.COLLECTING_BOOKING_DETAILS,
        (ConversationState.BOOKING_INITIATED, Intent.UNCLEAR): ConversationState.COLLECTING_BOOKING_DETAILS,
        (ConversationState.BOOKING_INITIATED, Intent.FAREWELL): ConversationState.IDLE,
        # From COLLECTING_BOOKING_DETAILS
        (ConversationState.COLLECTING_BOOKING_DETAILS, Intent.REPORT_ISSUE): ConversationState.COLLECTING_BOOKING_DETAILS,
        (ConversationState.COLLECTING_BOOKING_DETAILS, Intent.UNCLEAR): ConversationState.COLLECTING_BOOKING_DETAILS,
        # From REJECTED
        (ConversationState.REJECTED, Intent.GREETING): ConversationState.GREETING_HANDLED,
        (ConversationState.REJECTED, Intent.REPORT_ISSUE): ConversationState.COLLECTING_SYMPTOMS,
        (ConversationState.REJECTED, Intent.UNCLEAR): ConversationState.IDLE,
        (ConversationState.REJECTED, Intent.OFF_TOPIC): ConversationState.REJECTED,
    }

    RESPONSE_TEMPLATES: dict[ConversationState, str] = {
        ConversationState.GREETING_HANDLED: (
            "Hello! I'm your Instant Mechanic assistant — a senior automotive technician AI. "
            "What issue are you experiencing with your vehicle today?"
        ),
        ConversationState.COLLECTING_SYMPTOMS: (
            "Understood. Could you tell me your vehicle's make and model, "
            "and describe exactly when this issue occurs? (e.g., 'only when braking', 'on cold starts')"
        ),
        ConversationState.AWAITING_MEDIA: (
            "Please upload an image, audio recording, or short video of the issue. "
            "This will help me give you a more accurate diagnosis."
        ),
        ConversationState.REJECTED: (
            "I'm specialised in automotive issues only. "
            "Please describe a problem with your vehicle and I'll be happy to help."
        ),
        ConversationState.BOOKING_INITIATED: (
            "Let's get a mechanic to you. Please provide your full name and preferred date/time for the visit."
        ),
        ConversationState.BOOKING_CONFIRMED: (
            "Booking confirmed! A verified Instant Mechanic will contact you shortly."
        ),
        ConversationState.IDLE: (
            "Hello! I'm your Instant Mechanic assistant. How can I help with your vehicle today?"
        ),
        ConversationState.DIAGNOSING_ISSUE: (
            "Analysing your vehicle symptoms now. Please wait a moment..."
        ),
        ConversationState.COLLECTING_BOOKING_DETAILS: (
            "Got it. Please provide your phone number and preferred appointment slot."
        ),
        ConversationState.PRESENTING_DIAGNOSIS: "",  # Filled dynamically by ChatService
    }

    def transition(
        self,
        current_state: ConversationState,
        intent: Intent,
        context: ConversationContext,
        message: str = "",
    ) -> StateTransitionResult:
        # 1. Look up transition table
        next_state = self.TRANSITION_TABLE.get((current_state, intent))

        # 2. Fallback if no explicit transition defined
        if next_state is None:
            next_state = self._fallback_transition(current_state)

        # 3. Update context with any extracted info from message
        updated_context = self._update_context(context, message, intent)
        updated_context.state = next_state

        # 4. Elevate COLLECTING_SYMPTOMS → DIAGNOSING_ISSUE when guard passes
        if (
            next_state == ConversationState.COLLECTING_SYMPTOMS
            and self._symptoms_sufficient(updated_context)
        ):
            next_state = ConversationState.DIAGNOSING_ISSUE
            updated_context.state = next_state

        # 5. AI call authorized ONLY for DIAGNOSING_ISSUE
        requires_ai_call = next_state == ConversationState.DIAGNOSING_ISSUE

        return StateTransitionResult(
            next_state=next_state,
            requires_ai_call=requires_ai_call,
            response_template=self.RESPONSE_TEMPLATES.get(next_state, ""),
            updated_context=updated_context,
        )

    def _symptoms_sufficient(self, context: ConversationContext) -> bool:
        """
        Guard: Only authorize AI call when we have enough context.
        Prevents premature (expensive) AI invocations.
        Requires: at least one symptom description AND one follow-up round.
        """
        return (
            context.symptom_description is not None
            and context.follow_up_rounds >= 1
        )

    def _update_context(
        self,
        context: ConversationContext,
        message: str,
        intent: Intent,
    ) -> ConversationContext:
        """Extract vehicle info and accumulate symptoms. Returns a deep copy."""
        updated = copy.deepcopy(context)

        # Extract vehicle make via regex
        if not updated.vehicle_make and message:
            match = VEHICLE_MAKE_PATTERN.search(message)
            if match:
                updated.vehicle_make = match.group(0).title()

        # Accumulate symptom description
        if intent == Intent.REPORT_ISSUE and message:
            if updated.symptom_description:
                updated.symptom_description += f" | {message}"
                updated.follow_up_rounds += 1
            else:
                updated.symptom_description = message

        return updated

    def _fallback_transition(self, current_state: ConversationState) -> ConversationState:
        """Conservative fallback: stay in current state, or return to IDLE."""
        safe_fallbacks = {
            ConversationState.COLLECTING_SYMPTOMS: ConversationState.COLLECTING_SYMPTOMS,
            ConversationState.PRESENTING_DIAGNOSIS: ConversationState.PRESENTING_DIAGNOSIS,
            ConversationState.BOOKING_INITIATED: ConversationState.BOOKING_INITIATED,
        }
        return safe_fallbacks.get(current_state, ConversationState.IDLE)
