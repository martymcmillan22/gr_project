from project_middle_layer.schemas import ProjectSchema


def build_semantic_recommendations(
    schema: ProjectSchema,
    *,
    drift_forecast: dict[str, object],
    confidence: dict[str, object],
    stability_analysis: dict[str, object],
    lineage_explorer: dict[str, object],
    specialized_path: dict[str, object],
) -> list[dict[str, object]]:
    recommendations: list[dict[str, object]] = []

    risk_block = drift_forecast.get("risk", {}) if isinstance(drift_forecast, dict) else {}
    drift_value = float(risk_block.get("blended_semantic_drift_risk", 0.0) or 0.0)
    confidence_score = int(confidence.get("confidence_score", 0) or 0)
    stability_score = int(stability_analysis.get("stability_score", 0) or 0)
    branch_name = str(specialized_path.get("selected_branch", "specialization_branch"))

    cluster_count = len(lineage_explorer.get("semantic_clusters", [])) if isinstance(lineage_explorer, dict) else 0

    def add(code: str, label: str, rationale: str, suggested_changes: dict[str, object]) -> None:
        recommendations.append(
            {
                "code": code,
                "label": label,
                "rationale": rationale,
                "suggested_changes": suggested_changes,
            }
        )

    if drift_value >= 0.45:
        add(
            "reduce_drift",
            "Reduce semantic spread",
            "Current drift risk is elevated and benefits from tighter semantic boundaries.",
            {
                "tags": schema["semantic_tags"][: max(2, min(4, len(schema["semantic_tags"])))]
            },
        )

    if confidence_score < 70:
        add(
            "strengthen_intent",
            "Strengthen narrative intent",
            "Confidence is below the desired level for stable branch routing.",
            {
                "intent": schema["semantic_intent"],
                "tier": schema["mlas_tier"],
            },
        )

    if stability_score < 70:
        add(
            "recompile_adjusted",
            "Recompile after adjustments",
            "Stability score indicates the project should be recompiled with refined semantics.",
            {
                "tags": schema["semantic_tags"],
                "tier": "public",
            },
        )

    if cluster_count >= 3:
        add(
            "normalize_clusters",
            "Add more consistent tags",
            "Lineage clusters are broad; normalize tags to improve cluster coherence.",
            {
                "tags": sorted(set(schema["semantic_tags"][:3])),
            },
        )

    if branch_name != "stabilization_branch":
        add(
            "clone_branch",
            "Clone into new branch",
            "Current branch is optimized for flow, and a stabilization clone can reduce semantic volatility.",
            {
                "intent": schema["semantic_intent"],
                "tier": "public",
            },
        )

    if not recommendations:
        add(
            "maintain_state",
            "Maintain current semantic state",
            "Signals are already stable; monitor without major changes.",
            {
                "tags": schema["semantic_tags"],
            },
        )

    return recommendations
