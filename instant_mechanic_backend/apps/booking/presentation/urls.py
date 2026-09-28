from django.urls import path
from .views import BookingView, BookingDetailView

urlpatterns = [
    path("booking/", BookingView.as_view(), name="booking-create"),
    path("booking/<uuid:booking_id>/", BookingDetailView.as_view(), name="booking-detail"),
]
