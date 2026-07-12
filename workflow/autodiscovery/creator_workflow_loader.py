try:
    from workflow.index.workflow_index import WORKFLOW_INDEX
    from workflow.manifest.creator_workflow_manifest import CREATOR_WORKFLOW_MANIFEST
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from index.workflow_index import WORKFLOW_INDEX
    from manifest.creator_workflow_manifest import CREATOR_WORKFLOW_MANIFEST


def load_creator_workflow(workflow_registry):
    workflow_registry.register(
        workflow_id=CREATOR_WORKFLOW_MANIFEST["id"],
        manifest=CREATOR_WORKFLOW_MANIFEST,
        index_entry=WORKFLOW_INDEX["creator-workflow"],
    )

    return True
