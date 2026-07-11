from pathlib import Path
from typing import Any

from .btif_router import assign_btif_route
from .mlas_integration import classify_feature_mlas, normalize_semantic_tags


SAFE_AUTOFIX_TYPES = {
    "mlas_conflict",
    "btif_conflict",
    "tag_conflict",
}


def detect_feature_conflicts(feature: dict[str, Any], repo_root: Path) -> list[dict[str, str]]:
    conflicts: list[dict[str, str]] = []
    propagation = feature.get("propagation", {}) if isinstance(feature.get("propagation", {}), dict) else {}
    mlas_block = propagation.get("mlas", {}) if isinstance(propagation.get("mlas", {}), dict) else {}

    derived_mlas = classify_feature_mlas(feature)
    for key in ["mlas_tier", "semantic_intent", "semantic_tags"]:
        expected = str(derived_mlas.get(key, ""))
        observed = str(mlas_block.get(key, ""))
        if observed and expected and observed != expected:
            conflicts.append(
                {
                    "type": "mlas_conflict",
                    "reason": f"{key} expected '{expected}' observed '{observed}'",
                    "resolution": f"set propagation.mlas.{key} to '{expected}'",
                }
            )

    expected_route = assign_btif_route(feature)
    observed_route = str(propagation.get("btif_route", ""))
    if observed_route and observed_route != expected_route:
        conflicts.append(
            {
                "type": "btif_conflict",
                "reason": f"route expected '{expected_route}' observed '{observed_route}'",
                "resolution": f"set propagation.btif_route to '{expected_route}'",
            }
        )

    synced = propagation.get("synced_targets", {}) if isinstance(propagation.get("synced_targets", {}), dict) else {}
    for key, rel in synced.items():
        if rel and not (repo_root / str(rel)).exists():
            conflicts.append(
                {
                    "type": "sync_conflict",
                    "reason": f"synced target missing for {key}: {rel}",
                    "resolution": "run workflow sync-all to regenerate outputs",
                }
            )

    tags = normalize_semantic_tags(feature.get("semantic_tags", []))
    if not tags:
        conflicts.append(
            {
                "type": "tag_conflict",
                "reason": "semantic_tags empty",
                "resolution": "run workflow semantic-infer and apply recommended tags",
            }
        )

    return conflicts


def build_conflict_report(registry: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    report: dict[str, Any] = {"features": {}}
    for feature in registry.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue
        conflicts = detect_feature_conflicts(feature, repo_root)
        report["features"][slug] = {
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
        }
    return report


def build_autofix_plan(conflict_report: dict[str, Any]) -> dict[str, Any]:
    safe_slugs: list[str] = []
    unsafe_slugs: list[dict[str, Any]] = []

    for slug, payload in conflict_report.get("features", {}).items():
        conflicts = payload.get("conflicts", [])
        conflict_types = {str(item.get("type", "")) for item in conflicts}

        if not conflicts:
            safe_slugs.append(slug)
            continue

        unsafe_types = sorted(conflict_types - SAFE_AUTOFIX_TYPES)
        if unsafe_types:
            unsafe_slugs.append(
                {
                    "slug": slug,
                    "unsafe_conflict_types": unsafe_types,
                }
            )
            continue

        safe_slugs.append(slug)

    return {
        "safe_feature_slugs": sorted(safe_slugs),
        "unsafe_features": sorted(unsafe_slugs, key=lambda item: item["slug"]),
        "unsafe_count": len(unsafe_slugs),
        "safe_count": len(safe_slugs),
    }


def apply_conflict_autofix(feature: dict[str, Any]) -> dict[str, Any]:
    propagation = feature.setdefault("propagation", {})
    propagation["mlas"] = classify_feature_mlas(feature)
    propagation["btif_route"] = assign_btif_route(feature)
    feature["semantic_tags"] = normalize_semantic_tags(feature.get("semantic_tags", []))
    return feature
