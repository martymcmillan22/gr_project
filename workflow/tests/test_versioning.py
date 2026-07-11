import unittest
from pathlib import Path
import sys

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from _engine.versioning import bump_all_versions, bump_semver


class VersioningTests(unittest.TestCase):
    def test_bump_semver_patch(self) -> None:
        self.assertEqual(bump_semver("1.2.3", "patch"), "1.2.4")

    def test_bump_semver_minor(self) -> None:
        self.assertEqual(bump_semver("1.2.3", "minor"), "1.3.0")

    def test_bump_semver_major(self) -> None:
        self.assertEqual(bump_semver("1.2.3", "major"), "2.0.0")

    def test_bump_all_versions_advances_release_sequence(self) -> None:
        state = {
            "schema_version": "1.0.0",
            "workflow_engine_version": "0.6.0",
            "semantic_engine_version": "0.6.0",
            "sync_layer_version": "0.6.0",
            "visualization_layer_version": "0.6.0",
            "cli_version": "0.6.0",
            "ai_native_layer_version": "0.6.0",
            "release_sequence": 2,
        }

        result = bump_all_versions(state, "patch")

        self.assertEqual(result.current["workflow_engine_version"], "0.6.1")
        self.assertEqual(state["release_sequence"], 3)
        self.assertEqual(state["last_release_tag"], "v0.6.1")


if __name__ == "__main__":
    unittest.main()
