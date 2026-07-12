from project_middle_layer.schemas import ProjectSchema


def build_drift_heatmap_data(
    schema: ProjectSchema,
    *,
    drift_forecast: dict[str, object],
    lineage_explorer: dict[str, object],
) -> dict[str, object]:
    signals = drift_forecast.get("signals", {}) if isinstance(drift_forecast, dict) else {}
    risk_block = drift_forecast.get("risk", {}) if isinstance(drift_forecast, dict) else {}
    blended_risk = float(risk_block.get("blended_semantic_drift_risk", 0.0) or 0.0)
    singleton_tags = set(str(tag).strip().lower() for tag in signals.get("singleton_tags", []) if str(tag).strip())

    tag_intensities = []
    for tag in schema["semantic_tags"]:
        volatility = 1.0 if tag in singleton_tags else 0.35
        intensity = round(min(1.0, (blended_risk * 0.7) + (volatility * 0.3)), 4)
        tag_intensities.append({"dimension": "tag", "label": tag, "intensity": intensity})

    cluster_intensities = []
    for cluster in lineage_explorer.get("semantic_clusters", []):
        weight = int(cluster.get("weight", 1) or 1)
        cluster_intensity = round(min(1.0, (blended_risk * 0.6) + ((weight / max(1, len(schema["semantic_tags"]))) * 0.4)), 4)
        cluster_intensities.append(
            {
                "dimension": "cluster",
                "label": str(cluster.get("cluster", "cluster")),
                "intensity": cluster_intensity,
            }
        )

    top_drifting_tags = sorted(tag_intensities, key=lambda item: item["intensity"], reverse=True)[:3]
    stable_tags = [item["label"] for item in tag_intensities if item["intensity"] < 0.4]

    return {
        "heatmap_grid": {
            "tags": tag_intensities,
            "clusters": cluster_intensities,
            "time": [],
        },
        "top_drifting_tags": top_drifting_tags,
        "stable_tags": stable_tags,
    }
