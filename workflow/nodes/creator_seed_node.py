try:
    from workflow.errors.creator_workflow_errors import CreatorInputError
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from errors.creator_workflow_errors import CreatorInputError


class CreatorSeedNode:
    def __init__(self, config):
        self.config = config

    def run(self, payload):
        qpu = payload.get("qpu", [])
        semantic = payload.get("semantic", {})

        if len(qpu) != 4:
            raise CreatorInputError("validated QPU must contain four records")
        if not semantic:
            raise CreatorInputError("semantic metadata is required")

        return {
            "workflow_id": payload.get("workflow_id", "creator-workflow"),
            "source_workflow_id": payload.get("workflow_id", "strict-mode"),
            "source_name": payload.get("name", "Validated QPU"),
            "source_qpu": qpu,
            "semantic": semantic,
            "semantic_tags": payload.get("semantic_tags", []),
            "btif_subjects": payload.get("btif_subjects", []),
            "narrative_mode": self.config.get("narrative_mode", "creator"),
        }
