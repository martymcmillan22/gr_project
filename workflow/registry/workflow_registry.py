try:
    from workflow.autodiscovery.creator_workflow_loader import load_creator_workflow
    from workflow.autodiscovery.genre_classifier_loader import load_genre_classifier
    from workflow.autodiscovery.strict_mode_loader import load_strict_mode
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from autodiscovery.creator_workflow_loader import load_creator_workflow
    from autodiscovery.genre_classifier_loader import load_genre_classifier
    from autodiscovery.strict_mode_loader import load_strict_mode


class WorkflowRegistry:
    """
    Global workflow registry for the workflow engine.
    Handles registration, lookup, and enumeration of workflow types.
    """

    def __init__(self):
        self._registry = {}
        self._bootstrap()

    def register(self, workflow_id, manifest, index_entry):
        """
        Registers a workflow into the global registry.
        """
        self._registry[workflow_id] = {
            "manifest": manifest,
            "index": index_entry,
        }

    def _bootstrap(self):
        """
        Auto-discovery bootstrap.
        Loads all workflow types that provide auto-discovery hooks.
        """

        # Strict Mode auto-discovery
        load_strict_mode(self)
        load_creator_workflow(self)
        load_genre_classifier(self)

    def list_workflows(self):
        """
        Returns a list of registered workflow IDs.
        """
        return list(self._registry.keys())

    def get(self, workflow_id):
        """
        Returns the manifest + index entry for a workflow.
        """
        return self._registry.get(workflow_id)
