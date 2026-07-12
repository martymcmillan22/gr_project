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


class WorkflowDebugger:
    """
    Developer-facing debugging utility for workflow execution.
    Provides node-level tracing, schema validation checks,
    semantic metadata inspection, and propagation diagnostics.
    """

    def __init__(self):
        self.engine = WorkflowEngine()

    def _normalize_payload(self, payload):
        """
        Ensure payload satisfies strict-mode runtime contract.
        """
        normalized = dict(payload)
        colors = [color.lower() for color in normalized.get("colors", [])]
        relay_segment = normalized.get("relay_segment")

        if relay_segment is None and colors:
            relay_segment = colors

        if relay_segment is not None:
            normalized["relay_segment"] = [color.lower() for color in relay_segment]

        if colors:
            normalized["colors"] = colors

        normalized.setdefault("name", "strict-mode-debug")
        normalized.setdefault("srl_values", [4, 16, 64, 256])
        normalized.setdefault(
            "btif_subjects",
            ["Math", "Language", "Arts", "Science"],
        )
        normalized.setdefault("semantic_tags", ["debug"])

        return normalized

    # ---------------------------------------------------------
    # Core Debugging Entry Point
    # ---------------------------------------------------------

    def debug(self, workflow_id, payload):
        """
        Executes a workflow with full debugging output.
        Returns a structured diagnostic dictionary.
        """

        normalized_payload = self._normalize_payload(payload)

        diagnostics = {
            "workflow_id": workflow_id,
            "input_payload": normalized_payload,
            "steps": [],
            "output": None,
            "schema_valid": None,
            "semantic_metadata": None,
            "propagation": None,
        }

        # Step 1: Lookup workflow
        entry = self.engine.get_workflow(workflow_id)
        diagnostics["steps"].append("Loaded workflow registry entry.")

        if not entry:
            diagnostics["steps"].append("Workflow not found.")
            return diagnostics

        manifest = entry["manifest"]
        diagnostics["steps"].append("Loaded workflow manifest.")

        # Step 2: Import engine module
        engine_module = self.engine._import_engine(manifest["engine"])
        diagnostics["steps"].append("Imported workflow engine module.")

        # Step 3: Resolve engine class
        engine_class = getattr(
            engine_module,
            manifest["id"].replace("-", "_") + "_engine",
            None,
        )

        if engine_class is None:
            engine_class = self.engine._fallback_engine_class(engine_module)
            diagnostics["steps"].append("Resolved fallback engine class.")
        else:
            diagnostics["steps"].append("Resolved primary engine class.")

        # Step 4: Instantiate engine
        definition = self.engine._load_definition(manifest["definition"])
        engine_instance = engine_class(definition)
        diagnostics["steps"].append("Instantiated workflow engine.")

        # Step 5: Execute workflow
        output = engine_instance.run(normalized_payload)
        diagnostics["output"] = output
        diagnostics["steps"].append("Executed workflow engine.")

        # Step 6: Schema validation
        schema_module = self.engine._import_engine(manifest["schema"])
        schema_prefix = _workflow_symbol_prefix(workflow_id)
        validate_fn = _resolve_attribute(
            schema_module,
            [
                f"validate_{schema_prefix.lower()}_qpu",
                f"validate_{schema_prefix.lower()}_output",
                "validate_genre_classifier_output",
                "validate",
                "validate_strict_mode_qpu",
            ],
        )

        if callable(validate_fn):
            validation_result = validate_fn(output)
            if isinstance(validation_result, tuple):
                diagnostics["schema_valid"] = bool(validation_result[0])
            else:
                diagnostics["schema_valid"] = bool(validation_result)
        else:
            diagnostics["schema_valid"] = None
        diagnostics["steps"].append("Performed schema validation.")

        # Step 7: Semantic metadata
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

        diagnostics["semantic_metadata"] = metadata
        diagnostics["steps"].append("Loaded semantic metadata.")

        # Step 8: Propagation diagnostics
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

        diagnostics["propagation"] = propagation_class
        diagnostics["steps"].append("Loaded propagation class.")

        return diagnostics
