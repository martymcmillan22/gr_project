try:
    from workflow.metadata.genre_classifier_metadata import GENRE_CLASSIFIER_METADATA
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from metadata.genre_classifier_metadata import GENRE_CLASSIFIER_METADATA


class GenreClassifierPropagation:
    """
    Attaches Genre Classifier semantic metadata to the enriched QPU
    and produces a BTPE semantic layer for downstream workflows.
    """

    def __init__(self):
        self.metadata = GENRE_CLASSIFIER_METADATA

    def attach_metadata(self, classification_output):
        """
        Attaches genre metadata and classification fields to the QPU.
        """

        enriched = {
            "workflow_id": self.metadata["id"],
            "workflow_name": self.metadata["name"],
            "semantic_intent": self.metadata["semantic_intent"],
            "semantic_tags": self.metadata["semantic_tags"],
            "btif_subjects": self.metadata["btif_subjects"],
            "classification": self.metadata["classification"],
            "nodes": self.metadata["nodes"],
            "genre_taxonomy": self.metadata.get("genre_taxonomy", []),
            "genre": classification_output.get("genre"),
            "confidence": classification_output.get("confidence"),
            "signals_used": classification_output.get("signals_used"),
            "semantic_summary": classification_output.get("semantic_summary"),
        }

        return enriched

    def propagate_to_btpe(self, enriched):
        """
        Converts enriched metadata into a BTPE semantic layer.
        """

        return {
            "btpe_semantic_layer": {
                "intent": enriched["semantic_intent"],
                "tags": enriched["semantic_tags"],
                "subjects": enriched["btif_subjects"],
                "workflow": enriched["workflow_id"],
                "classification": enriched["classification"],
                "nodes": enriched["nodes"],
                "genre": enriched["genre"],
                "confidence": enriched["confidence"],
                "signals_used": enriched["signals_used"],
                "semantic_summary": enriched["semantic_summary"],
            }
        }

    def propagate(self, classification_output):
        """
        Full propagation pipeline:
        1. Attach metadata
        2. Convert to BTPE semantic layer
        """

        enriched = self.attach_metadata(classification_output)
        btpe_layer = self.propagate_to_btpe(enriched)

        return {
            "genre_classifier_enriched": enriched,
            "genre_enriched": enriched,
            "btpe_layer": btpe_layer,
        }
