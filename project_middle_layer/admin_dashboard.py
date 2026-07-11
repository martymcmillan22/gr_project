from __future__ import annotations

from urllib.parse import urlencode

from django.contrib import admin
from django.template.response import TemplateResponse

from project_middle_layer.models import ProjectEvolutionSnapshot, ProjectNode, SemanticAlert, SemanticLineageRecord
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
    confidence_distribution: dict[str, int] = {}
    confidence_scores: list[int] = []
    stability_scores: list[int] = []
    heatmap_tags: list[dict[str, object]] = []
    alert_counts: dict[str, int] = {}
    alert_severity_counts: dict[str, int] = {}
    recommendation_counts: dict[str, int] = {}

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

        confidence = card.get("confidence", {}) if isinstance(card, dict) else {}
        confidence_label = str(confidence.get("confidence_label", "Volatile"))
        confidence_distribution[confidence_label] = confidence_distribution.get(confidence_label, 0) + 1
        try:
            confidence_scores.append(int(confidence.get("confidence_score", 0)))
        except (TypeError, ValueError):
            confidence_scores.append(0)

        stability = card.get("stability_analysis", {}) if isinstance(card, dict) else {}
        try:
            stability_scores.append(int(stability.get("stability_score", 0)))
        except (TypeError, ValueError):
            stability_scores.append(0)

        heatmap = card.get("drift_heatmap_data", {}) if isinstance(card, dict) else {}
        if isinstance(heatmap, dict):
            heatmap_tags.extend(heatmap.get("top_drifting_tags", []))

        alerts = card.get("semantic_alerts", []) if isinstance(card, dict) else []
        for alert in alerts:
            alert_type = str(alert.get("alert_type", "unknown"))
            severity = str(alert.get("severity", "low"))
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
            alert_severity_counts[severity] = alert_severity_counts.get(severity, 0) + 1

        recommendations = card.get("recommendations", []) if isinstance(card, dict) else []
        for recommendation in recommendations:
            label = str(recommendation.get("label", "Recommendation"))
            recommendation_counts[label] = recommendation_counts.get(label, 0) + 1

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
        "confidence_distribution": confidence_distribution,
        "average_confidence_score": round(sum(confidence_scores) / project_count, 2),
        "average_stability_score": round(sum(stability_scores) / project_count, 2),
        "top_drifting_tags": heatmap_tags[:5],
        "total_alert_count": sum(alert_counts.values()),
        "alert_counts": alert_counts,
        "alert_severity_counts": alert_severity_counts,
        "recommendation_counts": recommendation_counts,
        "schema_issue_count": schema_issue_count,
        "projects_with_schema_issues": schema_issue_count,
    }


def _build_recommendation_apply_url(node: ProjectNode, recommendation: dict[str, object]) -> str:
    metadata = node.metadata or {}
    suggested_changes = recommendation.get("suggested_changes", {}) if isinstance(recommendation, dict) else {}

    tags = suggested_changes.get("tags")
    if isinstance(tags, list) and tags:
        tags_value = ", ".join(str(tag).strip() for tag in tags if str(tag).strip())
    else:
        tags_value = ", ".join(metadata.get("semantic_tags", []))

    query = {
        "title": node.name,
        "intent": suggested_changes.get("intent", node.semantic_intent),
        "tier": suggested_changes.get("tier", metadata.get("visibility_tier", "public")),
        "tags": tags_value,
        "description": metadata.get("description", ""),
    }
    return f"/project-middle-layer/compile/?{urlencode(query)}"


def project_middle_layer_admin_view(request):
    nodes = list(ProjectNode.objects.order_by("-updated_at")[:25])
    project_cards = []
    recent_snapshots = []

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
                "confidence": payload.get("confidence", {}),
                "lineage_explorer": payload.get("lineage_explorer", {}),
                "drift_heatmap_data": payload.get("drift_heatmap_data", {}),
                "stability_analysis": payload.get("stability_analysis", {}),
                "recommendations": payload.get("recommendations", []),
                "semantic_alerts": payload.get("semantic_alerts", []),
                "semantic_tree": payload["semantic_tree"],
                "schema_validation_errors": payload["schema_validation_errors"],
            }
        )

        project_cards[-1]["recommendation_actions"] = [
            {
                "label": str(rec.get("label", "Apply recommendation")),
                "rationale": str(rec.get("rationale", "")),
                "apply_url": _build_recommendation_apply_url(node, rec),
            }
            for rec in project_cards[-1]["recommendations"]
        ]

    for snapshot in ProjectEvolutionSnapshot.objects.select_related("project")[:10]:
        recent_snapshots.append(snapshot)

    recent_lineage_records = list(SemanticLineageRecord.objects.select_related("project")[:10])
    recent_alerts = list(SemanticAlert.objects.select_related("project", "source_snapshot")[:10])

    semantic_health = _build_semantic_health_summary(project_cards)

    context = {
        **admin.site.each_context(request),
        "title": "Project Middle Layer Admin",
        "compile_project_url": "/project-middle-layer/compile/",
        "batch_compile_url": "/project-middle-layer/batch-compile/",
        "export_url": "/project-middle-layer/export/",
        "pipelines_url": "/project-middle-layer/pipelines/",
        "schedules_url": "/project-middle-layer/schedules/",
        "webhooks_url": "/project-middle-layer/webhooks/",
        "integrations_url": "/project-middle-layer/integrations/",
        "timeline_url": "/project-middle-layer/timeline/",
        "lineage_explorer_url": "/project-middle-layer/lineage/",
        "alerts_url": "/project-middle-layer/alerts/",
        "recommendations_url": "/project-middle-layer/recommendations/",
        "diff_url": "/project-middle-layer/diff/",
        "analytics_url": "/project-middle-layer/analytics/",
        "dashboard_url": "/project-middle-layer/dashboard/",
        "search_url": "/project-middle-layer/search/",
        "insights_url": "/project-middle-layer/insights/",
        "agents_url": "/project-middle-layer/agents/",
        "roles_url": "/project-middle-layer/roles/",
        "collaboration_url": "/project-middle-layer/collaboration/",
        "change_requests_url": "/project-middle-layer/change-requests/",
        "audit_url": "/project-middle-layer/audit/",
        "versions_url": "/project-middle-layer/versions/",
        "merge_url": "/project-middle-layer/merge/",
        "replication_url": "/project-middle-layer/replication/",
        "federation_url": "/project-middle-layer/federation/",
        "shards_url": "/project-middle-layer/shards/",
        "cache_url": "/project-middle-layer/cache/",
        "sync_url": "/project-middle-layer/sync/",
        "distributed_agents_url": "/project-middle-layer/distributed-agents/",
        "marketplace_url": "/project-middle-layer/marketplace/",
        "plugins_url": "/project-middle-layer/plugins/",
        "extensions_url": "/project-middle-layer/extensions/",
        "gateway_url": "/project-middle-layer/gateway/",
        "btif_plus_url": "/project-middle-layer/btif-plus/",
        "external_agents_url": "/project-middle-layer/external-agents/",
        "cross_sync_url": "/project-middle-layer/cross-sync/",
        "project_cards": project_cards,
        "project_count": len(project_cards),
        "recent_snapshots": recent_snapshots,
        "recent_lineage_records": recent_lineage_records,
        "recent_alerts": recent_alerts,
        "semantic_health": semantic_health,
    }
    return TemplateResponse(request, "admin/project_middle_layer_admin.html", context)
