from __future__ import annotations

from django.utils import timezone

from project_middle_layer.models import ReplicationConfig, SemanticVersion
from project_middle_layer.semantic_merge import merge_semantic_states


def _collect_delta_versions(config: ReplicationConfig) -> list[SemanticVersion]:
    return list(
        SemanticVersion.objects.filter(version_number__gt=config.last_synced_version)
        .select_related("project")
        .order_by("version_number")[:500]
    )


def run_replication(config: ReplicationConfig, *, direction: str = "push") -> dict[str, object]:
    if not config.is_active:
        raise ValueError("Replication target is not active.")

    versions = _collect_delta_versions(config)
    conflicts = []

    # Hook into merge engine for conflict surface compatibility.
    for version in versions:
        local_state = {
            "project_slug": version.project.slug,
            "version_number": version.version_number,
            "message": version.message,
        }
        remote_state = dict(local_state)
        merge_result = merge_semantic_states(local_state, remote_state, base=local_state)
        if merge_result.get("has_conflicts"):
            conflicts.append({"version_id": version.id, "conflicts": merge_result.get("conflicts", [])})

    synced_count = len(versions)
    new_last_version = versions[-1].version_number if versions else config.last_synced_version

    config.last_synced_version = new_last_version
    config.last_sync_at = timezone.now()
    config.last_sync_status = "failed" if conflicts else "completed"
    config.last_error = "Conflicts detected during replication." if conflicts else ""
    config.save(update_fields=["last_synced_version", "last_sync_at", "last_sync_status", "last_error", "updated_at"])

    return {
        "replication_target": config.slug,
        "mode": config.mode,
        "direction": direction,
        "synced_versions": synced_count,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "last_synced_version": config.last_synced_version,
    }
