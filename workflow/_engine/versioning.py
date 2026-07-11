from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION_KEYS = [
    "workflow_engine_version",
    "semantic_engine_version",
    "sync_layer_version",
    "visualization_layer_version",
    "cli_version",
    "ai_native_layer_version",
]


@dataclass(frozen=True)
class VersionBumpResult:
    previous: dict[str, str]
    current: dict[str, str]
    part: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_version_state() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "workflow_engine_version": "0.1.0",
        "semantic_engine_version": "0.1.0",
        "sync_layer_version": "0.1.0",
        "visualization_layer_version": "0.1.0",
        "cli_version": "0.1.0",
        "ai_native_layer_version": "0.1.0",
        "release_sequence": 0,
        "last_release_at": None,
        "last_release_tag": None,
    }


def load_version_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _default_version_state()
    return json.loads(path.read_text(encoding="utf-8"))


def save_version_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _parse_semver(value: str) -> tuple[int, int, int]:
    parts = value.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"invalid semantic version: {value}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def _format_semver(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def bump_semver(value: str, part: str) -> str:
    major, minor, patch = _parse_semver(value)
    if part == "major":
        return _format_semver(major + 1, 0, 0)
    if part == "minor":
        return _format_semver(major, minor + 1, 0)
    if part == "patch":
        return _format_semver(major, minor, patch + 1)
    raise ValueError(f"unsupported version bump part: {part}")


def bump_all_versions(state: dict[str, Any], part: str) -> VersionBumpResult:
    previous = {key: str(state.get(key, "0.1.0")) for key in VERSION_KEYS}
    current: dict[str, str] = {}
    for key in VERSION_KEYS:
        current[key] = bump_semver(previous[key], part)
        state[key] = current[key]

    state["release_sequence"] = int(state.get("release_sequence", 0)) + 1
    state["last_release_at"] = _utc_now()
    state["last_release_tag"] = f"v{current['workflow_engine_version']}"
    return VersionBumpResult(previous=previous, current=current, part=part)


def get_version_report(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": str(state.get("schema_version", "1.0.0")),
        "versions": {key: str(state.get(key, "")) for key in VERSION_KEYS},
        "release_sequence": int(state.get("release_sequence", 0)),
        "last_release_at": state.get("last_release_at"),
        "last_release_tag": state.get("last_release_tag"),
    }
