import unittest
from pathlib import Path
import sys

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from _engine.semantic_infer import evaluate_inference_policy, infer_feature_metadata


class SemanticInferTests(unittest.TestCase):
    def test_infer_defaults_for_missing_metadata(self) -> None:
        feature = {
            "slug": "alpha-intake",
            "semantic_tags": [],
            "paths": {},
        }

        report = infer_feature_metadata(feature, WORKFLOW_ROOT)

        self.assertEqual(report["predicted"]["mlas_tier"], "Semantic Utility")
        self.assertEqual(report["predicted"]["btif_classification"], "GeneralFlow")
        self.assertEqual(report["predicted"]["semantic_intent"], "CaptureAndRoute")
        self.assertEqual(report["predicted"]["semantic_tags"], ["alpha", "intake"])
        self.assertTrue(report["recommended_updates"]["mlas_tier"])
        self.assertTrue(report["recommended_updates"]["semantic_intent"])

    def test_inference_policy_flags_low_confidence(self) -> None:
        report = {
            "features": [
                {
                    "slug": "alpha-intake",
                    "confidence": {
                        "mlas_tier": 0.95,
                        "btif_classification": 0.95,
                        "semantic_intent": 0.62,
                        "semantic_tags": 0.62,
                    },
                }
            ]
        }

        policy = evaluate_inference_policy(report, min_confidence=0.8)

        self.assertFalse(policy["passes"])
        self.assertEqual(policy["failing_count"], 1)
        self.assertEqual(policy["failing_features"][0]["slug"], "alpha-intake")
        self.assertIn("semantic_intent", policy["failing_features"][0]["below_threshold"])
        self.assertIn("semantic_tags", policy["failing_features"][0]["below_threshold"])


if __name__ == "__main__":
    unittest.main()
