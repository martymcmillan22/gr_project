from typing import Any


REQUIRED_FIELDS = {
    "name",
    "slug",
    "mlas_tier",
    "btif_classification",
    "semantic_intent",
    "paths",
    "semantic_tags",
    "status",
}


def validate_registry_shape(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if "schema_version" not in registry:
        errors.append("registry missing schema_version")
    if "workflow_version" not in registry:
        errors.append("registry missing workflow_version")
    features = registry.get("features")
    if not isinstance(features, list):
        errors.append("registry features must be a list")
        return errors

    seen_slugs: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            errors.append(f"feature[{index}] must be an object")
            continue
        missing = REQUIRED_FIELDS - set(feature.keys())
        if missing:
            errors.append(f"feature[{index}] missing fields: {', '.join(sorted(missing))}")
        slug = feature.get("slug")
        if isinstance(slug, str):
            if slug in seen_slugs:
                errors.append(f"duplicate feature slug: {slug}")
            seen_slugs.add(slug)
        paths = feature.get("paths")
        if not isinstance(paths, dict):
            errors.append(f"feature[{index}] paths must be an object")
    return errors
