from rest_framework import serializers


class CreateBookingSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    customer_name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)
    preferred_slot = serializers.DateTimeField()


class BookingConfirmationSerializer(serializers.Serializer):
    booking_id = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField()


class BookingDetailSerializer(serializers.Serializer):
    booking_id = serializers.CharField()
    customer_name = serializers.CharField()
    phone_number = serializers.CharField()
    preferred_slot = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.CharField()
