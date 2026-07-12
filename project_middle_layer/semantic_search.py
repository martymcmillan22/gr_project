from __future__ import annotations

from collections import defaultdict

from project_middle_layer.models import (
    ProjectEvolutionSnapshot,
    ProjectNode,
    SemanticAlert,
    SemanticIntegration,
    SemanticLineageRecord,
    SemanticPipeline,
    SemanticSchedule,
    SemanticWebhook,
)


def _matches(value: str, query: str) -> bool:
    return query in value.lower()


def run_semantic_search(query: str, *, limit: int = 50) -> dict[str, object]:
    q = (query or "").strip().lower()
    if not q:
        return {
            "query": "",
            "summary": {"total": 0},
            "results": {},
            "facets": {"types": {}},
        }

    results: dict[str, list[dict[str, object]]] = defaultdict(list)

    for node in ProjectNode.objects.all()[:1000]:
        metadata = node.metadata or {}
        tags = metadata.get("semantic_tags", []) if isinstance(metadata, dict) else []
        haystacks = [node.slug, node.name, node.semantic_intent, node.mlas_tier, node.btif_classification]
        haystacks.extend(str(tag) for tag in tags)
        if any(_matches(str(item), q) for item in haystacks):
            results["projects"].append({"id": node.id, "slug": node.slug, "name": node.name})

    for snapshot in ProjectEvolutionSnapshot.objects.select_related("project")[:1000]:
        identity_uri = str(snapshot.identity_uri or "")
        branch = str(snapshot.branch_name or "")
        if _matches(identity_uri, q) or _matches(branch, q):
            results["snapshots"].append(
                {
                    "id": snapshot.id,
                    "project_slug": snapshot.project.slug,
                    "identity_uri": identity_uri,
                    "branch": branch,
                }
            )

    for lineage in SemanticLineageRecord.objects.select_related("project")[:1000]:
        tree_text = str(lineage.lineage_tree)
        cluster_text = str(lineage.semantic_clusters)
        if _matches(tree_text, q) or _matches(cluster_text, q):
            results["lineage"].append({"id": lineage.id, "project_slug": lineage.project.slug})

    for alert in SemanticAlert.objects.select_related("project")[:1000]:
        if _matches(alert.alert_type, q) or _matches(alert.message, q) or _matches(alert.severity, q):
            results["alerts"].append({"id": alert.id, "project_slug": alert.project.slug, "severity": alert.severity, "type": alert.alert_type})

    for pipeline in SemanticPipeline.objects.all()[:500]:
        if _matches(pipeline.slug, q) or _matches(pipeline.name, q):
            results["pipelines"].append({"id": pipeline.id, "slug": pipeline.slug, "name": pipeline.name})

    for schedule in SemanticSchedule.objects.select_related("pipeline")[:500]:
        pipeline_slug = schedule.pipeline.slug if schedule.pipeline else ""
        if _matches(schedule.slug, q) or _matches(schedule.name, q) or _matches(pipeline_slug, q):
            results["schedules"].append({"id": schedule.id, "slug": schedule.slug, "name": schedule.name})

    for webhook in SemanticWebhook.objects.all()[:500]:
        if _matches(webhook.name, q) or _matches(webhook.event_type, q):
            results["webhooks"].append({"id": webhook.id, "name": webhook.name, "event_type": webhook.event_type})

    for integration in SemanticIntegration.objects.all()[:500]:
        if _matches(integration.slug, q) or _matches(integration.name, q) or _matches(integration.target_system, q):
            results["integrations"].append({"id": integration.id, "slug": integration.slug, "name": integration.name, "target_system": integration.target_system})

    trimmed_results = {}
    facets = {"types": {}}
    total = 0
    for key, values in results.items():
        trimmed = values[:limit]
        trimmed_results[key] = trimmed
        facets["types"][key] = len(trimmed)
        total += len(trimmed)

    return {
        "query": query,
        "summary": {"total": total},
        "results": trimmed_results,
        "facets": facets,
    }
