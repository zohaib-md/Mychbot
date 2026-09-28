from rest_framework import serializers


class DiagnosisRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()


class DiagnosisResultSerializer(serializers.Serializer):
    probable_causes = serializers.ListField(child=serializers.CharField())
    urgency_level = serializers.CharField()
    estimated_cost_range = serializers.CharField()
    recommended_service = serializers.CharField()
    mechanic_notes = serializers.CharField()
