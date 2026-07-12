from __future__ import annotations

from project_middle_layer.models import ProjectNode, SemanticShard


def _match_shard(project: ProjectNode, shard: SemanticShard) -> bool:
    metadata = project.metadata or {}
    tags = [str(item).strip().lower() for item in metadata.get("semantic_tags", [])]
    tier = str(metadata.get("visibility_tier", "")).strip().lower()

    if shard.strategy == "branch":
        selected_branch = str((metadata.get("identity_payload", {}).get("identity", {}).get("branch_resolution", {}) or {}).get("selected_branch", "")).strip().lower()
        return bool(shard.branch and shard.branch.strip().lower() == selected_branch)

    if shard.strategy == "tier":
        return bool(shard.tier and shard.tier.strip().lower() == tier)

    if shard.strategy == "slug_prefix":
        return bool(shard.project_slug_prefix and project.slug.startswith(shard.project_slug_prefix))

    if shard.strategy == "cluster":
        return bool(shard.cluster_label and shard.cluster_label.strip().lower() in tags)

    return False


def assign_project_to_shard(project: ProjectNode) -> SemanticShard | None:
    for shard in SemanticShard.objects.filter(is_active=True).order_by("name"):
        if _match_shard(project, shard):
            return shard
    return None


def build_shard_map() -> dict[str, object]:
    mapping = []
    for project in ProjectNode.objects.all()[:500]:
        shard = assign_project_to_shard(project)
        mapping.append({"project_slug": project.slug, "shard": shard.slug if shard else "unassigned"})
    return {"assignments": mapping, "total": len(mapping)}


def rebalance_shards() -> dict[str, object]:
    shards = list(SemanticShard.objects.filter(is_active=True).order_by("name"))
    if not shards:
        return {"rebalanced": 0, "status": "no-active-shards"}

    for shard in shards:
        shard.health_score = max(60, min(100, shard.health_score))
        shard.status = "healthy" if shard.health_score >= 80 else "watch"
        shard.save(update_fields=["health_score", "status", "updated_at"])

    return {"rebalanced": len(shards), "status": "completed"}
