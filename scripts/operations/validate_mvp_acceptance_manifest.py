#!/usr/bin/env python3
"""Validate the BaseTrue Grassroots MVP acceptance manifest contract.

This script is intentionally dependency-free so it can run in local and CI
without requiring extra package installs.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "workflow" / "meta" / "mvp_acceptance_manifest.json"
CRITERIA_DOC_PATH = ROOT / "docs" / "operations" / "basetrue_grassroots_mvp_acceptance_criteria.md"
SNAPSHOT_DOC_PATH = ROOT / "docs" / "architecture" / "basetrue_grassroots_mvp_snapshot.md"


EXPECTED_PHASE_ORDER = ["Idea", "Seed", "Project", "MVP"]
EXPECTED_INHERITANCE = {
    "subjects": 4,
    "sevm_branches": 16,
    "industries": 64,
    "sub_industries": 256,
}
EXPECTED_SURFACE_MODES = {
    "math": "sacp_probability_surface",
    "language": "ednp_transcript_surface",
    "arts": "vlsm_creator_surface",
    "science": "mbsp_consumer_gui_surface",
}
EXPECTED_MICRO_TEMPLATE_RUNTIME = {
    "backend_rows_when_present": 256,
    "frontend_fallback_rows_when_industry_only": 64,
    "fallback_behavior_expected": True,
}

EXPECTED_AC_IDS = [
    "AC-IDEA-001",
    "AC-IDEA-002",
    "AC-SEED-001",
    "AC-SEED-002",
    "AC-PROJECT-001",
    "AC-PROJECT-002",
    "AC-PROJECT-003",
    "AC-PROJECT-004",
    "AC-PROJECT-005",
    "AC-PROJECT-006",
    "AC-PROJECT-007",
    "AC-MVP-001",
    "AC-MVP-002",
    "AC-MVP-003",
    "AC-INV-001",
    "AC-INV-002",
    "AC-INV-003",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_manifest() -> dict[str, object]:
    require(MANIFEST_PATH.exists(), f"Missing manifest: {MANIFEST_PATH}")
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Manifest is not valid JSON: {exc}")
    return {}


def load_doc_text(path: Path) -> str:
    require(path.exists(), f"Missing required doc: {path}")
    return path.read_text(encoding="utf-8")


def validate_contract(manifest: dict[str, object]) -> None:
    require(manifest.get("manifest_id") == "basetrue_grassroots_mvp_acceptance_manifest", "Unexpected manifest_id")
    require(manifest.get("manifest_version") == "1.0.0", "Unexpected manifest_version")

    source = manifest.get("source_of_truth")
    require(isinstance(source, dict), "source_of_truth must be an object")
    require(source.get("snapshot_doc") == "docs/architecture/basetrue_grassroots_mvp_snapshot.md", "snapshot_doc path mismatch")
    require(source.get("criteria_doc") == "docs/operations/basetrue_grassroots_mvp_acceptance_criteria.md", "criteria_doc path mismatch")

    deterministic = manifest.get("deterministic_contract")
    require(isinstance(deterministic, dict), "deterministic_contract must be an object")

    require(deterministic.get("phase_order") == EXPECTED_PHASE_ORDER, "phase_order drift detected")
    require(deterministic.get("inheritance") == EXPECTED_INHERITANCE, "inheritance contract drift detected")
    require(deterministic.get("lfo_surface_modes") == EXPECTED_SURFACE_MODES, "lfo_surface_modes drift detected")
    require(
        deterministic.get("micro_template_runtime") == EXPECTED_MICRO_TEMPLATE_RUNTIME,
        "micro_template_runtime drift detected",
    )


def validate_ac_ids(manifest: dict[str, object], criteria_text: str) -> None:
    criteria = manifest.get("acceptance_criteria")
    require(isinstance(criteria, list), "acceptance_criteria must be an array")

    ids: list[str] = []
    for item in criteria:
        require(isinstance(item, dict), "Each acceptance_criteria item must be an object")
        item_id = item.get("id")
        require(isinstance(item_id, str) and item_id.strip(), "Each acceptance_criteria item must include non-empty id")
        ids.append(item_id)
        require(item.get("required") is True, f"Acceptance criteria {item_id} must be required=true")

    require(len(ids) == len(set(ids)), "Duplicate AC IDs found in manifest")
    require(sorted(ids) == sorted(EXPECTED_AC_IDS), "AC ID set drift detected in manifest")

    for ac_id in EXPECTED_AC_IDS:
        require(ac_id in criteria_text, f"AC ID missing from criteria doc: {ac_id}")


def validate_snapshot_alignment(snapshot_text: str, criteria_text: str) -> None:
    # Snapshot must include canonical inheritance and fallback narrative.
    require("4. 256 sub-industries" in snapshot_text, "Snapshot missing 256 sub-industries contract")
    require("frontend fallback" in snapshot_text.lower(), "Snapshot missing frontend fallback narrative")
    require("64 rows" in snapshot_text, "Snapshot missing 64-row fallback detail")

    # Criteria must include the matching fallback AC guard.
    require("AC-PROJECT-007" in criteria_text, "Criteria missing AC-PROJECT-007")
    require("Backend micro template contract resolves 256 rows" in criteria_text, "Criteria missing backend 256-row fallback guard")
    require("Frontend fallback may resolve 64 rows" in criteria_text, "Criteria missing frontend 64-row fallback guard")


def validate_regression_commands(manifest: dict[str, object]) -> None:
    commands = manifest.get("required_regression_commands")
    require(isinstance(commands, list) and len(commands) >= 2, "required_regression_commands must include at least two commands")
    joined = "\n".join(str(item) for item in commands)
    require("ProjectMiddleLayerLfoEngineTests" in joined, "Missing backend regression command requirement")
    require("lfoEngineHelpers.test.js" in joined, "Missing frontend regression command requirement")


def main() -> int:
    manifest = load_manifest()
    criteria_text = load_doc_text(CRITERIA_DOC_PATH)
    snapshot_text = load_doc_text(SNAPSHOT_DOC_PATH)

    validate_contract(manifest)
    validate_ac_ids(manifest, criteria_text)
    validate_snapshot_alignment(snapshot_text, criteria_text)
    validate_regression_commands(manifest)

    print("PASS: MVP acceptance manifest validation succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
