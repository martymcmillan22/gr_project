import unittest
from pathlib import Path
import sys

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from feature_expansion import (
    apply_expansion_report_to_registry,
    build_expansion_report,
    load_expansion_governance,
    validate_expansion_approvals,
)


class FeatureExpansionTests(unittest.TestCase):
    def _registry(self) -> dict:
        return {
            "features": [
                {
                    "name": "Pilot Intake",
                    "slug": "pilot-intake",
                    "mlas_tier": "Semantic Utility",
                    "btif_classification": "IntakeFlow",
                    "semantic_intent": "CaptureAndRoute",
                    "semantic_tags": ["intake", "pilot", "routing"],
                    "paths": {
                        "erd": "database_design/mermaid_erds/pilot-intake.erd.mmd",
                        "sequence": "logic_design/mermaid_sequences/pilot-intake.sequence.mmd",
                        "ui_template": "ui_templates/penpot_templates/features/pilot-intake/template.md",
                        "ui_component": "ui_components/penpot_components/features/pilot-intake/component.md",
                    },
                    "status": "scaffolded",
                }
            ]
        }

    def test_missing_coverage_detection(self) -> None:
        report = build_expansion_report(self._registry(), load_expansion_governance(WORKFLOW_ROOT / "missing.json"))
        categories = {row["category"] for row in report["proposals"]}
        self.assertIn("new_feature", categories)

    def test_semantic_gap_detection(self) -> None:
        report = build_expansion_report(self._registry(), load_expansion_governance(WORKFLOW_ROOT / "missing.json"))
        categories = {row["category"] for row in report["proposals"]}
        self.assertIn("new_semantic_intent", categories)

    def test_multi_feature_bundle_proposal(self) -> None:
        report = build_expansion_report(self._registry(), load_expansion_governance(WORKFLOW_ROOT / "missing.json"))
        categories = {row["category"] for row in report["proposals"]}
        self.assertIn("multi_feature_bundle", categories)

    def test_cross_feature_integration_proposal(self) -> None:
        report = build_expansion_report(self._registry(), load_expansion_governance(WORKFLOW_ROOT / "missing.json"))
        categories = {row["category"] for row in report["proposals"]}
        self.assertIn("cross_feature_integration", categories)

    def test_mlas_btif_expansion_detection(self) -> None:
        report = build_expansion_report(self._registry(), load_expansion_governance(WORKFLOW_ROOT / "missing.json"))
        categories = {row["category"] for row in report["proposals"]}
        self.assertIn("new_mlas_btif_pattern", categories)

    def test_tag_ontology_expansion_detection(self) -> None:
        report = build_expansion_report(self._registry(), load_expansion_governance(WORKFLOW_ROOT / "missing.json"))
        categories = {row["category"] for row in report["proposals"]}
        self.assertIn("new_tag_ontology_entry", categories)

    def test_governance_enforcement(self) -> None:
        report = build_expansion_report(self._registry(), load_expansion_governance(WORKFLOW_ROOT / "missing.json"))
        missing = validate_expansion_approvals(
            report,
            {
                "expansion_approval": True,
                "semantic_approval": False,
                "structural_approval": False,
                "sync_approval": False,
            },
        )
        self.assertTrue(len(missing) >= 1)

    def test_apply_path_behavior(self) -> None:
        registry = self._registry()
        report = build_expansion_report(registry, load_expansion_governance(WORKFLOW_ROOT / "missing.json"))
        updated = apply_expansion_report_to_registry(registry, report)
        self.assertGreater(len(updated["features"]), 1)


if __name__ == "__main__":
    unittest.main()
