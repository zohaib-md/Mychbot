from django.urls import path
from .views import DiagnosisView

urlpatterns = [
    path("diagnosis/", DiagnosisView.as_view(), name="diagnosis"),
]
