#!/usr/bin/env python3
import json
from pathlib import Path
import sys

from _engine.ai_native import build_ai_context_bundle
from _engine.config import REGISTRY_PATH, WORKFLOW_ROOT
from _engine.release_notes import build_release_notes, write_release_notes
from _engine.registry import load_registry
from _engine.versioning import get_version_report, load_version_state


def main() -> int:
    registry = load_registry(REGISTRY_PATH)
    version_state = load_version_state(WORKFLOW_ROOT / "meta" / "version.json")
    context_bundle = build_ai_context_bundle(registry, WORKFLOW_ROOT)

    notes = build_release_notes(
        version_state=version_state,
        registry=registry,
        semantic_context=context_bundle["semantic_context"],
        ai_hints=context_bundle["ai_hints"],
        ai_navigation=context_bundle["ai_navigation"],
        validation_checks={
            "generated_by": "release-notes",
            "version": get_version_report(version_state),
        },
    )
    out = write_release_notes(WORKFLOW_ROOT / "reports" / "release_notes.json", notes)
    print(json.dumps({"release_notes": out}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
