from project_middle_layer.schemas import ProjectSchema


def build_tier_aware_project(schema: ProjectSchema) -> dict[str, object]:
    return {
        "slug": schema["slug"],
        "name": schema["name"],
        "tier": schema["mlas_tier"],
        "intent": schema["semantic_intent"],
        "classification": schema["btif_classification"],
        "lifecycle": ["IDEA", "SEED", "PROJECT", "IDENTITY_BRANCH", "SPECIALIZED_PATH"],
        "stage_gates": {
            "IDEA->SEED": ["raw-content-captured", "semantic-tags-normalized"],
            "SEED->PROJECT": ["intent-locked", "mlas-tier-confirmed", "btif-route-confirmed"],
            "PROJECT->IDENTITY_BRANCH": ["identity-compiled", "lineage-recorded"],
            "IDENTITY_BRANCH->SPECIALIZED_PATH": ["branch-policy-selected", "runtime-route-published"],
        },
        "routing": {
            "semantic_route": f"btif://{schema['btif_classification'].lower()}/{schema['semantic_intent'].lower()}/{schema['slug']}",
            "lineage": f"workflow/{schema['slug']}",
        },
    }
