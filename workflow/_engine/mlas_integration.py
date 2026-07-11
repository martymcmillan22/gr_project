from typing import Any


def normalize_semantic_tags(tags: list[str]) -> list[str]:
    return sorted({tag.strip().lower().replace(" ", "-") for tag in tags if tag.strip()})


def classify_feature_mlas(feature: dict[str, Any]) -> dict[str, str]:
    slug = str(feature.get("slug", "")).strip()
    mlas_tier = str(feature.get("mlas_tier", "")).strip()
    semantic_intent = str(feature.get("semantic_intent", "")).strip()
    semantic_tags = normalize_semantic_tags(feature.get("semantic_tags", []))
    return {
        "slug": slug,
        "mlas_tier": mlas_tier,
        "semantic_intent": semantic_intent,
        "semantic_tags": ",".join(semantic_tags),
    }


def validate_mlas_feature(feature: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    mlas_tier = feature.get("mlas_tier")
    semantic_intent = feature.get("semantic_intent")
    semantic_tags = feature.get("semantic_tags")

    if not isinstance(mlas_tier, str) or not mlas_tier.strip():
        errors.append(f"feature[{index}] invalid mlas_tier")
    if not isinstance(semantic_intent, str) or not semantic_intent.strip():
        errors.append(f"feature[{index}] invalid semantic_intent")
    if not isinstance(semantic_tags, list) or not semantic_tags:
        errors.append(f"feature[{index}] semantic_tags must be non-empty list")
    elif len(normalize_semantic_tags(semantic_tags)) != len(semantic_tags):
        errors.append(f"feature[{index}] semantic_tags must be unique normalized values")

    return errors


def build_mlas_report(registry: dict[str, Any]) -> list[dict[str, str]]:
    features = registry.get("features", [])
    return [classify_feature_mlas(feature) for feature in features]
