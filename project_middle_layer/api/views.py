from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from project_middle_layer.models import ProjectNode
from project_middle_layer.pipelines import build_project_creation_payload

from .serializers import ProjectNodeSerializer, ProjectNodeWriteSerializer


class ProjectNodeViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectNode.objects.all().order_by("-updated_at")


class ProjectMiddleLayerCompileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProjectNodeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        compiled = build_project_creation_payload(
            slug=payload["slug"],
            name=payload["name"],
            semantic_intent=payload["semantic_intent"],
            mlas_tier=payload["mlas_tier"],
            btif_classification=payload["btif_classification"],
            semantic_tags=payload["semantic_tags"],
        )

        ProjectNode.objects.update_or_create(
            slug=payload["slug"],
            defaults={
                "name": payload["name"],
                "semantic_intent": payload["semantic_intent"],
                "mlas_tier": payload["mlas_tier"],
                "btif_classification": payload["btif_classification"],
                "metadata": payload.get("metadata", {}),
            },
        )

        return Response(compiled, status=status.HTTP_200_OK)
