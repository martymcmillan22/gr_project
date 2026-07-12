from __future__ import annotations

from collections import Counter
from math import sqrt

from project_middle_layer.models import ProjectEvolutionSnapshot, ProjectNode, SemanticAlert, SemanticAnalyticsSnapshot, SemanticLineageRecord


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = _mean(values)
    variance = sum((value - avg) ** 2 for value in values) / len(values)
    return sqrt(variance)


def build_semantic_analytics_snapshot(
    *,
    triggered_by: str = "system",
    branch_filter: str = "",
    tier_filter: str = "",
) -> SemanticAnalyticsSnapshot:
    branch = (branch_filter or "").strip().lower()
    tier = (tier_filter or "").strip().lower()

    snapshots_query = ProjectEvolutionSnapshot.objects.select_related("project")
    if branch:
        snapshots_query = snapshots_query.filter(branch_name=branch)

    snapshots = []
    for item in snapshots_query[:2000]:
        node_tier = str((item.project.metadata or {}).get("visibility_tier", "")).strip().lower()
        if tier and node_tier != tier:
            continue
        snapshots.append(item)

    filtered_project_ids = sorted({item.project_id for item in snapshots})
    project_count = len(filtered_project_ids)

    drift_values = [float(item.drift_risk or 0.0) for item in snapshots]
    confidence_values = [float(item.confidence_score or 0.0) for item in snapshots]

    stability_values = []
    for item in snapshots:
        recommendations = item.recommendations or []
        inferred_stability = max(0.0, 100.0 - float(item.drift_risk or 0.0) * 100.0 - len(recommendations) * 2.0)
        stability_values.append(inferred_stability)

    lineage_cluster_counter: Counter[str] = Counter()
    for record in SemanticLineageRecord.objects.select_related("project")[:1000]:
        if filtered_project_ids and record.project_id not in filtered_project_ids:
            continue
        for cluster in (record.semantic_clusters or []):
            if isinstance(cluster, dict):
                label = str(cluster.get("cluster", "unknown"))
            else:
                label = str(cluster)
            lineage_cluster_counter[label] += 1

    tag_counter: Counter[str] = Counter()
    for node in ProjectNode.objects.all()[:1000]:
        if filtered_project_ids and node.id not in filtered_project_ids:
            continue
        metadata = node.metadata or {}
        tags = metadata.get("semantic_tags", [])
        if isinstance(tags, list):
            for tag in tags:
                tag_counter[str(tag).strip().lower()] += 1

    alert_counts: Counter[str] = Counter()
    alert_severity_counts: Counter[str] = Counter()
    for alert in SemanticAlert.objects.all()[:1000]:
        if filtered_project_ids and alert.project_id not in filtered_project_ids:
            continue
        alert_counts[str(alert.alert_type)] += 1
        alert_severity_counts[str(alert.severity)] += 1

    chart_series = [
        {"metric": "drift_mean", "value": round(_mean(drift_values), 4)},
        {"metric": "confidence_mean", "value": round(_mean(confidence_values), 2)},
        {"metric": "stability_mean", "value": round(_mean(stability_values), 2)},
        {"metric": "snapshot_count", "value": len(snapshots)},
    ]

    metrics = {
        "triggered_by": triggered_by,
        "filters": {"branch": branch, "tier": tier},
        "alert_counts": dict(alert_counts),
        "alert_severity_counts": dict(alert_severity_counts),
        "snapshot_count": len(snapshots),
    }

    snapshot = SemanticAnalyticsSnapshot.objects.create(
        metrics=metrics,
        branch_filter=branch,
        tier_filter=tier,
        project_count=project_count,
        drift_mean=round(_mean(drift_values), 4),
        drift_std=round(_std(drift_values), 4),
        confidence_mean=round(_mean(confidence_values), 2),
        confidence_std=round(_std(confidence_values), 2),
        stability_mean=round(_mean(stability_values), 2),
        stability_std=round(_std(stability_values), 2),
        lineage_cluster_map=dict(lineage_cluster_counter),
        tag_frequency_map=dict(tag_counter),
        chart_series=chart_series,
    )
    return snapshot


def build_semantic_analytics_dashboard(*, limit: int = 20, branch_filter: str = "", tier_filter: str = "") -> dict[str, object]:
    branch = (branch_filter or "").strip().lower()
    tier = (tier_filter or "").strip().lower()

    snapshots_query = SemanticAnalyticsSnapshot.objects.all()
    if branch:
        snapshots_query = snapshots_query.filter(branch_filter=branch)
    if tier:
        snapshots_query = snapshots_query.filter(tier_filter=tier)

    snapshots = list(snapshots_query[:limit])
    latest = snapshots[0] if snapshots else None

    trend_points = [
        {
            "id": item.id,
            "created_at": item.created_at,
            "drift_mean": item.drift_mean,
            "confidence_mean": item.confidence_mean,
            "stability_mean": item.stability_mean,
            "project_count": item.project_count,
        }
        for item in reversed(snapshots)
    ]

    available_branches = sorted({str(item.branch_name or "").strip().lower() for item in ProjectEvolutionSnapshot.objects.all()[:1000] if str(item.branch_name or "").strip()})
    available_tiers = sorted({str((item.metadata or {}).get("visibility_tier", "")).strip().lower() for item in ProjectNode.objects.all()[:1000] if str((item.metadata or {}).get("visibility_tier", "")).strip()})

    return {
        "latest": latest,
        "snapshots": snapshots,
        "trend_points": trend_points,
        "filters": {"branch": branch, "tier": tier},
        "available_branches": available_branches,
        "available_tiers": available_tiers,
    }
