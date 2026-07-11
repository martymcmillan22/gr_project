import unittest
from pathlib import Path
import sys

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from _engine.ai_native import (
    build_ai_context_bundle,
    build_feature_dependency_graph,
    build_semantic_context,
)


class AINativeTests(unittest.TestCase):
    def test_feature_dependency_graph_uses_shared_tags(self) -> None:
        registry = {
            "features": [
                {"slug": "alpha", "semantic_tags": ["intake", "pilot"]},
                {"slug": "beta", "semantic_tags": ["pilot", "routing"]},
            ]
        }

        graph = build_feature_dependency_graph(registry)

        self.assertEqual(graph["nodes"], ["alpha", "beta"])
        self.assertEqual(len(graph["edges"]), 1)
        self.assertEqual(graph["edges"][0]["type"], "shared_semantic_tags")
        self.assertEqual(graph["edges"][0]["shared_tags"], ["pilot"])

    def test_semantic_context_includes_policy_blocks(self) -> None:
        registry = {
            "features": [
                {
                    "slug": "alpha",
                    "mlas_tier": "Semantic Utility",
                    "btif_classification": "IntakeFlow",
                    "semantic_intent": "CaptureAndRoute",
                    "semantic_tags": ["alpha", "intake"],
                }
            ]
        }

        context = build_semantic_context(registry)

        self.assertIn("confidence_thresholds", context)
        self.assertIn("autofix_safety_gates", context)
        self.assertTrue(context["autofix_safety_gates"]["requires_force_unsafe_for_other_types"])

    def test_ai_context_bundle_contains_required_sections(self) -> None:
        registry = {
            "schema_version": "1.0.0",
            "workflow_version": "0.1.0",
            "features": [
                {
                    "name": "Pilot Intake",
                    "slug": "pilot-intake",
                    "mlas_tier": "Semantic Utility",
                    "btif_classification": "IntakeFlow",
                    "semantic_intent": "CaptureAndRoute",
                    "semantic_tags": ["intake", "pilot"],
                    "paths": {
                        "erd": "database_design/mermaid_erds/pilot-intake.erd.mmd",
                        "sequence": "logic_design/mermaid_sequences/pilot-intake.sequence.mmd",
                        "ui_template": "ui_templates/penpot_templates/features/pilot-intake/template.md",
                        "ui_component": "ui_components/penpot_components/features/pilot-intake/component.md",
                    },
                    "status": "scaffolded",
                }
            ],
        }

        bundle = build_ai_context_bundle(registry, WORKFLOW_ROOT)

        self.assertIn("ai_hints", bundle)
        self.assertIn("ai_navigation", bundle)
        self.assertIn("semantic_context", bundle)


if __name__ == "__main__":
    unittest.main()
