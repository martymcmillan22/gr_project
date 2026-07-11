import json
from pathlib import Path
from typing import Any


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": "1.0.0",
            "workflow_version": "0.1.0",
            "features": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def feature_exists(registry: dict[str, Any], slug: str) -> bool:
    return any(feature.get("slug") == slug for feature in registry.get("features", []))


def add_feature(registry: dict[str, Any], feature: dict[str, Any]) -> None:
    registry.setdefault("features", []).append(feature)
