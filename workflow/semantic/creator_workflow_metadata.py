CREATOR_WORKFLOW_METADATA = {
    "id": "creator-workflow",
    "name": "Narrative Creator Workflow",
    "description": (
        "Semantic metadata for the Creator Workflow. "
        "Transforms a validated QPU into deterministic narrative structure."
    ),
    "semantic_tags": [
        "creator",
        "narrative",
        "transformer",
        "output",
        "workflow",
    ],
    "btif_subjects": [
        "Math",
        "Language",
        "Arts",
        "Science",
    ],
    "semantic_intent": "QPU-Creator-Output",
    "nodes": {
        "creator_seed_node": {
            "role": "seed-validation",
            "description": "Validates the source QPU and seeds the narrative generator.",
        },
        "creator_arc_node": {
            "role": "arc-generation",
            "description": "Maps the source QPU into a four-beat narrative arc.",
        },
        "creator_outline_node": {
            "role": "outline-generation",
            "description": "Expands narrative beats into a deterministic outline.",
        },
        "creator_render_node": {
            "role": "rendering",
            "description": "Renders the outline into structured narrative output.",
        },
    },
    "classification": {
        "type": "workflow",
        "tier": "creator",
        "category": "narrative-generation",
        "engine": "BTPE",
    },
}
