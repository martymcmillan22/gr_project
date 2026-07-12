from project_middle_layer.schemas import ProjectSchema


def build_semantic_stability_analysis(
    schema: ProjectSchema,
    *,
    drift_forecast: dict[str, object],
    confidence: dict[str, object],
    lineage_explorer: dict[str, object],
    specialized_path: dict[str, object],
) -> dict[str, object]:
    risk_block = drift_forecast.get("risk", {}) if isinstance(drift_forecast, dict) else {}
    drift_value = float(risk_block.get("blended_semantic_drift_risk", 0.0) or 0.0)
    confidence_score = int(confidence.get("confidence_score", 0) or 0)

    lineage_cluster_count = len(lineage_explorer.get("semantic_clusters", []))
    branch_name = str(specialized_path.get("selected_branch", specialized_path.get("forms", [{}])[0].get("branch", "")))

    branch_bonus = 10 if branch_name == "stabilization_branch" else 6 if branch_name == "governance_branch" else 8
    lineage_bonus = min(12, lineage_cluster_count * 3)
    drift_penalty = round(drift_value * 40)

    stability_score = max(
        0,
        min(
            100,
            round((confidence_score * 0.55) + branch_bonus + lineage_bonus - drift_penalty),
        ),
    )

    if stability_score >= 80:
        stability_label = "Stable"
    elif stability_score >= 60:
        stability_label = "Watch"
    else:
        stability_label = "At Risk"

    recommended_actions: list[str] = []
    if drift_value >= 0.45:
        recommended_actions.append("Add more consistent tags")
        recommended_actions.append("Reduce semantic spread")
    if confidence_score < 75:
        recommended_actions.append("Strengthen narrative intent")
    if branch_name != "stabilization_branch":
        recommended_actions.append("Recompile after adjustments")
    if not recommended_actions:
        recommended_actions.append("Maintain current semantic structure")

    deduped_actions: list[str] = []
    seen_actions = set()
    for action in recommended_actions:
        if action not in seen_actions:
            deduped_actions.append(action)
            seen_actions.add(action)

    return {
        "stability_score": stability_score,
        "stability_label": stability_label,
        "recommended_actions": deduped_actions,
        "signals": {
            "branch_name": branch_name,
            "drift_value": round(drift_value, 4),
            "confidence_score": confidence_score,
            "lineage_cluster_count": lineage_cluster_count,
        },
    }
