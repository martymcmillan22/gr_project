try:
    from workflow.testing.workflow_test_harness import WorkflowTestHarness
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from testing.workflow_test_harness import WorkflowTestHarness


class WorkflowValidationReport:
    """
    Generates human-readable validation reports for workflow test results.
    Consumes WorkflowTestHarness and produces structured diagnostic output.
    """

    def __init__(self):
        self.harness = WorkflowTestHarness()

    # ---------------------------------------------------------
    # Single Report Generator
    # ---------------------------------------------------------

    def generate_report(self, workflow_id, payload):
        """
        Runs a workflow test and returns a formatted validation report string.
        """

        result = self.harness.run_test(workflow_id, payload)

        lines = []
        lines.append("=== Workflow Validation Report ===")
        lines.append(f"Workflow ID: {workflow_id}")
        lines.append("")

        # Registry
        lines.append("Registry Lookup:")
        lines.append(f"  - Found: {result['registry_lookup']}")
        lines.append("")

        # Engine import
        lines.append("Engine Import:")
        lines.append(f"  - Successful: {result['engine_import']}")
        lines.append("")

        # Execution
        lines.append("Execution Output:")
        lines.append(f"  {result['execution']}")
        lines.append("")

        # Schema validation
        lines.append("Schema Validation:")
        lines.append(f"  - Valid: {result['schema_valid']}")
        lines.append("")

        # Semantic metadata
        lines.append("Semantic Metadata:")
        lines.append(f"  {result['semantic_metadata']}")
        lines.append("")

        # Propagation class
        lines.append("Propagation Class:")
        lines.append(f"  {result['propagation_class']}")
        lines.append("")

        # Final status
        lines.append("Final Status:")
        lines.append(f"  - Passed: {result['passed']}")
        lines.append("")

        return "\n".join(lines)

    # ---------------------------------------------------------
    # Batch Report Generator
    # ---------------------------------------------------------

    def generate_batch_report(self, workflow_id, test_cases):
        """
        Runs multiple test cases and returns a combined validation report.
        """

        lines = []
        lines.append("=== Workflow Batch Validation Report ===")
        lines.append(f"Workflow ID: {workflow_id}")
        lines.append("")

        for i, payload in enumerate(test_cases):
            lines.append(f"--- Test Case {i + 1} ---")
            report = self.generate_report(workflow_id, payload)
            lines.append(report)
            lines.append("")

        return "\n".join(lines)

    def generate_workflow_summary(self, workflow_ids=None):
        results = self.harness.run_workflow_suite(workflow_ids)

        lines = []
        lines.append("=== Workflow Validation Summary ===")
        lines.append("")

        for result in results:
            workflow_id = result["workflow_id"]
            status = "OK" if result.get("passed") else "FAILED"
            lines.append(f"Workflow: {workflow_id}")
            lines.append(f"  - Status: {status}")
            lines.append(f"  - Engine: {'OK' if result.get('engine_import') else 'FAILED'}")
            lines.append(f"  - Schema: {'OK' if result.get('schema_valid') else 'FAILED'}")
            lines.append(f"  - Metadata: {'OK' if result.get('semantic_metadata') is not None else 'FAILED'}")
            lines.append(f"  - Propagation: {'OK' if result.get('propagation_valid') else 'FAILED'}")

            introspection = result.get("introspection", {})
            introspect_ok = isinstance(introspection, dict) and "error" not in introspection
            lines.append(f"  - Introspection: {'OK' if introspect_ok else 'FAILED'}")

            registry_ok = bool(result.get("registry_lookup"))
            lines.append(f"  - Registry/Index: {'OK' if registry_ok else 'FAILED'}")

            cli_ok = result.get("engine_import") and result.get("schema_valid")
            lines.append(f"  - CLI Contract: {'OK' if cli_ok else 'FAILED'}")
            lines.append("")

        return "\n".join(lines)
