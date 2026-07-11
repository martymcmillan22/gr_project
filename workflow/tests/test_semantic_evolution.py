import tempfile
import unittest
from pathlib import Path
import sys

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from semantic_evolution import (
    apply_evolution_report_to_registry,
    build_evolution_report,
    load_long_term_governance,
    validate_evolution_approvals,
)


class SemanticEvolutionTests(unittest.TestCase):
    def _registry(self) -> dict:
        return {
            "features": [
                {
                    "name": "Pilot Intake",
                    "slug": "pilot-intake",
                    "mlas_tier": "Semantic Utility",
                    "btif_classification": "IntakeFlow",
                    "semantic_intent": "CaptureAndRoute",
                    "semantic_tags": ["Intake", "pilot"],
                    "paths": {
                        "erd": "database_design/mermaid_erds/pilot-intake.erd.mmd",
                        "sequence": "logic_design/mermaid_sequences/pilot-intake.sequence.mmd",
                        "ui_template": "ui_templates/penpot_templates/features/pilot-intake/template.md",
                        "ui_component": "ui_components/penpot_components/features/pilot-intake/component.md",
                    },
                    "status": "scaffolded",
                    "propagation": {
                        "btif_route": "btif://intakeflow/captureandroute/pilot-intake",
                    },
                }
            ]
        }

    def test_erd_sequence_ui_component_detection(self) -> None:
        registry = self._registry()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "database_design/mermaid_erds").mkdir(parents=True)
            (root / "logic_design/mermaid_sequences").mkdir(parents=True)
            (root / "ui_templates/penpot_templates/features/pilot-intake").mkdir(parents=True)
            (root / "ui_components/penpot_components/features/pilot-intake").mkdir(parents=True)

            (root / "database_design/mermaid_erds/pilot-intake.erd.mmd").write_text("erDiagram\n", encoding="utf-8")
            (root / "logic_design/mermaid_sequences/pilot-intake.sequence.mmd").write_text("sequenceDiagram\n", encoding="utf-8")
            (root / "ui_templates/penpot_templates/features/pilot-intake/template.md").write_text("# Template\n", encoding="utf-8")
            (root / "ui_components/penpot_components/features/pilot-intake/component.md").write_text("# Component\n", encoding="utf-8")

            report = build_evolution_report(registry, root, load_long_term_governance(root / "missing.json"))

        categories = {p["category"] for p in report["features"][0]["proposals"]}
        self.assertIn("erd", categories)
        self.assertIn("sequence", categories)
        self.assertIn("ui_template", categories)
        self.assertIn("component", categories)

    def test_semantic_metadata_and_tag_detection(self) -> None:
        registry = self._registry()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in [
                "database_design/mermaid_erds/pilot-intake.erd.mmd",
                "logic_design/mermaid_sequences/pilot-intake.sequence.mmd",
                "ui_templates/penpot_templates/features/pilot-intake/template.md",
                "ui_components/penpot_components/features/pilot-intake/component.md",
            ]:
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ok", encoding="utf-8")

            report = build_evolution_report(registry, root, load_long_term_governance(root / "missing.json"))

        categories = {p["category"] for p in report["features"][0]["proposals"]}
        self.assertIn("semantic_metadata", categories)
        self.assertIn("tag_ontology", categories)

    def test_governance_enforcement(self) -> None:
        report = {
            "features": [
                {
                    "slug": "pilot-intake",
                    "proposal_count": 1,
                    "proposals": [
                        {
                            "category": "mlas_btif_lineage",
                            "governance_requirements": ["evolution_approval", "semantic_approval"],
                        }
                    ],
                }
            ]
        }

        missing = validate_evolution_approvals(
            report,
            {
                "evolution_approval": True,
                "semantic_approval": False,
                "structural_approval": True,
                "sync_approval": True,
            },
        )
        self.assertEqual(missing, ["semantic_approval"])

    def test_apply_evolution_to_registry(self) -> None:
        registry = self._registry()
        report = {
            "generated_at": "2026-07-11T00:00:00+00:00",
            "features": [
                {
                    "slug": "pilot-intake",
                    "proposal_count": 1,
                    "proposals": [{"category": "erd", "governance_requirements": ["evolution_approval"]}],
                }
            ],
        }

        updated = apply_evolution_report_to_registry(registry, report)
        self.assertIn("evolution", updated["features"][0])
        self.assertEqual(updated["features"][0]["evolution"]["proposal_count"], 1)


if __name__ == "__main__":
    unittest.main()
