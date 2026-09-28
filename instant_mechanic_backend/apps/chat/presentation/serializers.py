from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    message = serializers.CharField(max_length=2000)


class ChatResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    state = serializers.CharField()
    requires_booking = serializers.BooleanField()
    diagnosis = serializers.DictField(required=False, allow_null=True)


class MediaUploadSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    file = serializers.FileField()


class MediaUploadResponseSerializer(serializers.Serializer):
    media_id = serializers.IntegerField()
    status = serializers.CharField()
