from django.db import models
from apps.chat.models import Conversation


class Diagnosis(models.Model):
    URGENCY_CHOICES = [
        ("GREEN", "Green — Safe to drive"),
        ("YELLOW", "Yellow — Caution"),
        ("RED", "Red — Stop driving immediately"),
    ]
    conversation = models.OneToOneField(
        Conversation, on_delete=models.CASCADE, related_name="diagnosis"
    )
    probable_causes = models.JSONField(default=list)
    urgency_level = models.CharField(max_length=10, choices=URGENCY_CHOICES)
    estimated_cost_range = models.CharField(max_length=60)
    recommended_service = models.CharField(max_length=200)
    mechanic_notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis({self.urgency_level}, conv={self.conversation.session_id})"
