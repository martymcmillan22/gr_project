from __future__ import annotations

from project_middle_layer.models import ProjectNode, SemanticAuditLog


def record_semantic_audit_log(
    *,
    actor=None,
    action: str,
    project: ProjectNode | None = None,
    payload: dict[str, object] | None = None,
    source: str = "system",
) -> SemanticAuditLog:
    return SemanticAuditLog.objects.create(
        actor=actor,
        action=action,
        project=project,
        payload=payload or {},
        source=source,
    )
