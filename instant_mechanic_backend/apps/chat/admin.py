from django.contrib import admin
from .models import Conversation, Message, Media


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["session_id", "state", "vehicle_make", "vehicle_model", "created_at"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "role", "content", "created_at"]


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ["conversation", "media_type", "gemini_file_uri", "uploaded_at"]
