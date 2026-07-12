import json
from datetime import datetime, timezone

from .models import ProjectEvolutionSnapshot, ProjectNode, SemanticAlert, SemanticLineageRecord


def _iso(dt):
    if not dt:
        return ""
    return dt.astimezone(timezone.utc).isoformat()


def _serialize_snapshot(snapshot: ProjectEvolutionSnapshot) -> dict[str, object]:
    return {
        "id": snapshot.id,
        "created_at": _iso(snapshot.created_at),
        "identity_uri": snapshot.identity_uri,
        "branch_name": snapshot.branch_name,
        "drift_risk": snapshot.drift_risk,
        "confidence_score": snapshot.confidence_score,
        "confidence_label": snapshot.confidence_label,
        "schema_issue_count": snapshot.schema_issue_count,
        "semantic_tags": snapshot.semantic_tags,
        "recommendations": snapshot.recommendations,
    }


def _serialize_lineage(record: SemanticLineageRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "created_at": _iso(record.created_at),
        "lineage_tree": record.lineage_tree,
        "semantic_clusters": record.semantic_clusters,
        "recommendations": record.recommendations,
    }


def _serialize_alert(alert: SemanticAlert) -> dict[str, object]:
    return {
        "id": alert.id,
        "created_at": _iso(alert.created_at),
        "resolved_at": _iso(alert.resolved_at),
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "metadata": alert.metadata,
        "source_snapshot_id": alert.source_snapshot_id,
    }


def build_semantic_export_payload(
    *,
    scope: str = "all",
    project_slug: str | None = None,
    include_history: bool = False,
    max_items: int = 100,
    exported_by: str = "system",
) -> dict[str, object]:
    projects_query = ProjectNode.objects.order_by("slug")
    if scope == "project" and project_slug:
        projects_query = projects_query.filter(slug=project_slug)

    projects = list(projects_query[:max_items])
    project_ids = [project.id for project in projects]

    snapshots = list(ProjectEvolutionSnapshot.objects.filter(project_id__in=project_ids).select_related("project").order_by("-created_at", "-id"))
    lineages = list(SemanticLineageRecord.objects.filter(project_id__in=project_ids).select_related("project").order_by("-created_at", "-id"))
    alerts = list(SemanticAlert.objects.filter(project_id__in=project_ids).select_related("project").order_by("-created_at", "-id"))

    snapshots_by_project: dict[int, list[ProjectEvolutionSnapshot]] = {}
    for item in snapshots:
        snapshots_by_project.setdefault(item.project_id, []).append(item)

    lineages_by_project: dict[int, list[SemanticLineageRecord]] = {}
    for item in lineages:
        lineages_by_project.setdefault(item.project_id, []).append(item)

    alerts_by_project: dict[int, list[SemanticAlert]] = {}
    for item in alerts:
        alerts_by_project.setdefault(item.project_id, []).append(item)

    project_items = []
    for project in projects:
        project_snapshots = snapshots_by_project.get(project.id, [])
        project_lineages = lineages_by_project.get(project.id, [])
        project_alerts = alerts_by_project.get(project.id, [])

        project_entry: dict[str, object] = {
            "project": {
                "id": project.id,
                "slug": project.slug,
                "name": project.name,
                "semantic_intent": project.semantic_intent,
                "mlas_tier": project.mlas_tier,
                "btif_classification": project.btif_classification,
                "metadata": project.metadata,
                "created_at": _iso(project.created_at),
                "updated_at": _iso(project.updated_at),
            },
            "latest_snapshot": _serialize_snapshot(project_snapshots[0]) if project_snapshots else None,
            "latest_lineage": _serialize_lineage(project_lineages[0]) if project_lineages else None,
            "recent_alerts": [_serialize_alert(item) for item in project_alerts[:10]],
        }

        if include_history:
            project_entry["history"] = {
                "snapshots": [_serialize_snapshot(item) for item in project_snapshots],
                "lineage_records": [_serialize_lineage(item) for item in project_lineages],
                "alerts": [_serialize_alert(item) for item in project_alerts],
            }

        project_items.append(project_entry)

    payload = {
        "export_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": exported_by,
        "filter": {
            "scope": scope,
            "project_slug": project_slug,
            "include_history": include_history,
            "max_items": max_items,
        },
        "summary": {
            "project_count": len(projects),
            "snapshot_count": len(snapshots),
            "lineage_record_count": len(lineages),
            "alert_count": len(alerts),
        },
        "projects": project_items,
    }
    return payload


def export_payload_to_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
