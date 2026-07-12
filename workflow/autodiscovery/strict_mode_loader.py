try:
    from workflow.index.workflow_index import WORKFLOW_INDEX
    from workflow.manifest.strict_mode_manifest import STRICT_MODE_MANIFEST
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from index.workflow_index import WORKFLOW_INDEX
    from manifest.strict_mode_manifest import STRICT_MODE_MANIFEST


def load_strict_mode(workflow_registry):
    """
    Auto-discovery hook for Strict Mode.
    Registers Strict Mode into the workflow engine's registry
    during bootstrap initialization.
    """

    workflow_registry.register(
        workflow_id=STRICT_MODE_MANIFEST["id"],
        manifest=STRICT_MODE_MANIFEST,
        index_entry=WORKFLOW_INDEX["strict-mode"],
    )

    return True
