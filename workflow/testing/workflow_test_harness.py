try:
    from workflow.engine.workflow_engine import WorkflowEngine
    from workflow.debug.workflow_debugger import WorkflowDebugger
    from workflow.introspection.workflow_introspect import WorkflowIntrospect
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from engine.workflow_engine import WorkflowEngine
    from debug.workflow_debugger import WorkflowDebugger
    from introspection.workflow_introspect import WorkflowIntrospect


class WorkflowTestHarness:
    """
    Deterministic test harness for workflow execution.
    Provides regression testing, schema validation checks,
    semantic metadata verification, and engine import tests.
    """

    def __init__(self):
        self.engine = WorkflowEngine()
        self.debugger = WorkflowDebugger()
        self.introspector = WorkflowIntrospect()

    def get_workflow_ids(self):
        return self.engine.list_workflows()

    def _strict_seed_payload(self):
        return {
            "name": "Harness Strict Seed",
            "inverse_pairs": [("red", "green"), ("blue", "yellow")],
            "relay_segment": ["red", "blue", "yellow", "green"],
            "srl_values": [4, 16, 64, 256],
            "tenses": ["past", "present-past", "present-future", "future"],
            "btif_subjects": ["Math", "Language", "Arts", "Science"],
            "semantic_tags": ["strict", "qpu"],
        }

    def _default_payload_for(self, workflow_id):
        if workflow_id == "strict-mode":
            return self._strict_seed_payload()

        strict_output = self.engine.run("strict-mode", self._strict_seed_payload())
        if workflow_id in {"creator-workflow", "genre-classifier"}:
            return strict_output
        return strict_output

    # ---------------------------------------------------------
    # Core Test Runner
    # ---------------------------------------------------------

    def run_test(self, workflow_id, payload):
        """
        Executes a workflow test suite:
        - engine import test
        - registry lookup test
        - execution test
        - schema validation test
        - semantic metadata test
        - propagation test
        Returns a structured test report.
        """

        report = {
            "workflow_id": workflow_id,
            "payload": payload,
            "engine_import": None,
            "registry_lookup": None,
            "execution": None,
            "schema_valid": None,
            "semantic_metadata": None,
            "propagation_class": None,
            "propagation_valid": None,
            "introspection": None,
            "passed": False
        }

        # -----------------------------------------------------
        # Registry lookup test
        # -----------------------------------------------------
        entry = self.engine.get_workflow(workflow_id)
        report["registry_lookup"] = entry is not None

        if not entry:
            return report

        manifest = entry["manifest"]

        # -----------------------------------------------------
        # Engine import test
        # -----------------------------------------------------
        try:
            self.engine._import_engine(manifest["engine"])
            report["engine_import"] = True
        except Exception:
            report["engine_import"] = False
            return report

        # -----------------------------------------------------
        # Execution test (via debugger)
        # -----------------------------------------------------
        diagnostics = self.debugger.debug(workflow_id, payload)
        report["execution"] = diagnostics["output"]

        # -----------------------------------------------------
        # Schema validation test
        # -----------------------------------------------------
        report["schema_valid"] = diagnostics["schema_valid"]

        # -----------------------------------------------------
        # Semantic metadata test
        # -----------------------------------------------------
        report["semantic_metadata"] = diagnostics["semantic_metadata"]

        # -----------------------------------------------------
        # Propagation class test
        # -----------------------------------------------------
        report["propagation_class"] = diagnostics["propagation"]

        introspection = self.introspector.inspect(workflow_id)
        report["introspection"] = introspection

        output = diagnostics.get("output")
        propagation_valid = False
        propagation_class = diagnostics.get("propagation")
        if propagation_class is not None and output is not None:
            try:
                propagated = propagation_class().propagate(output)
                propagation_valid = isinstance(propagated, dict) and "btpe_layer" in propagated
            except Exception:
                propagation_valid = False
        report["propagation_valid"] = propagation_valid

        # -----------------------------------------------------
        # Final pass/fail determination
        # -----------------------------------------------------
        report["passed"] = (
            report["engine_import"] and
            report["registry_lookup"] and
            report["schema_valid"] and
            report["semantic_metadata"] is not None and
            report["propagation_class"] is not None and
            report["propagation_valid"] and
            isinstance(report["introspection"], dict) and
            "error" not in report["introspection"]
        )

        return report

    # ---------------------------------------------------------
    # Batch Test Runner
    # ---------------------------------------------------------

    def run_batch(self, workflow_id, test_cases):
        """
        Runs multiple test cases for a workflow.
        Returns a list of test reports.
        """

        results = []
        for payload in test_cases:
            results.append(self.run_test(workflow_id, payload))
        return results

    def run_workflow_suite(self, workflow_ids=None):
        targets = workflow_ids if workflow_ids is not None else self.get_workflow_ids()
        reports = []
        for workflow_id in targets:
            payload = self._default_payload_for(workflow_id)
            reports.append(self.run_test(workflow_id, payload))
        return reports
