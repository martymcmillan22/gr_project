from project_middle_layer.compiler import (
    compile_project_middle_layer_payload,
    compile_specialized_path,
)
from project_middle_layer.schemas import (
    build_project_schema,
    get_projects_json_schema,
    validate_project_schema_dict,
)
from project_middle_layer.semantic import (
    build_semantic_alerts,
    build_identity_confidence_score,
    build_drift_heatmap_data,
    build_project_drift_forecast,
    build_semantic_recommendations,
    build_semantic_lineage_explorer,
    build_semantic_stability_analysis,
    build_semantic_tree_mermaid,
)
from project_middle_layer.tier import build_tier_aware_project


def build_project_creation_payload(
    *,
    slug: str,
    name: str,
    semantic_intent: str,
    mlas_tier: str,
    btif_classification: str,
    semantic_tags: list[str],
) -> dict[str, object]:
    projects_json_schema = get_projects_json_schema()

    schema = build_project_schema(
        slug=slug,
        name=name,
        semantic_intent=semantic_intent,
        mlas_tier=mlas_tier,
        btif_classification=btif_classification,
        semantic_tags=semantic_tags,
    )
    schema_validation_errors = validate_project_schema_dict(schema)
    drift_forecast = build_project_drift_forecast(schema)
    tier_profile = build_tier_aware_project(schema)
    identity_payload = compile_project_middle_layer_payload(schema, drift_forecast=drift_forecast)
    specialized_path = compile_specialized_path(
        schema,
        tier_profile=tier_profile,
        identity_payload=identity_payload,
        drift_forecast=drift_forecast,
    )
    confidence = build_identity_confidence_score(
        schema,
        drift_forecast=drift_forecast,
        identity_payload=identity_payload,
        specialized_path=specialized_path,
        schema_validation_errors=schema_validation_errors,
    )
    lineage_explorer = build_semantic_lineage_explorer(
        schema,
        identity_payload=identity_payload,
        specialized_path=specialized_path,
        drift_forecast=drift_forecast,
    )
    drift_heatmap_data = build_drift_heatmap_data(
        schema,
        drift_forecast=drift_forecast,
        lineage_explorer=lineage_explorer,
    )
    stability_analysis = build_semantic_stability_analysis(
        schema,
        drift_forecast=drift_forecast,
        confidence=confidence,
        lineage_explorer=lineage_explorer,
        specialized_path=specialized_path,
    )
    recommendations = build_semantic_recommendations(
        schema,
        drift_forecast=drift_forecast,
        confidence=confidence,
        stability_analysis=stability_analysis,
        lineage_explorer=lineage_explorer,
        specialized_path=specialized_path,
    )
    alerts = build_semantic_alerts(
        schema,
        drift_forecast=drift_forecast,
        confidence=confidence,
        stability_analysis=stability_analysis,
        schema_validation_errors=schema_validation_errors,
        recent_schema_issue_count=0,
        prior_drift_values=[],
    )

    return {
        "projects_json_schema": projects_json_schema,
        "schema": schema,
        "schema_validation_errors": schema_validation_errors,
        "tier_profile": tier_profile,
        "identity_payload": identity_payload,
        "specialized_path": specialized_path,
        "semantic_tree": build_semantic_tree_mermaid(schema),
        "drift_forecast": drift_forecast,
        "confidence": confidence,
        "lineage_explorer": lineage_explorer,
        "drift_heatmap_data": drift_heatmap_data,
        "stability_analysis": stability_analysis,
        "recommendations": recommendations,
        "semantic_alerts": alerts,
    }
