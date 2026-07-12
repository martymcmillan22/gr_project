import json
from pathlib import Path

try:
    from workflow.engine.genre_classifier_engine import GenreClassifierEngine
    from workflow.metadata.genre_classifier_metadata import GENRE_CLASSIFIER_METADATA
    from workflow.propagation.genre_classifier_propagation import GenreClassifierPropagation
    from workflow.schema.genre_classifier_schema import GENRE_CLASSIFIER_SCHEMA
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from engine.genre_classifier_engine import GenreClassifierEngine
    from metadata.genre_classifier_metadata import GENRE_CLASSIFIER_METADATA
    from propagation.genre_classifier_propagation import GenreClassifierPropagation
    from schema.genre_classifier_schema import GENRE_CLASSIFIER_SCHEMA


class GenreClassifierLoader:
    """
    Autodiscovery loader for the Genre Classifier Workflow.
    Registers the workflow with the global WorkflowRegistry.
    """

    def __init__(self):
        self.workflow_id = "genre-classifier"
        self.definition_path = "workflow/definitions/genre_classifier.workflow.json"

    def _load_definition(self):
        repo_root = Path(__file__).resolve().parents[2]
        absolute_path = (repo_root / self.definition_path).resolve()
        if not absolute_path.exists():
            raise ValueError(f"Workflow definition file not found: {self.definition_path}")
        return json.loads(absolute_path.read_text(encoding="utf-8"))

    def _manifest(self):
        definition = self._load_definition()
        return {
            "id": self.workflow_id,
            "name": definition.get("name", "Genre Classifier Workflow"),
            "version": definition.get("version", "1.0.0"),
            "status": definition.get("status", "active"),
            "definition": self.definition_path,
            "engine": "workflow/engine/genre_classifier_engine.py",
            "schema": "workflow/schema/genre_classifier_schema.py",
            "metadata": "workflow/metadata/genre_classifier_metadata.py",
            "propagation": "workflow/propagation/genre_classifier_propagation.py",
            "documentation": "workflow/docs/genre_classifier.md",
            "nodes": [
                "workflow/nodes/signal_extraction_node.py",
                "workflow/nodes/genre_rule_engine_node.py",
                "workflow/nodes/classification_output_node.py",
            ],
            "semantic": {
                "intent": GENRE_CLASSIFIER_METADATA.get("semantic_intent", "Genre-Classification"),
                "tags": GENRE_CLASSIFIER_METADATA.get("semantic_tags", []),
                "btif_subjects": GENRE_CLASSIFIER_METADATA.get("btif_subjects", []),
                "classification": GENRE_CLASSIFIER_METADATA.get("classification", {}),
            },
        }

    def _index_entry(self, manifest):
        return {
            "id": manifest["id"],
            "name": manifest["name"],
            "version": manifest["version"],
            "status": manifest["status"],
            "definition": manifest["definition"],
            "engine": manifest["engine"],
            "schema": manifest["schema"],
            "metadata": manifest["metadata"],
            "propagation": manifest["propagation"],
            "documentation": manifest["documentation"],
            "nodes": manifest["nodes"],
            "semantic": manifest["semantic"],
        }

    def load(self, workflow_registry):
        # Import-side checks to make loader failures explicit during bootstrap.
        _ = GenreClassifierEngine
        _ = GENRE_CLASSIFIER_SCHEMA
        _ = GENRE_CLASSIFIER_METADATA
        _ = GenreClassifierPropagation

        manifest = self._manifest()
        workflow_registry.register(
            workflow_id=self.workflow_id,
            manifest=manifest,
            index_entry=self._index_entry(manifest),
        )
        return True


def load_genre_classifier(workflow_registry):
    """
    Module-level compatibility hook for WorkflowRegistry bootstrap.
    """

    return GenreClassifierLoader().load(workflow_registry)
