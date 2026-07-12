def build_semantic_diff(
    source: dict[str, object],
    target: dict[str, object],
) -> dict[str, object]:
    source_tags = set(str(tag).strip().lower() for tag in source.get("semantic_tags", []) if str(tag).strip())
    target_tags = set(str(tag).strip().lower() for tag in target.get("semantic_tags", []) if str(tag).strip())

    added_tags = sorted(target_tags - source_tags)
    removed_tags = sorted(source_tags - target_tags)

    source_drift = float(source.get("drift_risk", 0.0) or 0.0)
    target_drift = float(target.get("drift_risk", 0.0) or 0.0)
    source_confidence = int(source.get("confidence_score", 0) or 0)
    target_confidence = int(target.get("confidence_score", 0) or 0)
    source_stability = int(source.get("stability_score", 0) or 0)
    target_stability = int(target.get("stability_score", 0) or 0)

    source_branch = str(source.get("branch_name", ""))
    target_branch = str(target.get("branch_name", ""))
    source_final_uri = str(source.get("final_identity_uri", ""))
    target_final_uri = str(target.get("final_identity_uri", ""))

    return {
        "tag_changes": {
            "added": added_tags,
            "removed": removed_tags,
            "unchanged_count": len(source_tags & target_tags),
        },
        "drift_delta": round(target_drift - source_drift, 4),
        "confidence_delta": target_confidence - source_confidence,
        "stability_delta": target_stability - source_stability,
        "branch_changes": {
            "from": source_branch,
            "to": target_branch,
            "changed": source_branch != target_branch,
        },
        "identity_changes": {
            "from": str(source.get("identity_uri", "")),
            "to": str(target.get("identity_uri", "")),
            "changed": str(source.get("identity_uri", "")) != str(target.get("identity_uri", "")),
        },
        "specialized_path_changes": {
            "from": source_final_uri,
            "to": target_final_uri,
            "changed": source_final_uri != target_final_uri,
        },
    }
