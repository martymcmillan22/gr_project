try:
    from workflow.manifest.creator_workflow_manifest import CREATOR_WORKFLOW_MANIFEST
    from workflow.manifest.strict_mode_manifest import STRICT_MODE_MANIFEST
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from manifest.creator_workflow_manifest import CREATOR_WORKFLOW_MANIFEST
    from manifest.strict_mode_manifest import STRICT_MODE_MANIFEST

WORKFLOW_INDEX = {
    "strict-mode": {
        "id": STRICT_MODE_MANIFEST["id"],
        "name": STRICT_MODE_MANIFEST["name"],
        "version": STRICT_MODE_MANIFEST["version"],
        "status": STRICT_MODE_MANIFEST["status"],
        "definition": STRICT_MODE_MANIFEST["definition"],
        "engine": STRICT_MODE_MANIFEST["engine"],
        "schema": STRICT_MODE_MANIFEST["schema"],
        "metadata": STRICT_MODE_MANIFEST["metadata"],
        "propagation": STRICT_MODE_MANIFEST["propagation"],
        "documentation": STRICT_MODE_MANIFEST["documentation"],
        "nodes": STRICT_MODE_MANIFEST["nodes"],
        "semantic": STRICT_MODE_MANIFEST["semantic"],
    },
    "creator-workflow": {
        "id": CREATOR_WORKFLOW_MANIFEST["id"],
        "name": CREATOR_WORKFLOW_MANIFEST["name"],
        "version": CREATOR_WORKFLOW_MANIFEST["version"],
        "status": CREATOR_WORKFLOW_MANIFEST["status"],
        "definition": CREATOR_WORKFLOW_MANIFEST["definition"],
        "engine": CREATOR_WORKFLOW_MANIFEST["engine"],
        "schema": CREATOR_WORKFLOW_MANIFEST["schema"],
        "metadata": CREATOR_WORKFLOW_MANIFEST["metadata"],
        "propagation": CREATOR_WORKFLOW_MANIFEST["propagation"],
        "documentation": CREATOR_WORKFLOW_MANIFEST["documentation"],
        "nodes": CREATOR_WORKFLOW_MANIFEST["nodes"],
        "semantic": CREATOR_WORKFLOW_MANIFEST["semantic"],
    },
    "genre-classifier": {
        "id": "genre-classifier",
        "name": "Genre Classifier Workflow",
        "version": "1.0.0",
        "status": "active",
        "category": "semantic-classification",
        "description": "Determines narrative genre using structural signals from Strict Mode QPU.",
        "definition": "workflow/definitions/genre_classifier.workflow.json",
        "documentation": "workflow/docs/genre_classifier.md",
        "engine": "workflow/engine/genre_classifier_engine.py",
        "schema": "workflow/schema/genre_classifier_schema.py",
        "metadata": "workflow/metadata/genre_classifier_metadata.py",
        "propagation": "workflow/propagation/genre_classifier_propagation.py",
        "nodes": [
            "workflow/nodes/signal_extraction_node.py",
            "workflow/nodes/genre_rule_engine_node.py",
            "workflow/nodes/classification_output_node.py",
        ],
        "semantic": {
            "intent": "Genre-Classification",
            "tags": [
                "genre",
                "classification",
                "semantic",
                "qpu",
                "structure",
                "analysis",
            ],
            "btif_subjects": [
                "Language",
                "Arts",
                "Science",
                "Math",
            ],
            "classification": {
                "type": "workflow",
                "tier": "semantic",
                "category": "genre-classification",
                "engine": "BTPE",
            },
        },
    }
}
