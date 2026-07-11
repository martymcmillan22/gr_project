from pathlib import Path
from typing import Any

from .mlas_integration import normalize_semantic_tags


INFERENCE_CONFIDENCE_DEFAULT = 0.85
INFERENCE_CONFIDENCE_KEYS = [
    "mlas_tier",
    "btif_classification",
    "semantic_intent",
    "semantic_tags",
]


def _score(value_present: bool) -> float:
    return 0.95 if value_present else 0.62


def infer_feature_metadata(feature: dict[str, Any], workflow_root: Path) -> dict[str, Any]:
    slug = str(feature.get("slug", "")).strip()
    paths = feature.get("paths", {})

    tags = normalize_semantic_tags(feature.get("semantic_tags", []))
    semantic_intent = str(feature.get("semantic_intent", "")).strip()
    mlas_tier = str(feature.get("mlas_tier", "")).strip()
    btif_classification = str(feature.get("btif_classification", "")).strip()

    if not semantic_intent:
        semantic_intent = "CaptureAndRoute"
    if not mlas_tier:
        mlas_tier = "Semantic Utility"
    if not btif_classification:
        btif_classification = "GeneralFlow"
    if not tags:
        tags = [part for part in slug.split("-") if part]

    path_hints: list[str] = []
    for key in ["erd", "sequence", "ui_template", "ui_component"]:
        rel = str(paths.get(key, ""))
        if rel and (workflow_root / rel).exists():
            path_hints.append(f"{key}:exists")

    return {
        "slug": slug,
        "predicted": {
            "mlas_tier": mlas_tier,
            "btif_classification": btif_classification,
            "semantic_intent": semantic_intent,
            "semantic_tags": tags,
            "feature_lineage": f"workflow/{slug}",
            "dependency_classification": "deterministic",
        },
        "confidence": {
            "mlas_tier": _score(bool(feature.get("mlas_tier"))),
            "btif_classification": _score(bool(feature.get("btif_classification"))),
            "semantic_intent": _score(bool(feature.get("semantic_intent"))),
            "semantic_tags": _score(bool(feature.get("semantic_tags"))),
        },
        "justification": {
            "metadata_presence": "derived from explicit registry fields where present",
            "artifact_presence": ",".join(path_hints) if path_hints else "no artifact hints",
        },
        "recommended_updates": {
            "mlas_tier": feature.get("mlas_tier") != mlas_tier,
            "btif_classification": feature.get("btif_classification") != btif_classification,
            "semantic_intent": feature.get("semantic_intent") != semantic_intent,
            "semantic_tags": normalize_semantic_tags(feature.get("semantic_tags", [])) != tags,
        },
    }


def build_inference_report(registry: dict[str, Any], workflow_root: Path) -> dict[str, Any]:
    return {
        "features": [infer_feature_metadata(feature, workflow_root) for feature in registry.get("features", [])]
    }


def evaluate_inference_policy(report: dict[str, Any], min_confidence: float) -> dict[str, Any]:
    failing_features: list[dict[str, Any]] = []
    for feature in report.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        confidence = feature.get("confidence", {})
        below_threshold = {
            key: float(confidence.get(key, 0.0))
            for key in INFERENCE_CONFIDENCE_KEYS
            if float(confidence.get(key, 0.0)) < min_confidence
        }
        if below_threshold:
            failing_features.append(
                {
                    "slug": slug,
                    "below_threshold": below_threshold,
                }
            )

    return {
        "min_confidence": min_confidence,
        "failing_count": len(failing_features),
        "failing_features": failing_features,
        "passes": len(failing_features) == 0,
    }
