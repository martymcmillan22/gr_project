from __future__ import annotations

from django.utils import timezone

from project_middle_layer.btif_plus import decode_btif_plus, encode_btif_plus, validate_btif_plus
from project_middle_layer.models import SemanticCrossSyncLog
from project_middle_layer.semantic_merge import merge_semantic_states


def run_semantic_cross_sync(*, sync_type: str, target_platform: str, project_slug: str) -> dict[str, object]:
    log = SemanticCrossSyncLog.objects.create(
        sync_type=sync_type,
        source_platform="local",
        target_platform=target_platform,
        status="running",
    )

    try:
        encoded = encode_btif_plus(project_slug=project_slug)
        decoded = decode_btif_plus(encoded)
        validation = validate_btif_plus(decoded)
        if not validation["valid"]:
            raise ValueError("BTIF+ validation failed.")

        merge_result = merge_semantic_states(decoded, decoded, base=decoded)
        summary = {
            "sync_type": sync_type,
            "target_platform": target_platform,
            "project_slug": project_slug,
            "btif_plus_valid": validation["valid"],
            "conflicts": merge_result.get("conflicts", []),
        }

        log.status = "completed"
        log.summary = summary
        log.conflict_report = {"has_conflicts": merge_result.get("has_conflicts", False), "conflicts": merge_result.get("conflicts", [])}
        log.error_message = ""
        log.completed_at = timezone.now()
        log.save(update_fields=["status", "summary", "conflict_report", "error_message", "completed_at"])

        return {
            "cross_sync_log_id": log.id,
            "status": "completed",
            "summary": summary,
        }
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)
        log.completed_at = timezone.now()
        log.save(update_fields=["status", "error_message", "completed_at"])
        return {
            "cross_sync_log_id": log.id,
            "status": "failed",
            "error": str(exc),
        }
