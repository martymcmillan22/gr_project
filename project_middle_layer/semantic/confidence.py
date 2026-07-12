from project_middle_layer.schemas import ProjectSchema


def build_identity_confidence_score(
    schema: ProjectSchema,
    *,
    drift_forecast: dict[str, object],
    identity_payload: dict[str, object],
    specialized_path: dict[str, object],
    schema_validation_errors: list[str],
) -> dict[str, object]:
    drift_risk = drift_forecast.get("risk", {}) if isinstance(drift_forecast, dict) else {}
    drift_value = float(drift_risk.get("blended_semantic_drift_risk", 1.0) or 1.0)

    signals = drift_forecast.get("signals", {}) if isinstance(drift_forecast, dict) else {}
    project_tag_count = max(1, int(signals.get("project_tag_count", len(schema["semantic_tags"])) or 1))
    singleton_tag_count = int(signals.get("singleton_tag_count", project_tag_count) or project_tag_count)
    tag_volatility = min(1.0, max(0.0, singleton_tag_count / project_tag_count))

    branch_resolution = {}
    if isinstance(identity_payload, dict):
        identity = identity_payload.get("identity", {})
        if isinstance(identity, dict):
            branch_resolution = identity.get("branch_resolution", {}) if isinstance(identity.get("branch_resolution"), dict) else {}

    branch_stability = float(branch_resolution.get("confidence", 0.8) or 0.8)
    lineage_strength = 0.9 if str(identity_payload.get("identity", {}).get("lineage", "")).strip() else 0.6

    schema_consistency = 1.0 if not schema_validation_errors else max(0.35, 1.0 - (0.15 * len(schema_validation_errors)))

    compile_readiness = 1.0 if specialized_path.get("compile_status") == "ready" else 0.5

    weighted_score = (
        (1.0 - drift_value) * 0.30
        + (1.0 - tag_volatility) * 0.20
        + branch_stability * 0.20
        + lineage_strength * 0.15
        + schema_consistency * 0.10
        + compile_readiness * 0.05
    )
    confidence_score = max(0, min(100, round(weighted_score * 100)))

    if confidence_score >= 80:
        confidence_label = "Stable"
    elif confidence_score >= 60:
        confidence_label = "Moderate"
    else:
        confidence_label = "Volatile"

    return {
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "signals": {
            "drift_risk": drift_value,
            "tag_volatility": round(tag_volatility, 4),
            "branch_stability": round(branch_stability, 4),
            "lineage_strength": round(lineage_strength, 4),
            "schema_consistency": round(schema_consistency, 4),
            "compile_readiness": round(compile_readiness, 4),
        },
    }
