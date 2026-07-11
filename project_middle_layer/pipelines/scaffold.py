from project_middle_layer.compiler import compile_project_middle_layer_payload
from project_middle_layer.schemas import (
    build_project_schema,
    get_projects_json_schema,
    validate_project_schema_dict,
)
from project_middle_layer.semantic import build_semantic_tree_mermaid
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

    return {
        "projects_json_schema": projects_json_schema,
        "schema": schema,
        "schema_validation_errors": schema_validation_errors,
        "tier_profile": build_tier_aware_project(schema),
        "identity_payload": compile_project_middle_layer_payload(schema),
        "semantic_tree": build_semantic_tree_mermaid(schema),
    }
