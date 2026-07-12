STRICT_MODE_METADATA = {
    "id": "strict-mode",
    "name": "QPU Strict Mode",
    "description": (
        "Semantic metadata for the Strict Mode workflow. "
        "Defines classification tags, BTIF lineage, and semantic intent "
        "for deterministic QPU validation."
    ),

    # Core semantic tags used by BTPE + CLI
    "semantic_tags": [
        "strict",
        "qpu",
        "relay",
        "inverse",
        "temporal",
        "srl",
        "workflow",
        "validation"
    ],

    # BTIF subject lineage (MLAS)
    "btif_subjects": [
        "Math",
        "Language",
        "Arts",
        "Science"
    ],

    # Semantic intent for classification engines
    "semantic_intent": "QPU-Strict-Validation",

    # Workflow node identity map
    "nodes": {
        "inverse_pair_node": {
            "role": "inverse-validation",
            "description": "Validates two complete inverse pairs."
        },
        "relay_alignment_node": {
            "role": "relay-validation",
            "description": "Ensures colors form a contiguous Linear Relay segment."
        },
        "srl_node": {
            "role": "srl-scaling",
            "description": "Validates SRL x4 growth across repositories."
        },
        "temporal_mapping_node": {
            "role": "temporal-mapping",
            "description": "Maps relay segment to Past -> Present-Past -> Present-Future -> Future."
        }
    },

    # Workflow-level semantic classification
    "classification": {
        "type": "workflow",
        "tier": "strict",
        "category": "qpu-validation",
        "engine": "BTPE"
    }
}
