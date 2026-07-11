#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from _engine.config import REGISTRY_PATH, WORKFLOW_ROOT
from _engine.release_pipeline import run_release_pipeline
from _engine.semantic_infer import INFERENCE_CONFIDENCE_DEFAULT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run workflow release pipeline")
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Semantic version bump part",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=INFERENCE_CONFIDENCE_DEFAULT,
        help="Minimum confidence threshold for semantic inference release gate",
    )
    parser.add_argument(
        "--no-enforce-confidence",
        action="store_false",
        dest="enforce_confidence",
        default=True,
        help="Disable inference confidence gate during release",
    )
    parser.add_argument(
        "--approve-semantic-changes",
        action="store_true",
        help="Approve release when semantic governance deltas are detected",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    code, payload = run_release_pipeline(
        workflow_root=WORKFLOW_ROOT,
        registry_path=REGISTRY_PATH,
        version_path=WORKFLOW_ROOT / "version.json",
        semantic_changelog_path=WORKFLOW_ROOT / "semantic_changelog.md",
        release_notes_path=WORKFLOW_ROOT / "release_notes.json",
        ai_hints_path=WORKFLOW_ROOT / "ai_hints.json",
        ai_navigation_path=WORKFLOW_ROOT / "ai_navigation.json",
        semantic_context_path=WORKFLOW_ROOT / "semantic_context.json",
        governance_policy_path=WORKFLOW_ROOT / "governance_policy.json",
        bump_part=args.bump,
        enforce_confidence=args.enforce_confidence,
        min_confidence=args.min_confidence,
        approve_semantic_changes=args.approve_semantic_changes,
    )
    print(json.dumps(payload, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
