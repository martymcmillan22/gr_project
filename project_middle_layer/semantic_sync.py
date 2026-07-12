from __future__ import annotations

from django.utils import timezone

from project_middle_layer.models import ReplicationConfig, SemanticSyncLog
from project_middle_layer.replication import run_replication


def run_semantic_sync(*, sync_type: str, target_slug: str | None = None) -> dict[str, object]:
    log = SemanticSyncLog.objects.create(
        sync_type=sync_type,
        source_node="local",
        target_node=target_slug or "all",
        status="running",
    )

    try:
        query = ReplicationConfig.objects.filter(is_active=True)
        if target_slug:
            query = query.filter(slug=target_slug)
        targets = list(query[:50])

        results = []
        for target in targets:
            results.append(run_replication(target, direction=target.direction))

        summary = {
            "target_count": len(targets),
            "results": results,
        }
        log.status = "completed"
        log.summary = summary
        log.error_message = ""
        log.completed_at = timezone.now()
        log.save(update_fields=["status", "summary", "error_message", "completed_at"])
        return {"sync_log_id": log.id, "status": "completed", "summary": summary}
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)
        log.completed_at = timezone.now()
        log.save(update_fields=["status", "error_message", "completed_at"])
        return {"sync_log_id": log.id, "status": "failed", "error": str(exc)}
