try:
    from workflow.engine.workflow_engine import WorkflowEngine
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from engine.workflow_engine import WorkflowEngine


def _workflow_symbol_prefix(workflow_id):
    return workflow_id.replace("-", "_").upper()


def _workflow_camel_name(workflow_id, suffix=""):
    parts = [part for part in workflow_id.replace("-", "_").split("_") if part]
    camel = "".join(part[:1].upper() + part[1:] for part in parts)
    return f"{camel}{suffix}"


def _resolve_attribute(module, candidates):
    for candidate in candidates:
        if hasattr(module, candidate):
            return getattr(module, candidate)
    return None


class WorkflowIntrospect:
    """
    Programmatic introspection API for workflow structure, metadata,
    schema, nodes, engine modules, and propagation rules.
    """

    def __init__(self):
        self.engine = WorkflowEngine()

    # ---------------------------------------------------------
    # Core Introspection Entry Point
    # ---------------------------------------------------------

    def inspect(self, workflow_id):
        """
        Returns a structured introspection dictionary containing:
        - manifest
        - index entry
        - nodes
        - schema object
        - metadata object
        - propagation class
        - engine module
        """

        entry = self.engine.get_workflow(workflow_id)
        if not entry:
            return {
                "workflow_id": workflow_id,
                "error": "Workflow not found."
            }

        manifest = entry["manifest"]
        index = entry["index"]

        # -----------------------------------------------------
        # Load engine module
        # -----------------------------------------------------
        engine_module = self.engine._import_engine(manifest["engine"])

        # -----------------------------------------------------
        # Load schema
        # -----------------------------------------------------
        schema_module = self.engine._import_engine(manifest["schema"])
        schema_prefix = _workflow_symbol_prefix(workflow_id)
        schema = _resolve_attribute(
            schema_module,
            [
                f"{schema_prefix}_QPU_SCHEMA",
                f"{schema_prefix}_SCHEMA",
                "STRICT_MODE_QPU_SCHEMA",
                "CREATOR_WORKFLOW_QPU_SCHEMA",
                "GENRE_CLASSIFIER_SCHEMA",
            ],
        )

        # -----------------------------------------------------
        # Load metadata
        # -----------------------------------------------------
        metadata_module = self.engine._import_engine(manifest["metadata"])
        metadata = _resolve_attribute(
            metadata_module,
            [
                f"{schema_prefix}_METADATA",
                "STRICT_MODE_METADATA",
                "CREATOR_WORKFLOW_METADATA",
                "GENRE_CLASSIFIER_METADATA",
            ],
        )

        # -----------------------------------------------------
        # Load propagation rules
        # -----------------------------------------------------
        propagation_module = self.engine._import_engine(manifest["propagation"])
        propagation_class = _resolve_attribute(
            propagation_module,
            [
                _workflow_camel_name(workflow_id, "Propagation"),
                "StrictModePropagation",
                "CreatorWorkflowPropagation",
                "GenreClassifierPropagation",
            ],
        )

        # -----------------------------------------------------
        # Build introspection dictionary
        # -----------------------------------------------------
        return {
            "workflow_id": workflow_id,
            "manifest": manifest,
            "index": index,
            "nodes": manifest.get("nodes", []),
            "schema": schema,
            "metadata": metadata,
            "propagation": propagation_class,
            "engine_module": engine_module
        }
