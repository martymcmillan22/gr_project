from typing import Any


def _norm(value: str) -> str:
    return value.strip().lower().replace(" ", "-")


def assign_btif_route(feature: dict[str, Any]) -> str:
    slug = _norm(str(feature.get("slug", "")))
    btif_classification = _norm(str(feature.get("btif_classification", "")))
    semantic_intent = _norm(str(feature.get("semantic_intent", "")))
    return f"btif://{btif_classification}/{semantic_intent}/{slug}"


def validate_btif_feature(feature: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    btif_classification = feature.get("btif_classification")
    semantic_intent = feature.get("semantic_intent")
    slug = feature.get("slug")

    if not isinstance(btif_classification, str) or not btif_classification.strip():
        errors.append(f"feature[{index}] invalid btif_classification")
    if not isinstance(semantic_intent, str) or not semantic_intent.strip():
        errors.append(f"feature[{index}] invalid semantic_intent for btif routing")
    if not isinstance(slug, str) or not slug.strip():
        errors.append(f"feature[{index}] invalid slug for btif routing")

    return errors


def build_btif_routing_table(registry: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for feature in registry.get("features", []):
        rows.append(
            {
                "slug": str(feature.get("slug", "")),
                "btif_classification": str(feature.get("btif_classification", "")),
                "route": assign_btif_route(feature),
            }
        )
    return rows
