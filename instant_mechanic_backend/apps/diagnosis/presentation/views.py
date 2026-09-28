from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from apps.diagnosis.presentation.serializers import DiagnosisRequestSerializer, DiagnosisResultSerializer
from apps.diagnosis.application.services.diagnosis_service import DiagnosisService
from apps.chat.infrastructure.repositories.conversation_repository import DjangoConversationRepository
from apps.diagnosis.infrastructure.repositories.diagnosis_repository import DjangoDiagnosisRepository
from apps.chat.application.services.dependencies import get_chat_service


class DiagnosisView(APIView):
    """POST /api/diagnosis/ — Manually trigger AI diagnosis for a session."""

    @extend_schema(
        tags=["diagnosis"],
        request=DiagnosisRequestSerializer,
        responses={200: DiagnosisResultSerializer},
        description=(
            "Manually trigger Gemini diagnosis for an existing session. "
            "Requires symptoms to have been collected via /api/chat/. "
            "Returns cached result if diagnosis already exists for this session."
        ),
    )
    def post(self, request):
        serializer = DiagnosisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        chat_service = get_chat_service()
        service = DiagnosisService(
            ai_provider=chat_service.ai_provider,
            conversation_repo=DjangoConversationRepository(),
            diagnosis_repo=DjangoDiagnosisRepository(),
        )
        result = service.run_diagnosis(str(serializer.validated_data["session_id"]))

        return Response({
            "probable_causes": result.probable_causes,
            "urgency_level": result.urgency_level,
            "estimated_cost_range": result.estimated_cost_range,
            "recommended_service": result.recommended_service,
            "mechanic_notes": result.mechanic_notes,
        })
