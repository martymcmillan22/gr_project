from __future__ import annotations

from django.contrib import admin
from django.template.response import TemplateResponse

from project_middle_layer.models import ProjectNode
from project_middle_layer.pipelines import build_project_creation_payload


def _risk_level_to_score(risk_level: str) -> int:
    if risk_level == "high":
        return 25
    if risk_level == "medium":
        return 60
    return 90


def _build_semantic_health_summary(project_cards: list[dict[str, object]]) -> dict[str, object]:
    project_count = len(project_cards)
    if not project_cards:
        return {
            "status": "empty",
            "label": "No Projects",
            "score": 0,
            "average_drift_risk": 0.0,
            "branch_distribution": {},
            "schema_issue_count": 0,
            "projects_with_schema_issues": 0,
        }

    drift_scores: list[float] = []
    branch_distribution: dict[str, int] = {}
    schema_issue_count = 0

    for card in project_cards:
        drift_forecast = card.get("drift_forecast", {})
        drift_risk = drift_forecast.get("risk", {}) if isinstance(drift_forecast, dict) else {}
        drift_value = drift_risk.get("blended_semantic_drift_risk", 0.0)
        try:
            drift_scores.append(float(drift_value))
        except (TypeError, ValueError):
            drift_scores.append(0.0)

        branch = card.get("branch", {}) if isinstance(card, dict) else {}
        branch_name = str(branch.get("selected_branch", "unknown"))
        branch_distribution[branch_name] = branch_distribution.get(branch_name, 0) + 1

        if card.get("schema_validation_errors"):
            schema_issue_count += 1

    average_drift_risk = round(sum(drift_scores) / project_count, 4)
    health_score = max(
        0,
        min(
            100,
            round(
                (sum(_risk_level_to_score(str(card.get("drift_forecast", {}).get("risk", {}).get("risk_level", "low"))) for card in project_cards) / project_count)
                - (schema_issue_count * 8),
            ),
        ),
    )

    return {
        "status": "healthy" if health_score >= 70 else "watch" if health_score >= 45 else "critical",
        "label": "Healthy" if health_score >= 70 else "Watch" if health_score >= 45 else "Critical",
        "score": health_score,
        "average_drift_risk": average_drift_risk,
        "branch_distribution": branch_distribution,
        "schema_issue_count": schema_issue_count,
        "projects_with_schema_issues": schema_issue_count,
    }


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

    semantic_health = _build_semantic_health_summary(project_cards)

    context = {
        **admin.site.each_context(request),
        "title": "Project Middle Layer Admin",
        "project_cards": project_cards,
        "project_count": len(project_cards),
        "semantic_health": semantic_health,
    }
    return TemplateResponse(request, "admin/project_middle_layer_admin.html", context)
