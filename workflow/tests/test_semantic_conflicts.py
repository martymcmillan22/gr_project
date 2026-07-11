import tempfile
import unittest
from pathlib import Path
import sys

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from _engine.semantic_conflicts import (
    apply_conflict_autofix,
    build_autofix_plan,
    detect_feature_conflicts,
)


class SemanticConflictTests(unittest.TestCase):
    def test_autofix_plan_marks_sync_conflicts_unsafe(self) -> None:
        conflict_report = {
            "features": {
                "alpha-intake": {
                    "conflict_count": 1,
                    "conflicts": [
                        {
                            "type": "sync_conflict",
                            "reason": "target missing",
                            "resolution": "run workflow sync-all",
                        }
                    ],
                },
                "beta-intake": {
                    "conflict_count": 1,
                    "conflicts": [
                        {
                            "type": "tag_conflict",
                            "reason": "semantic_tags empty",
                            "resolution": "run workflow semantic-infer",
                        }
                    ],
                },
            }
        }

        plan = build_autofix_plan(conflict_report)

        self.assertEqual(plan["unsafe_count"], 1)
        self.assertEqual(plan["unsafe_features"][0]["slug"], "alpha-intake")
        self.assertIn("sync_conflict", plan["unsafe_features"][0]["unsafe_conflict_types"])
        self.assertIn("beta-intake", plan["safe_feature_slugs"])

    def test_detect_conflicts_reports_missing_sync_target(self) -> None:
        feature = {
            "slug": "alpha-intake",
            "mlas_tier": "Semantic Utility",
            "semantic_intent": "CaptureAndRoute",
            "semantic_tags": ["alpha", "intake"],
            "btif_classification": "IntakeFlow",
            "propagation": {
                "mlas": {
                    "slug": "alpha-intake",
                    "mlas_tier": "Semantic Utility",
                    "semantic_intent": "CaptureAndRoute",
                    "semantic_tags": "alpha,intake",
                },
                "btif_route": "btif://intakeflow/captureandroute/alpha-intake",
                "synced_targets": {
                    "erd_backend_models": "missing/path.py",
                },
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            conflicts = detect_feature_conflicts(feature, repo_root)

        self.assertTrue(any(item["type"] == "sync_conflict" for item in conflicts))

    def test_apply_conflict_autofix_normalizes_tags(self) -> None:
        feature = {
            "slug": "alpha-intake",
            "mlas_tier": "Semantic Utility",
            "semantic_intent": "CaptureAndRoute",
            "semantic_tags": ["Intake", "intake", "alpha"],
            "btif_classification": "IntakeFlow",
        }

        updated = apply_conflict_autofix(feature)

        self.assertIn("propagation", updated)
        self.assertEqual(updated["semantic_tags"], ["alpha", "intake"])


if __name__ == "__main__":
    unittest.main()
