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

        propagation = feature.get("propagation")
        if propagation is not None and not isinstance(propagation, dict):
            errors.append(f"feature[{index}] propagation must be an object when present")
        if isinstance(propagation, dict):
            mlas_block = propagation.get("mlas")
            if mlas_block is not None and not isinstance(mlas_block, dict):
                errors.append(f"feature[{index}] propagation.mlas must be an object")
            btif_route = propagation.get("btif_route")
            if btif_route is not None and (not isinstance(btif_route, str) or not btif_route.strip()):
                errors.append(f"feature[{index}] propagation.btif_route must be non-empty string")
            synced_targets = propagation.get("synced_targets")
            if synced_targets is not None and not isinstance(synced_targets, dict):
                errors.append(f"feature[{index}] propagation.synced_targets must be an object")

        lineage = feature.get("feature_lineage")
        if lineage is not None and (not isinstance(lineage, str) or not lineage.strip()):
            errors.append(f"feature[{index}] feature_lineage must be non-empty string when present")

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
