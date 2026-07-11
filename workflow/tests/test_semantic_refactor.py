import tempfile
import unittest
from pathlib import Path
import sys

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from semantic_refactor import (
    apply_refactor_report_to_registry,
    build_refactor_report,
    load_refactor_governance,
    validate_refactor_approvals,
)


class SemanticRefactorTests(unittest.TestCase):
    def _registry(self) -> dict:
        return {
            "features": [
                {
                    "name": "Pilot Intake",
                    "slug": "pilot-intake",
                    "mlas_tier": "Semantic Utility",
                    "btif_classification": "IntakeFlow",
                    "semantic_intent": "capture_and_route",
                    "semantic_tags": ["Intake", "Pilot", "routing"],
                    "paths": {
                        "erd": "database_design/mermaid_erds/pilot-intake.erd.mmd",
                        "sequence": "logic_design/mermaid_sequences/pilot-intake.sequence.mmd",
                        "ui_template": "ui_templates/penpot_templates/features/pilot-intake/template.md",
                        "ui_component": "ui_components/penpot_components/features/pilot-intake/component.md",
                    },
                    "status": "scaffolded",
                    "propagation": {
                        "btif_route": "btif://wrong/route/pilot-intake",
                    },
                }
            ]
        }

    def _write_artifacts(self, root: Path) -> None:
        (root / "database_design/mermaid_erds").mkdir(parents=True, exist_ok=True)
        (root / "logic_design/mermaid_sequences").mkdir(parents=True, exist_ok=True)
        (root / "ui_templates/penpot_templates/features/pilot-intake").mkdir(parents=True, exist_ok=True)
        (root / "ui_components/penpot_components/features/pilot-intake").mkdir(parents=True, exist_ok=True)

        (root / "database_design/mermaid_erds/pilot-intake.erd.mmd").write_text(
            "\n".join(
                [
                    "erDiagram",
                    "    FEATURE_ENTITY {",
                    "      string id PK",
                    "    }",
                    "    FEATURE_ENTITY {",
                    "      string name",
                    "    }",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        (root / "logic_design/mermaid_sequences/pilot-intake.sequence.mmd").write_text(
            "\n".join(
                [
                    "sequenceDiagram",
                    "    participant UI",
                    "    participant API",
                    "    UI->>API: Request",
                    "    UI->>API: Request",
                    "    Note over UI: TODO remove dead path",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        (root / "ui_templates/penpot_templates/features/pilot-intake/template.md").write_text(
            "# UI Template\n",
            encoding="utf-8",
        )

        (root / "ui_components/penpot_components/features/pilot-intake/component.md").write_text(
            "# UI Component\n",
            encoding="utf-8",
        )

    def test_refactor_detection_all_categories(self) -> None:
        registry = self._registry()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_artifacts(root)
            report = build_refactor_report(registry, root, load_refactor_governance(root / "missing.json"))

        categories = {p["category"] for p in report["features"][0]["proposals"]}
        self.assertIn("erd", categories)
        self.assertIn("sequence", categories)
        self.assertIn("ui_template", categories)
        self.assertIn("component", categories)
        self.assertIn("semantic_metadata", categories)
        self.assertIn("mlas_btif_lineage", categories)
        self.assertIn("tag_ontology", categories)

    def test_governance_enforcement(self) -> None:
        report = {
            "features": [
                {
                    "slug": "pilot-intake",
                    "proposal_count": 1,
                    "proposals": [
                        {
                            "category": "semantic_metadata",
                            "governance_requirements": ["refactor_approval", "semantic_approval"],
                        }
                    ],
                }
            ]
        }
        missing = validate_refactor_approvals(
            report,
            {
                "refactor_approval": True,
                "semantic_approval": False,
                "structural_approval": True,
                "sync_approval": True,
            },
        )
        self.assertEqual(missing, ["semantic_approval"])

    def test_apply_path_behavior(self) -> None:
        registry = self._registry()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_artifacts(root)
            report = build_refactor_report(registry, root, load_refactor_governance(root / "missing.json"))

        updated = apply_refactor_report_to_registry(registry, report)
        feature = updated["features"][0]
        self.assertIn("refactor", feature)
        self.assertEqual(feature["semantic_tags"], ["intake", "pilot", "routing"])
        self.assertEqual(feature["feature_lineage"], "workflow/pilot-intake")
        self.assertEqual(feature["propagation"]["btif_route"], "btif://intakeflow/captureandroute/pilot-intake")


if __name__ == "__main__":
    unittest.main()
