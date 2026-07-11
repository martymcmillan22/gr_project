import unittest
from pathlib import Path
import sys

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from _engine.release_pipeline import _governance_diff


class ReleaseGovernanceTests(unittest.TestCase):
    def test_governance_diff_requires_approval_on_mlas_change(self) -> None:
        previous = {
            "semantic_lineage": [
                {
                    "slug": "pilot-intake",
                    "mlas": {
                        "mlas_tier": "Semantic Utility",
                        "semantic_intent": "CaptureAndRoute",
                    },
                    "btif_route": "btif://intakeflow/captureandroute/pilot-intake",
                }
            ],
            "tag_ontology": ["intake", "pilot"],
        }
        current = {
            "semantic_lineage": [
                {
                    "slug": "pilot-intake",
                    "mlas": {
                        "mlas_tier": "Semantic Control",
                        "semantic_intent": "CaptureAndRoute",
                    },
                    "btif_route": "btif://intakeflow/captureandroute/pilot-intake",
                }
            ],
            "tag_ontology": ["intake", "pilot"],
        }

        delta = _governance_diff(previous, current)

        self.assertTrue(delta["requires_approval"])
        self.assertEqual(delta["mlas_tier_changes"][0]["from"], "Semantic Utility")
        self.assertEqual(delta["mlas_tier_changes"][0]["to"], "Semantic Control")

    def test_governance_diff_no_changes(self) -> None:
        context = {
            "semantic_lineage": [
                {
                    "slug": "pilot-intake",
                    "mlas": {
                        "mlas_tier": "Semantic Utility",
                        "semantic_intent": "CaptureAndRoute",
                    },
                    "btif_route": "btif://intakeflow/captureandroute/pilot-intake",
                }
            ],
            "tag_ontology": ["intake", "pilot"],
        }

        delta = _governance_diff(context, context)

        self.assertFalse(delta["requires_approval"])
        self.assertEqual(delta["mlas_tier_changes"], [])


if __name__ == "__main__":
    unittest.main()
