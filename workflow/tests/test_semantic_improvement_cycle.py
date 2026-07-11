import tempfile
import unittest
from pathlib import Path
import sys

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from semantic_improvement_cycle import (
    apply_improvement_cycle_plan,
    build_improvement_cycle_plan,
    load_cycle_governance,
    validate_cycle_approvals,
)


class SemanticImprovementCycleTests(unittest.TestCase):
    def _registry(self) -> dict:
        return {
            "features": [
                {
                    "name": "Pilot Intake",
                    "slug": "pilot-intake",
                    "mlas_tier": "Semantic Utility",
                    "btif_classification": "IntakeFlow",
                    "semantic_intent": "capture_and_route",
                    "semantic_tags": ["Intake", "pilot"],
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

        (root / "database_design/mermaid_erds/pilot-intake.erd.mmd").write_text("erDiagram\n", encoding="utf-8")
        (root / "logic_design/mermaid_sequences/pilot-intake.sequence.mmd").write_text("sequenceDiagram\n", encoding="utf-8")
        (root / "ui_templates/penpot_templates/features/pilot-intake/template.md").write_text("# Template\n", encoding="utf-8")
        (root / "ui_components/penpot_components/features/pilot-intake/component.md").write_text("# Component\n", encoding="utf-8")

    def test_per_feature_orchestration(self) -> None:
        registry = self._registry()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_artifacts(root)
            plan = build_improvement_cycle_plan(
                registry,
                root,
                load_cycle_governance(root / "missing.json"),
                feature_slug="pilot-intake",
            )

        self.assertEqual(plan["target"], "pilot-intake")
        self.assertEqual(plan["engine_order"], ["evolution", "expansion", "refactor"])

    def test_registry_wide_orchestration(self) -> None:
        registry = self._registry()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_artifacts(root)
            plan = build_improvement_cycle_plan(registry, root, load_cycle_governance(root / "missing.json"))

        self.assertIn("reports", plan)
        self.assertIn("feature_summaries", plan)
        self.assertGreaterEqual(plan["proposal_count"], 0)

    def test_ordering_evolution_expansion_refactor(self) -> None:
        registry = self._registry()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_artifacts(root)
            plan = build_improvement_cycle_plan(registry, root, load_cycle_governance(root / "missing.json"))
        self.assertEqual(plan["engine_order"], ["evolution", "expansion", "refactor"])

    def test_governance_enforcement(self) -> None:
        plan = {
            "proposal_count": 1,
            "reports": {
                "evolution": {"proposal_count": 1},
                "expansion": {"proposal_count": 1},
                "refactor": {"proposal_count": 1},
            },
            "aggregated_proposals": [
                {
                    "governance_requirements": [
                        "evolution_approval",
                        "expansion_approval",
                        "refactor_approval",
                        "semantic_approval",
                        "structural_approval",
                        "sync_approval",
                    ]
                }
            ],
        }
        policy = {
            "gates": {
                "cycle_apply_requires_engine_approvals": True,
                "cycle_apply_requires_cross_domain_approvals": True,
            }
        }
        missing = validate_cycle_approvals(
            plan,
            {
                "evolution_approval": True,
                "expansion_approval": False,
                "refactor_approval": False,
                "semantic_approval": False,
                "structural_approval": False,
                "sync_approval": False,
            },
            policy,
        )
        self.assertIn("expansion_approval", missing)
        self.assertIn("refactor_approval", missing)

    def test_preview_vs_apply_behavior(self) -> None:
        registry = self._registry()
        plan = {
            "generated_at": "2026-07-11T00:00:00+00:00",
            "engine_order": ["evolution", "expansion", "refactor"],
            "proposal_count": 1,
            "reports": {
                "evolution": {"generated_at": "2026-07-11T00:00:00+00:00", "features": []},
                "expansion": {"generated_at": "2026-07-11T00:00:00+00:00", "proposals": []},
                "refactor": {"generated_at": "2026-07-11T00:00:00+00:00", "features": []},
            },
            "feature_summaries": [],
            "aggregated_proposals": [],
        }

        # preview: no mutation applied
        self.assertNotIn("improvement_cycle", registry)

        # apply: mutation block should be added
        updated = apply_improvement_cycle_plan(registry, plan)
        self.assertIn("improvement_cycle", updated)


if __name__ == "__main__":
    unittest.main()
