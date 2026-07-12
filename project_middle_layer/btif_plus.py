from __future__ import annotations

from project_middle_layer.models import (
    ProjectEvolutionSnapshot,
    ProjectNode,
    SemanticAgentRun,
    SemanticAnalyticsSnapshot,
    SemanticLineageRecord,
    SemanticVersion,
)


def encode_btif_plus(*, project_slug: str) -> dict[str, object]:
    project = ProjectNode.objects.filter(slug=project_slug).first()
    if not project:
        raise ValueError("Project not found.")

    latest_snapshot = project.evolution_snapshots.first()
    latest_lineage = project.lineage_records.first()
    latest_version = project.semantic_versions.first()
    latest_analytics = SemanticAnalyticsSnapshot.objects.first()
    latest_agent_run = SemanticAgentRun.objects.first()

    return {
        "btif_plus_version": "1.0",
        "project": {
            "slug": project.slug,
            "name": project.name,
            "semantic_intent": project.semantic_intent,
            "mlas_tier": project.mlas_tier,
            "btif_classification": project.btif_classification,
            "metadata": project.metadata,
        },
        "identity_payload": latest_snapshot.identity_payload if latest_snapshot else {},
        "semantic_tags": latest_snapshot.semantic_tags if latest_snapshot else (project.metadata or {}).get("semantic_tags", []),
        "lineage_graph": latest_lineage.lineage_tree if latest_lineage else {},
        "metrics": {
            "drift": latest_snapshot.drift_risk if latest_snapshot else 0.0,
            "confidence": latest_snapshot.confidence_score if latest_snapshot else 0,
            "stability": latest_analytics.stability_mean if latest_analytics else 0.0,
        },
        "analytics_snapshot": {
            "id": latest_analytics.id,
            "metrics": latest_analytics.metrics,
            "chart_series": latest_analytics.chart_series,
        }
        if latest_analytics
        else {},
        "insight_cards": latest_agent_run.insights_generated if latest_agent_run else [],
        "agent_run_logs": {
            "id": latest_agent_run.id,
            "agent_name": latest_agent_run.agent_name,
            "status": latest_agent_run.status,
            "actions_taken": latest_agent_run.actions_taken,
        }
        if latest_agent_run
        else {},
        "version_metadata": {
            "version_id": latest_version.id,
            "version_number": latest_version.version_number,
            "message": latest_version.message,
        }
        if latest_version
        else {},
    }


def decode_btif_plus(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("BTIF+ payload must be a JSON object.")
    return payload


def validate_btif_plus(payload: dict[str, object]) -> dict[str, object]:
    required = ["project", "identity_payload", "semantic_tags", "lineage_graph", "metrics"]
    missing = [field for field in required if field not in payload]
    return {
        "valid": not missing,
        "missing_fields": missing,
    }


def btif_plus_compatibility_matrix() -> dict[str, object]:
    return {
        "btif_plus": "1.0",
        "compatible_gateway_versions": ["v1"],
        "supported_sync_types": ["full", "delta", "version", "lineage", "analytics", "insight"],
    }


def btif_plus_cross_platform_sync_helpers() -> dict[str, object]:
    return {
        "export_helper": "encode_btif_plus",
        "import_helper": "decode_btif_plus",
        "validation_helper": "validate_btif_plus",
    }
