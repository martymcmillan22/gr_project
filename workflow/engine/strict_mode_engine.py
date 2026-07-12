try:
    from workflow.errors.strict_mode_errors import RelaySegmentError, SRLGrowthError, StrictModeError
    from workflow.nodes.inverse_pair_node import InversePairNode
    from workflow.nodes.relay_alignment_node import RelayAlignmentNode
    from workflow.nodes.srl_node import SRLNode
    from workflow.nodes.temporal_mapping_node import TemporalMappingNode
    from workflow.semantic.strict_mode_propagation import StrictModePropagation
    from workflow.semantic.strict_mode_qpu_schema import (
        STRICT_MODE_QPU_SCHEMA,
        build_strict_mode_semantic_block,
        validate_strict_mode_qpu,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from errors.strict_mode_errors import RelaySegmentError, SRLGrowthError, StrictModeError
    from nodes.inverse_pair_node import InversePairNode
    from nodes.relay_alignment_node import RelayAlignmentNode
    from nodes.srl_node import SRLNode
    from nodes.temporal_mapping_node import TemporalMappingNode
    from semantic.strict_mode_propagation import StrictModePropagation
    from semantic.strict_mode_qpu_schema import (
        STRICT_MODE_QPU_SCHEMA,
        build_strict_mode_semantic_block,
        validate_strict_mode_qpu,
    )


class StrictModeEngine:
    """
    Executes the Strict Mode workflow as defined in strict_mode.workflow.json.
    This module provides deterministic node sequencing and structured error handling.
    """

    def __init__(self, definition):
        self.definition = definition
        self.nodes = self._load_nodes(definition)
        self.propagation = StrictModePropagation()

    def _load_nodes(self, definition):
        """
        Load node configurations from workflow definition JSON.
        """
        node_map = {}

        for node_def in definition["nodes"]:
            node_id = node_def["id"]
            config = node_def.get("config", {})

            if node_id == "inverse_pair_node":
                node_map[node_id] = InversePairNode(config)
            elif node_id == "relay_alignment_node":
                node_map[node_id] = RelayAlignmentNode(config)
            elif node_id == "srl_node":
                node_map[node_id] = SRLNode(config)
            elif node_id == "temporal_mapping_node":
                node_map[node_id] = TemporalMappingNode(config)

        return node_map

    def run(self, payload):
        """
        Executes the Strict Mode workflow end-to-end.
        """
        relay_segment_input = [c.lower() for c in payload["relay_segment"]]
        expected_srl_values = payload["srl_values"]
        btif_subjects = payload["btif_subjects"]

        inverse_pairs = self.nodes["inverse_pair_node"].run(relay_segment_input)

        relay_segment = self.nodes["relay_alignment_node"].run(inverse_pairs)
        if relay_segment != relay_segment_input:
            raise RelaySegmentError(relay_segment_input)

        srl_values = self.nodes["srl_node"].run(relay_segment)
        if srl_values != expected_srl_values:
            raise SRLGrowthError(self.nodes["srl_node"].growth_factor)

        qpu = self.nodes["temporal_mapping_node"].run(srl_values)
        qpu_with_subjects = []
        for index, row in enumerate(qpu):
            enriched = dict(row)
            enriched["subject"] = btif_subjects[index]
            qpu_with_subjects.append(enriched)

        base_result = {
            "workflow_id": self.definition.get("id", "strict-mode"),
            "name": payload["name"],
            "inverse_pairs": [list(pair) for pair in inverse_pairs],
            "relay_segment": relay_segment,
            "srl_values": srl_values,
            "qpu": qpu_with_subjects,
            "semantic_tags": payload.get("semantic_tags", []),
        }

        node_roles = {
            node_id: details.get("role", "")
            for node_id, details in self.propagation.metadata.get("nodes", {}).items()
        }
        semantic_block = build_strict_mode_semantic_block(
            semantic_intent=self.propagation.metadata.get("semantic_intent", "QPU-Strict-Validation"),
            semantic_tags=base_result["semantic_tags"],
            btif_subjects=self.propagation.metadata.get("btif_subjects", []),
            classification=self.propagation.metadata.get("classification", {}),
            node_roles=node_roles,
        )

        schema_payload = {
            "workflow_id": base_result["workflow_id"],
            "name": base_result["name"],
            "inverse_pairs": base_result["inverse_pairs"],
            "relay_segment": base_result["relay_segment"],
            "srl_values": base_result["srl_values"],
            "qpu": base_result["qpu"],
            "semantic": semantic_block,
        }

        is_valid, reason = validate_strict_mode_qpu(schema_payload)
        if not is_valid:
            raise StrictModeError("STRICT_SCHEMA_INVALID", reason)

        propagated = self.propagation.propagate(base_result["qpu"])

        return {
            **base_result,
            "semantic": semantic_block,
            "strict_mode_enriched": propagated["strict_mode_enriched"],
            "btpe_layer": propagated["btpe_layer"],
            "schema": {
                "schema_id": STRICT_MODE_QPU_SCHEMA.get("schema_id"),
                "schema_version": STRICT_MODE_QPU_SCHEMA.get("schema_version"),
                "valid": True,
            },
        }
