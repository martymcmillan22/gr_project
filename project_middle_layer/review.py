from __future__ import annotations

from django.utils import timezone

from project_middle_layer.models import ProjectNode, SemanticChangeRequest


def create_change_request(*, project: ProjectNode, author, proposed_changes: dict[str, object]) -> SemanticChangeRequest:
    return SemanticChangeRequest.objects.create(
        project=project,
        author=author,
        proposed_changes=proposed_changes,
        status="pending",
    )


def apply_change_request(*, change_request: SemanticChangeRequest, reviewer, approve: bool, notes: str = "") -> SemanticChangeRequest:
    change_request.reviewer = reviewer
    change_request.review_notes = notes
    change_request.reviewed_at = timezone.now()

    if not approve:
        change_request.status = "rejected"
        change_request.save(update_fields=["reviewer", "review_notes", "reviewed_at", "status"])
        return change_request

    proposed = change_request.proposed_changes or {}
    project = change_request.project

    updates = {}
    if "name" in proposed:
        updates["name"] = str(proposed.get("name") or project.name)
    if "semantic_intent" in proposed:
        updates["semantic_intent"] = str(proposed.get("semantic_intent") or project.semantic_intent)
    if "mlas_tier" in proposed:
        updates["mlas_tier"] = str(proposed.get("mlas_tier") or project.mlas_tier)
    if "btif_classification" in proposed:
        updates["btif_classification"] = str(proposed.get("btif_classification") or project.btif_classification)
    if "metadata" in proposed and isinstance(proposed.get("metadata"), dict):
        updates["metadata"] = {**(project.metadata or {}), **proposed["metadata"]}

    if updates:
        for key, value in updates.items():
            setattr(project, key, value)
        project.save(update_fields=[*updates.keys(), "updated_at"])

    change_request.status = "approved"
    change_request.save(update_fields=["reviewer", "review_notes", "reviewed_at", "status"])
    return change_request
