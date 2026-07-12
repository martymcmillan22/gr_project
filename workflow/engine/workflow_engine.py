import json
from pathlib import Path

try:
    from workflow.engine.bootstrap import WorkflowEngineBootstrap
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from engine.bootstrap import WorkflowEngineBootstrap


class WorkflowEngine:
    """
    Main workflow engine.
    Provides execution, lookup, and semantic integration for all workflows.
    """

    def __init__(self):
        # Initialize bootstrap (loads registry + autodiscovery)
        self.bootstrap = WorkflowEngineBootstrap()
        self.registry = self.bootstrap.get_registry()

    # ---------------------------------------------------------
    # Workflow Lookup
    # ---------------------------------------------------------

    def list_workflows(self):
        """
        Returns a list of all registered workflow IDs.
        """
        return self.registry.list_workflows()

    def get_workflow(self, workflow_id):
        """
        Returns manifest + index entry for a workflow.
        """
        return self.registry.get(workflow_id)

    # ---------------------------------------------------------
    # Workflow Execution
    # ---------------------------------------------------------

    def run(self, workflow_id, payload):
        """
        Executes a workflow by ID using its engine module.
        """

        entry = self.get_workflow(workflow_id)
        if not entry:
            raise ValueError(f"Workflow '{workflow_id}' is not registered.")

        manifest = entry["manifest"]
        engine_path = manifest["engine"]
        definition_path = manifest["definition"]

        # Dynamic import of workflow engine module
        module = self._import_engine(engine_path)

        engine_class = getattr(module, manifest["id"].replace("-", "_") + "_engine", None)
        if engine_class is None:
            # Fallback: look for StrictModeEngine or similar
            engine_class = self._fallback_engine_class(module)

        definition = self._load_definition(definition_path)
        engine = engine_class(definition)
        return engine.run(payload)

    # ---------------------------------------------------------
    # Engine Import Helpers
    # ---------------------------------------------------------

    def _import_engine(self, engine_path):
        """
        Imports the engine module dynamically.
        Supports both script-mode and package-mode imports.
        """
        import_path = engine_path.replace("/", ".").replace(".py", "")
        try:
            return __import__(import_path, fromlist=["*"])
        except ModuleNotFoundError:
            if import_path.startswith("workflow."):
                return __import__(import_path.replace("workflow.", "", 1), fromlist=["*"])
            raise

    def _fallback_engine_class(self, module):
        """
        Fallback lookup for workflow engine classes.
        """
        for attr in dir(module):
            if attr.endswith("Engine"):
                return getattr(module, attr)
        raise ValueError("No workflow engine class found in module.")

    def _load_definition(self, definition_path):
        repo_root = Path(__file__).resolve().parents[2]
        absolute_path = (repo_root / definition_path).resolve()
        if not absolute_path.exists():
            raise ValueError(f"Workflow definition file not found: {definition_path}")
        return json.loads(absolute_path.read_text(encoding="utf-8"))
