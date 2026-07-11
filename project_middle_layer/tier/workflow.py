from project_middle_layer.schemas import ProjectSchema


def build_tier_aware_project(schema: ProjectSchema) -> dict[str, str]:
    return {
        "slug": schema["slug"],
        "name": schema["name"],
        "tier": schema["mlas_tier"],
        "intent": schema["semantic_intent"],
        "classification": schema["btif_classification"],
    }
