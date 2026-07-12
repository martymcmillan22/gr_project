try:
    from workflow.semantic.creator_workflow_metadata import CREATOR_WORKFLOW_METADATA
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from semantic.creator_workflow_metadata import CREATOR_WORKFLOW_METADATA


class CreatorWorkflowPropagation:
    def __init__(self):
        self.metadata = CREATOR_WORKFLOW_METADATA

    def attach_metadata(self, narrative_output):
        return {
            "workflow_id": self.metadata["id"],
            "workflow_name": self.metadata["name"],
            "semantic_intent": self.metadata["semantic_intent"],
            "semantic_tags": self.metadata["semantic_tags"],
            "btif_subjects": self.metadata["btif_subjects"],
            "classification": self.metadata["classification"],
            "nodes": self.metadata["nodes"],
            "narrative_output": narrative_output,
        }

    def propagate_to_btpe(self, enriched_creator):
        return {
            "btpe_semantic_layer": {
                "intent": enriched_creator["semantic_intent"],
                "tags": enriched_creator["semantic_tags"],
                "subjects": enriched_creator["btif_subjects"],
                "workflow": enriched_creator["workflow_id"],
                "classification": enriched_creator["classification"],
                "nodes": enriched_creator["nodes"],
                "narrative_output": enriched_creator["narrative_output"],
            }
        }

    def propagate(self, narrative_output):
        enriched = self.attach_metadata(narrative_output)
        btpe_layer = self.propagate_to_btpe(enriched)
        return {
            "creator_enriched": enriched,
            "btpe_layer": btpe_layer,
        }
