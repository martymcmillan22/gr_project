from typing import Any

from .btif_router import assign_btif_route
from .mlas_integration import classify_feature_mlas, normalize_semantic_tags


def propagate_feature_semantics(feature: dict[str, Any], synced_targets: dict[str, str]) -> dict[str, Any]:
    feature["semantic_tags"] = normalize_semantic_tags(feature.get("semantic_tags", []))

    mlas = classify_feature_mlas(feature)
    btif_route = assign_btif_route(feature)

    feature["propagation"] = {
        "mlas": mlas,
        "btif_route": btif_route,
        "synced_targets": synced_targets,
    }
    return feature


def propagate_registry_semantics(registry: dict[str, Any], sync_results: dict[str, dict[str, str]]) -> dict[str, Any]:
    for feature in registry.get("features", []):
        slug = str(feature.get("slug", ""))
        targets = sync_results.get(slug, {})
        propagate_feature_semantics(feature, targets)
    return registry
