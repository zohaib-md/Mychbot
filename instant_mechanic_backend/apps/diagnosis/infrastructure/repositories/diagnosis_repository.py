import uuid
from apps.chat.domain.entities import DiagnosisResult


class DjangoDiagnosisRepository:
    """Persists and retrieves Diagnosis records via Django ORM."""

    def save(self, session_id: str, result: DiagnosisResult):
        from apps.chat.models import Conversation
        from apps.diagnosis.models import Diagnosis
        conv = Conversation.objects.get(session_id=uuid.UUID(str(session_id)))
        diagnosis, _ = Diagnosis.objects.update_or_create(
            conversation=conv,
            defaults={
                "probable_causes": result.probable_causes,
                "urgency_level": result.urgency_level,
                "estimated_cost_range": result.estimated_cost_range,
                "recommended_service": result.recommended_service,
                "mechanic_notes": result.mechanic_notes,
            },
        )
        return diagnosis

    def get_by_session(self, session_id: str):
        from apps.diagnosis.models import Diagnosis
        from apps.chat.models import Conversation
        try:
            conv = Conversation.objects.get(session_id=uuid.UUID(str(session_id)))
            return Diagnosis.objects.get(conversation=conv)
        except (Diagnosis.DoesNotExist, Conversation.DoesNotExist):
            return None
