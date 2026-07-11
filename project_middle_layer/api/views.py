import uuid

from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from project_middle_layer.models import ProjectNode
from project_middle_layer.pipelines import build_project_creation_payload

from .serializers import (
    ProjectNodeSerializer,
    ProjectNodeWriteSerializer,
    ProjectWizardStartSerializer,
    ProjectWizardTagsSerializer,
)


WIZARD_TTL_SECONDS = 60 * 30


def _wizard_cache_key(user_id: int, wizard_id: str) -> str:
    return f"project_middle_layer:wizard:{user_id}:{wizard_id}"


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


class ProjectCreationWizardStartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProjectWizardStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        wizard_id = uuid.uuid4().hex
        cache.set(
            _wizard_cache_key(request.user.id, wizard_id),
            {
                "wizard_id": wizard_id,
                "step": "start",
                "base": payload,
                "tags": None,
            },
            timeout=WIZARD_TTL_SECONDS,
        )

        return Response(
            {
                "wizard_id": wizard_id,
                "next_step": "tags",
                "expires_in_seconds": WIZARD_TTL_SECONDS,
            },
            status=status.HTTP_201_CREATED,
        )


class ProjectCreationWizardTagsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, wizard_id: str):
        serializer = ProjectWizardTagsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key = _wizard_cache_key(request.user.id, wizard_id)
        draft = cache.get(key)
        if not draft:
            return Response({"detail": "Wizard session not found or expired."}, status=status.HTTP_404_NOT_FOUND)

        draft["tags"] = serializer.validated_data
        draft["step"] = "tags"
        cache.set(key, draft, timeout=WIZARD_TTL_SECONDS)

        return Response({"wizard_id": wizard_id, "next_step": "compile"}, status=status.HTTP_200_OK)


class ProjectCreationWizardCompileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, wizard_id: str):
        key = _wizard_cache_key(request.user.id, wizard_id)
        draft = cache.get(key)
        if not draft:
            return Response({"detail": "Wizard session not found or expired."}, status=status.HTTP_404_NOT_FOUND)

        if not draft.get("tags"):
            return Response({"detail": "Wizard tags step not completed."}, status=status.HTTP_400_BAD_REQUEST)

        base = draft["base"]
        tags = draft["tags"]

        compiled = build_project_creation_payload(
            slug=base["slug"],
            name=base["name"],
            semantic_intent=base["semantic_intent"],
            mlas_tier=base["mlas_tier"],
            btif_classification=base["btif_classification"],
            semantic_tags=tags["semantic_tags"],
        )

        ProjectNode.objects.update_or_create(
            slug=base["slug"],
            defaults={
                "name": base["name"],
                "semantic_intent": base["semantic_intent"],
                "mlas_tier": base["mlas_tier"],
                "btif_classification": base["btif_classification"],
                "metadata": tags.get("metadata", {}),
            },
        )

        cache.delete(key)
        return Response(compiled, status=status.HTTP_200_OK)
