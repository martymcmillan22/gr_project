from django.http import JsonResponse
from django.views import View

from .pipelines import build_project_creation_payload


class ProjectMiddleLayerStatusView(View):
    def get(self, request):
        payload = build_project_creation_payload(
            slug="project-middle-layer",
            name="Project Middle Layer",
            semantic_intent="ExpandAndIntegrate",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            semantic_tags=["project", "semantic", "identity", "pipeline", "tier", "compiler"],
        )
        return JsonResponse(payload)
