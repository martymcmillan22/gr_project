CREATOR_WORKFLOW_QPU_SCHEMA = {
    "schema_id": "creator-workflow-qpu",
    "schema_version": "1.0.0",
    "workflow_id": "creator-workflow",
    "required": [
        "workflow_id",
        "name",
        "source_workflow_id",
        "source_name",
        "source_qpu",
        "story_beats",
        "outline",
        "scenes",
        "narrative",
        "semantic",
    ],
    "properties": {
        "workflow_id": {"type": "string", "const": "creator-workflow"},
        "name": {"type": "string", "min_length": 1},
        "source_workflow_id": {"type": "string", "min_length": 1},
        "source_name": {"type": "string", "min_length": 1},
        "source_qpu": {"type": "array", "length": 4},
        "story_beats": {"type": "array", "length": 4},
        "outline": {"type": "array", "length": 4},
        "scenes": {"type": "array", "length": 4},
        "narrative": {"type": "string", "min_length": 1},
        "semantic": {
            "type": "object",
            "required": [
                "semantic_intent",
                "semantic_tags",
                "btif_subjects",
                "classification",
                "node_roles",
            ],
        },
    },
}


def build_creator_workflow_semantic_block(*, semantic_intent, semantic_tags, btif_subjects, classification, node_roles):
    return {
        "semantic_intent": semantic_intent,
        "semantic_tags": list(semantic_tags),
        "btif_subjects": list(btif_subjects),
        "classification": dict(classification),
        "node_roles": dict(node_roles),
    }


def validate_creator_workflow_qpu(payload):
    required = CREATOR_WORKFLOW_QPU_SCHEMA["required"]
    missing = [key for key in required if key not in payload]
    if missing:
        return False, f"Missing required keys: {missing}"

    if payload.get("workflow_id") != "creator-workflow":
        return False, "workflow_id must be 'creator-workflow'"

    source_qpu = payload.get("source_qpu", [])
    if len(source_qpu) != 4:
        return False, "source_qpu must contain exactly four records"

    story_beats = payload.get("story_beats", [])
    if len(story_beats) != 4:
        return False, "story_beats must contain exactly four beats"

    outline = payload.get("outline", [])
    if len(outline) != 4:
        return False, "outline must contain exactly four sections"

    scenes = payload.get("scenes", [])
    if len(scenes) != 4:
        return False, "scenes must contain exactly four scenes"

    narrative = payload.get("narrative", "")
    if not str(narrative).strip():
        return False, "narrative must be non-empty"

    semantic = payload.get("semantic", {})
    semantic_required = CREATOR_WORKFLOW_QPU_SCHEMA["properties"]["semantic"]["required"]
    semantic_missing = [key for key in semantic_required if key not in semantic]
    if semantic_missing:
        return False, f"semantic block missing keys: {semantic_missing}"

    return True, "ok"
