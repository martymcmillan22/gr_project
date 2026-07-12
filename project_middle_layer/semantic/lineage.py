from project_middle_layer.schemas import ProjectSchema


def build_semantic_lineage_explorer(
    schema: ProjectSchema,
    *,
    identity_payload: dict[str, object],
    specialized_path: dict[str, object],
    drift_forecast: dict[str, object],
) -> dict[str, object]:
    identity = identity_payload.get("identity", {}) if isinstance(identity_payload, dict) else {}
    branch_resolution = identity.get("branch_resolution", {}) if isinstance(identity, dict) else {}
    selected_branch = str(branch_resolution.get("selected_branch", "specialization_branch"))

    tags = schema["semantic_tags"]
    tag_groups: dict[str, list[str]] = {}
    for tag in tags:
        root = tag.split("-")[0] if tag else "uncategorized"
        tag_groups.setdefault(root, []).append(tag)

    semantic_clusters = []
    for cluster_name in sorted(tag_groups):
        cluster_tags = sorted(tag_groups[cluster_name])
        semantic_clusters.append(
            {
                "cluster": cluster_name,
                "tags": cluster_tags,
                "weight": len(cluster_tags),
            }
        )

    inferred_ancestry = [
        "Idea",
        "Seed",
        f"Intent:{schema['semantic_intent']}",
        f"Tier:{schema['mlas_tier']}",
        f"BTIF:{schema['btif_classification']}",
        f"Branch:{selected_branch}",
        f"Specialized:{specialized_path.get('selected_branch', selected_branch)}",
    ]

    sibling_concepts = sorted({tag for tag in tags if tag != schema["semantic_intent"].strip().lower()})

    lineage_tree = {
        "project": schema["name"],
        "slug": schema["slug"],
        "identity_uri": identity.get("identity_uri", ""),
        "branch_uri": branch_resolution.get("branch_uri", ""),
        "ancestry": inferred_ancestry,
        "parent_concepts": [
            "Idea",
            "Seed",
            schema["semantic_intent"],
            schema["btif_classification"],
            schema["mlas_tier"],
        ],
        "sibling_concepts": sibling_concepts,
        "semantic_clusters": semantic_clusters,
        "inferred_ancestry": [
            f"{schema['semantic_intent']} -> {selected_branch}",
            f"{schema['btif_classification']} -> {specialized_path.get('selected_branch', selected_branch)}",
            f"{schema['slug']} -> {identity.get('identity_id', '')}",
        ],
        "drift_risk": drift_forecast.get("risk", {}).get("blended_semantic_drift_risk", 0.0)
        if isinstance(drift_forecast, dict)
        else 0.0,
    }

    return {
        "lineage_tree": lineage_tree,
        "semantic_clusters": semantic_clusters,
        "parent_concepts": lineage_tree["parent_concepts"],
        "sibling_concepts": sibling_concepts,
    }
