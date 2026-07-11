from pathlib import Path
from typing import Any

from _engine.btif_router import validate_btif_feature
from _engine.mlas_integration import validate_mlas_feature


def run_workflow_validation(workflow_root: Path, registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    features = registry.get("features", [])

    for index, feature in enumerate(features):
        slug = feature.get("slug")
        if not isinstance(slug, str) or not slug:
            errors.append(f"feature[{index}] has invalid slug")
            continue

        semantic_tags = feature.get("semantic_tags")
        if not isinstance(semantic_tags, list) or not semantic_tags:
            errors.append(f"feature[{index}] semantic_tags must be a non-empty list")

        semantic_intent = feature.get("semantic_intent")
        if not isinstance(semantic_intent, str) or not semantic_intent.strip():
            errors.append(f"feature[{index}] semantic_intent must be non-empty")

        errors.extend(validate_mlas_feature(feature, index))
        errors.extend(validate_btif_feature(feature, index))

        status = feature.get("status")
        if status not in {"scaffolded", "in-progress", "validated", "released"}:
            errors.append(f"feature[{index}] has invalid status: {status}")

        paths = feature.get("paths", {})
        required_paths = {"erd", "sequence", "ui_template", "ui_component"}
        if not isinstance(paths, dict):
            errors.append(f"feature[{index}] paths must be an object")
            continue

        missing_paths = required_paths - set(paths.keys())
        if missing_paths:
            errors.append(
                f"feature[{index}] missing path keys: {', '.join(sorted(missing_paths))}"
            )
            continue

        for key in sorted(required_paths):
            rel = paths.get(key)
            if not isinstance(rel, str) or not rel.strip():
                errors.append(f"feature[{index}] path '{key}' must be non-empty string")
                continue
            artifact = workflow_root / rel
            if not artifact.exists():
                errors.append(
                    f"feature[{index}] path '{key}' not found: {artifact.as_posix()}"
                )

    return errors
