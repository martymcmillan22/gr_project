STRICT_MODE_QPU_SCHEMA = {
    "schema_id": "strict-mode-qpu",
    "schema_version": "1.0.0",
    "workflow_id": "strict-mode",
    "required": [
        "workflow_id",
        "name",
        "inverse_pairs",
        "relay_segment",
        "srl_values",
        "qpu",
        "semantic",
    ],
    "properties": {
        "workflow_id": {"type": "string", "const": "strict-mode"},
        "name": {"type": "string", "min_length": 1},
        "inverse_pairs": {
            "type": "array",
            "length": 2,
            "item_type": "array",
            "item_length": 2,
            "item_value_type": "string",
        },
        "relay_segment": {
            "type": "array",
            "length": 4,
            "item_type": "string",
        },
        "srl_values": {
            "type": "array",
            "length": 4,
            "item_type": "integer",
            "growth_factor": 4,
            "seed": 4,
        },
        "qpu": {
            "type": "array",
            "length": 4,
            "item_type": "object",
            "required": ["tense", "srl", "subject"],
        },
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


def build_strict_mode_semantic_block(*, semantic_intent, semantic_tags, btif_subjects, classification, node_roles):
    return {
        "semantic_intent": semantic_intent,
        "semantic_tags": list(semantic_tags),
        "btif_subjects": list(btif_subjects),
        "classification": dict(classification),
        "node_roles": dict(node_roles),
    }


def validate_strict_mode_qpu(payload):
    required = STRICT_MODE_QPU_SCHEMA["required"]
    missing = [key for key in required if key not in payload]
    if missing:
        return False, f"Missing required keys: {missing}"

    if payload.get("workflow_id") != "strict-mode":
        return False, "workflow_id must be 'strict-mode'"

    inverse_pairs = payload.get("inverse_pairs", [])
    if len(inverse_pairs) != 2 or any(len(pair) != 2 for pair in inverse_pairs):
        return False, "inverse_pairs must contain exactly two color pairs"

    relay_segment = payload.get("relay_segment", [])
    if len(relay_segment) != 4:
        return False, "relay_segment must contain exactly four colors"

    srl_values = payload.get("srl_values", [])
    if len(srl_values) != 4:
        return False, "srl_values must contain exactly four values"

    expected = [4, 16, 64, 256]
    if srl_values != expected:
        return False, f"srl_values must match {expected}"

    qpu = payload.get("qpu", [])
    if len(qpu) != 4:
        return False, "qpu must contain exactly four temporal records"

    semantic = payload.get("semantic", {})
    semantic_required = STRICT_MODE_QPU_SCHEMA["properties"]["semantic"]["required"]
    semantic_missing = [key for key in semantic_required if key not in semantic]
    if semantic_missing:
        return False, f"semantic block missing keys: {semantic_missing}"

    return True, "ok"
