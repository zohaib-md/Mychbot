from django.contrib import admin
from .models import Diagnosis


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ["conversation", "urgency_level", "recommended_service", "created_at"]
