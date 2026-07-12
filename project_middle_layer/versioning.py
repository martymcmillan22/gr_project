from __future__ import annotations

from django.db.models import Max

from project_middle_layer.models import ProjectEvolutionSnapshot, ProjectNode, SemanticVersion


def commit_semantic_version(*, project: ProjectNode, author=None, message: str = "") -> SemanticVersion:
    latest_snapshot = project.evolution_snapshots.first()
    latest_number = project.semantic_versions.aggregate(max_number=Max("version_number")).get("max_number") or 0
    return SemanticVersion.objects.create(
        project=project,
        version_number=latest_number + 1,
        snapshot=latest_snapshot,
        author=author,
        message=(message or "").strip(),
    )


def list_semantic_versions(*, project: ProjectNode) -> list[SemanticVersion]:
    return list(project.semantic_versions.select_related("snapshot", "author").order_by("-version_number"))


def checkout_semantic_version(*, version: SemanticVersion, actor=None) -> ProjectNode:
    project = version.project
    snapshot = version.snapshot
    if not snapshot:
        return project

    if snapshot.identity_payload and isinstance(snapshot.identity_payload, dict):
        identity = snapshot.identity_payload.get("identity", {})
        if isinstance(identity, dict):
            project.slug = str(identity.get("slug", project.slug) or project.slug)

    metadata = project.metadata or {}
    metadata.update(
        {
            "semantic_tags": snapshot.semantic_tags,
            "identity_payload": snapshot.identity_payload,
            "drift_forecast": snapshot.drift_forecast,
            "specialized_path": snapshot.specialized_path,
            "restored_from_version": version.version_number,
            "restored_by": getattr(actor, "username", "system") if actor else "system",
        }
    )
    project.metadata = metadata
    project.save(update_fields=["metadata", "updated_at"])

    return project
