try:
    from workflow.semantic.strict_mode_metadata import STRICT_MODE_METADATA
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from semantic.strict_mode_metadata import STRICT_MODE_METADATA


class StrictModePropagation:
    """
    Defines how Strict Mode semantic metadata is attached to QPU outputs
    and propagated into BTPE semantic layers.
    """

    def __init__(self):
        self.metadata = STRICT_MODE_METADATA

    def attach_metadata(self, qpu_output):
        """
        Attaches Strict Mode semantic metadata to the final QPU object.
        """

        enriched = {
            "workflow_id": self.metadata["id"],
            "workflow_name": self.metadata["name"],
            "semantic_intent": self.metadata["semantic_intent"],
            "semantic_tags": self.metadata["semantic_tags"],
            "btif_subjects": self.metadata["btif_subjects"],
            "classification": self.metadata["classification"],
            "nodes": self.metadata["nodes"],
            "qpu": qpu_output,
        }

        return enriched

    def propagate_to_btpe(self, enriched_qpu):
        """
        Converts enriched QPU metadata into BTPE semantic layers.
        """

        return {
            "btpe_semantic_layer": {
                "intent": enriched_qpu["semantic_intent"],
                "tags": enriched_qpu["semantic_tags"],
                "subjects": enriched_qpu["btif_subjects"],
                "workflow": enriched_qpu["workflow_id"],
                "classification": enriched_qpu["classification"],
                "nodes": enriched_qpu["nodes"],
                "qpu": enriched_qpu["qpu"],
            }
        }

    def propagate(self, qpu_output):
        """
        Full propagation pipeline:
        1. Attach Strict Mode metadata
        2. Convert to BTPE semantic layer
        """

        enriched = self.attach_metadata(qpu_output)
        btpe_layer = self.propagate_to_btpe(enriched)

        return {
            "strict_mode_enriched": enriched,
            "btpe_layer": btpe_layer,
        }
