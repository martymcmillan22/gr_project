from __future__ import annotations

from django.contrib import admin
from django.template.response import TemplateResponse

from project_middle_layer.models import ProjectNode
from project_middle_layer.pipelines import build_project_creation_payload


def project_middle_layer_admin_view(request):
    nodes = list(ProjectNode.objects.order_by("-updated_at")[:25])
    project_cards = []

    for node in nodes:
        metadata = node.metadata or {}
        semantic_tags = metadata.get("semantic_tags") or ["project", "semantic", "identity"]
        payload = build_project_creation_payload(
            slug=node.slug,
            name=node.name,
            semantic_intent=node.semantic_intent,
            mlas_tier=node.mlas_tier,
            btif_classification=node.btif_classification,
            semantic_tags=semantic_tags,
        )
        project_cards.append(
            {
                "node": node,
                "branch": payload["identity_payload"]["identity"]["branch_resolution"],
                "specialized_path": payload["specialized_path"],
                "drift_forecast": payload["drift_forecast"],
                "semantic_tree": payload["semantic_tree"],
                "schema_validation_errors": payload["schema_validation_errors"],
            }
        )

    context = {
        **admin.site.each_context(request),
        "title": "Project Middle Layer Admin",
        "project_cards": project_cards,
        "project_count": len(project_cards),
    }
    return TemplateResponse(request, "admin/project_middle_layer_admin.html", context)
