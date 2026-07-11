from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _feature_summary(registry: dict[str, Any]) -> list[dict[str, Any]]:
    features = registry.get("features", [])
    rows: list[dict[str, Any]] = []
    for feature in features:
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue
        rows.append(
            {
                "slug": slug,
                "mlas_tier": str(feature.get("mlas_tier", "")),
                "btif_classification": str(feature.get("btif_classification", "")),
                "semantic_intent": str(feature.get("semantic_intent", "")),
                "semantic_tags": sorted({str(tag).strip().lower() for tag in feature.get("semantic_tags", []) if str(tag).strip()}),
            }
        )
    return rows


def build_release_notes(
    version_state: dict[str, Any],
    registry: dict[str, Any],
    semantic_context: dict[str, Any],
    ai_hints: dict[str, Any],
    ai_navigation: dict[str, Any],
    validation_checks: dict[str, Any],
) -> dict[str, Any]:
    feature_rows = _feature_summary(registry)

    semantic_changes = {
        "mlas_tiers": [item.get("name") for item in semantic_context.get("mlas_tier_definitions", [])],
        "btif_classes": semantic_context.get("btif_routing_definitions", {}).get("known_classes", []),
        "semantic_intents": [item.get("name") for item in semantic_context.get("semantic_intent_definitions", [])],
        "tag_ontology_count": len(semantic_context.get("tag_ontology", [])),
    }

    sync_changes = {
        "sync_output_locations": ai_navigation.get("sync_output_locations", {}),
        "feature_count": len(feature_rows),
    }

    visualization_changes = {
        "global_outputs": ai_navigation.get("visualization_output_locations", {}).get("global_graphs", []),
        "feature_visualization_pattern": ai_navigation.get("visualization_output_locations", {}).get("feature_visualizations", ""),
    }

    ai_context_changes = {
        "ai_hints_version": ai_hints.get("version"),
        "ai_navigation_version": ai_navigation.get("version"),
        "semantic_context_version": semantic_context.get("version"),
    }

    governance_changes = {
        "confidence_thresholds": semantic_context.get("confidence_thresholds", {}),
        "autofix_safety_gates": semantic_context.get("autofix_safety_gates", {}),
        "validation_checks": validation_checks,
    }

    return {
        "generated_at": _utc_now(),
        "version": version_state.get("workflow_engine_version", ""),
        "release_tag": version_state.get("last_release_tag", ""),
        "changed_features": feature_rows,
        "semantic_changes": semantic_changes,
        "sync_changes": sync_changes,
        "visualization_changes": visualization_changes,
        "ai_context_changes": ai_context_changes,
        "governance_changes": governance_changes,
    }


def write_release_notes(path: Path, notes: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notes, indent=2) + "\n", encoding="utf-8")
    return path.as_posix()
