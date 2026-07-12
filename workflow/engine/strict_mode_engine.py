try:
    from workflow.errors.strict_mode_errors import RelaySegmentError, SRLGrowthError
    from workflow.nodes.inverse_pair_node import InversePairNode
    from workflow.nodes.relay_alignment_node import RelayAlignmentNode
    from workflow.nodes.srl_node import SRLNode
    from workflow.nodes.temporal_mapping_node import TemporalMappingNode
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from errors.strict_mode_errors import RelaySegmentError, SRLGrowthError
    from nodes.inverse_pair_node import InversePairNode
    from nodes.relay_alignment_node import RelayAlignmentNode
    from nodes.srl_node import SRLNode
    from nodes.temporal_mapping_node import TemporalMappingNode


class StrictModeEngine:
    """
    Executes the Strict Mode workflow as defined in strict_mode.workflow.json.
    This module provides deterministic node sequencing and structured error handling.
    """

    def __init__(self, definition):
        self.definition = definition
        self.nodes = self._load_nodes(definition)

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

        return {
            "name": payload["name"],
            "inverse_pairs": [list(pair) for pair in inverse_pairs],
            "relay_segment": relay_segment,
            "srl_values": srl_values,
            "qpu": qpu_with_subjects,
            "semantic_tags": payload.get("semantic_tags", []),
        }
