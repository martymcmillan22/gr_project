try:
    from workflow.registry.workflow_registry import WorkflowRegistry
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from registry.workflow_registry import WorkflowRegistry


class WorkflowEngineBootstrap:
    """
    Engine bootstrap layer.
    Initializes the global workflow registry and exposes it to the engine.
    """

    def __init__(self):
        self.registry = WorkflowRegistry()

    def get_registry(self):
        """
        Returns the initialized workflow registry.
        """
        return self.registry

    def list_workflows(self):
        """
        Convenience wrapper for listing all registered workflows.
        """
        return self.registry.list_workflows()

    def get_workflow(self, workflow_id):
        """
        Returns manifest + index entry for a workflow.
        """
        return self.registry.get(workflow_id)
