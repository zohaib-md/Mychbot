import uuid
from apps.chat.application.interfaces.i_conversation_repository import IConversationRepository
from apps.chat.domain.entities import ConversationContext
from apps.chat.domain.enums import ConversationState


class DjangoConversationRepository(IConversationRepository):
    """
    Concrete Django ORM implementation of IConversationRepository.
    Maps ORM models to/from domain dataclasses — no ORM objects leak into the domain layer.
    """

    def get_or_create(self, session_id: str) -> ConversationContext:
        from apps.chat.models import Conversation
        sid = uuid.UUID(str(session_id))
        conv, _ = Conversation.objects.get_or_create(
            session_id=sid,
            defaults={"state": ConversationState.IDLE.value},
        )
        return self._to_context(conv)

    def update(self, context: ConversationContext) -> None:
        from apps.chat.models import Conversation
        sid = uuid.UUID(str(context.session_id))
        state_value = (
            context.state.value
            if isinstance(context.state, ConversationState)
            else context.state
        )
        Conversation.objects.filter(session_id=sid).update(
            state=state_value,
            vehicle_make=context.vehicle_make or "",
            vehicle_model=context.vehicle_model or "",
            follow_up_rounds=context.follow_up_rounds,
            symptom_description=context.symptom_description or "",
        )

    def append_message(self, session_id: str, role: str, content: str) -> None:
        from apps.chat.models import Conversation, Message
        sid = uuid.UUID(str(session_id))
        conv = Conversation.objects.get(session_id=sid)
        Message.objects.create(conversation=conv, role=role, content=content)

    def _to_context(self, conv) -> ConversationContext:
        return ConversationContext(
            session_id=str(conv.session_id),
            state=ConversationState(conv.state),
            vehicle_make=conv.vehicle_make or None,
            vehicle_model=conv.vehicle_model or None,
            symptom_description=conv.symptom_description or None,
            follow_up_rounds=conv.follow_up_rounds,
        )
