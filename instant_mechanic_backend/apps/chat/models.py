import uuid
from django.db import models


class Conversation(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    state = models.CharField(max_length=40, default="idle")
    vehicle_make = models.CharField(max_length=60, blank=True, default="")
    vehicle_model = models.CharField(max_length=60, blank=True, default="")
    follow_up_rounds = models.IntegerField(default=0)
    symptom_description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Conversation({self.session_id}, state={self.state})"


class Message(models.Model):
    ROLE_CHOICES = [("user", "User"), ("bot", "Bot")]
    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message({self.role}, conv={self.conversation.session_id})"


class Media(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("image", "Image"),
        ("audio", "Audio"),
        ("video", "Video"),
    ]
    conversation = models.ForeignKey(
        Conversation, related_name="media", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    gemini_file_uri = models.CharField(max_length=500, blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media({self.media_type}, conv={self.conversation.session_id})"
