import uuid
from django.db import models
from apps.chat.models import Conversation


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]
    booking_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="bookings"
    )
    customer_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    preferred_slot = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking({self.booking_id}, status={self.status})"
