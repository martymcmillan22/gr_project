from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .btif_router import assign_btif_route
from .config import CATEGORY_DIRS
from .mlas_integration import classify_feature_mlas, normalize_semantic_tags
from .semantic_conflicts import SAFE_AUTOFIX_TYPES
from .semantic_infer import INFERENCE_CONFIDENCE_DEFAULT
from .validate import REQUIRED_FIELDS


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _registry_features(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [feature for feature in registry.get("features", []) if isinstance(feature, dict)]


def _collect_example_tags(features: list[dict[str, Any]]) -> list[str]:
    all_tags: set[str] = set()
    for feature in features:
        all_tags.update(normalize_semantic_tags(feature.get("semantic_tags", [])))
    return sorted(all_tags)


def _collect_mlas_tiers(features: list[dict[str, Any]]) -> list[str]:
    tiers = {str(feature.get("mlas_tier", "")).strip() for feature in features}
    return sorted(tier for tier in tiers if tier)


def _collect_btif_classes(features: list[dict[str, Any]]) -> list[str]:
    classes = {str(feature.get("btif_classification", "")).strip() for feature in features}
    return sorted(cls for cls in classes if cls)


def _base_command_docs() -> list[dict[str, str]]:
    return [
        {"command": "new-feature", "description": "Create deterministic feature artifacts and registry row"},
        {"command": "validate", "description": "Validate registry shape"},
        {"command": "validate-suite", "description": "Validate registry, artifacts, drift, and conflicts"},
        {"command": "classify", "description": "Export MLAS and BTIF classification reports"},
        {"command": "semantic-check", "description": "Run semantic validation checks"},
        {"command": "sync", "description": "Generate sync outputs for one feature"},
        {"command": "sync-all", "description": "Generate sync outputs for all features"},
        {"command": "visualize", "description": "Generate one feature visualization bundle"},
        {"command": "visualize-all", "description": "Generate full visualization bundle"},
        {"command": "semantic-drift", "description": "Detect semantic drift"},
        {"command": "semantic-infer", "description": "Infer semantic metadata with confidence policy"},
        {"command": "semantic-resolve", "description": "Resolve semantic conflicts with safety gate"},
        {"command": "semantic-health", "description": "Run deterministic semantic health scan and write weekly health report"},
        {"command": "ai-context", "description": "Print combined AI hints, navigation, and semantic context"},
        {"command": "ai-export", "description": "Write AI JSON context files for assistants"},
        {"command": "ai-new-feature", "description": "Generate feature from AI template with validation"},
        {"command": "version", "description": "Read semantic layer version identities"},
        {"command": "bump-version", "description": "Bump semantic versions for workflow release"},
        {"command": "release", "description": "Run governed release pipeline with safety gates"},
        {"command": "release-notes", "description": "Generate deterministic release notes payload"},
        {"command": "evolve-feature", "description": "Analyze one feature for deterministic evolution proposals"},
        {"command": "evolve-all", "description": "Analyze all features for deterministic evolution proposals"},
        {"command": "evolve-preview", "description": "Preview evolution proposals without apply-mode mutation"},
        {"command": "expand", "description": "Propose deterministic feature expansion opportunities"},
        {"command": "expand-all", "description": "Propose expansion opportunities across all features"},
        {"command": "expand-preview", "description": "Preview expansion proposals without apply-mode mutation"},
        {"command": "refactor-feature", "description": "Propose deterministic refactors for one feature"},
        {"command": "refactor-all", "description": "Propose deterministic refactors for all features"},
        {"command": "refactor-preview", "description": "Preview refactor proposals without apply-mode mutation"},
        {"command": "improve-feature", "description": "Run unified semantic improvement cycle for one feature"},
        {"command": "improve-all", "description": "Run unified semantic improvement cycle for all features"},
        {"command": "improve-preview", "description": "Preview unified improvement cycle without apply-mode mutation"},
    ]


def build_ai_hints(registry: dict[str, Any], workflow_root: Path) -> dict[str, Any]:
    features = _registry_features(registry)
    example_tags = _collect_example_tags(features)

    category_map = {
        "database_design": "database_design/mermaid_erds",
        "logic_design": "logic_design/mermaid_sequences",
        "ui_templates": "ui_templates/penpot_templates/features",
        "ui_components": "ui_components/penpot_components/features",
    }

    semantic_schema = {
        "name": "string",
        "slug": "string",
        "mlas_tier": "string",
        "btif_classification": "string",
        "semantic_intent": "string",
        "semantic_tags": "list[string]",
        "paths": {
            "erd": "string",
            "sequence": "string",
            "ui_template": "string",
            "ui_component": "string",
        },
        "status": "string",
        "propagation": {
            "mlas": "object",
            "btif_route": "string",
            "synced_targets": "object",
        },
    }

    examples = []
    for feature in features[:3]:
        examples.append(
            {
                "name": feature.get("name", ""),
                "slug": feature.get("slug", ""),
                "mlas_tier": feature.get("mlas_tier", ""),
                "btif_classification": feature.get("btif_classification", ""),
                "semantic_intent": feature.get("semantic_intent", ""),
                "semantic_tags": normalize_semantic_tags(feature.get("semantic_tags", [])),
                "route": assign_btif_route(feature),
            }
        )

    mappings = [
        {
            "slug": feature.get("slug", ""),
            "mlas_tier": feature.get("mlas_tier", ""),
            "btif_classification": feature.get("btif_classification", ""),
            "route": assign_btif_route(feature),
        }
        for feature in features[:10]
    ]

    return {
        "version": "1.0.0",
        "generated_at": _utc_timestamp(),
        "workflow_root": str(workflow_root.relative_to(workflow_root.parent)),
        "canonical_categories": category_map,
        "semantic_metadata_schema": semantic_schema,
        "mlas_tiers": [
            {"name": tier, "definition": "Observed MLAS tier from workflow registry"}
            for tier in _collect_mlas_tiers(features)
        ],
        "btif_routing": {
            "route_pattern": "btif://{btif_classification}/{semantic_intent}/{slug}",
            "known_classes": _collect_btif_classes(features),
        },
        "cli_commands": _base_command_docs(),
        "example_features": examples,
        "example_semantic_tags": example_tags,
        "example_mlas_btif_mappings": mappings,
    }


def build_feature_dependency_graph(registry: dict[str, Any]) -> dict[str, Any]:
    features = _registry_features(registry)
    nodes = [str(feature.get("slug", "")).strip() for feature in features if str(feature.get("slug", "")).strip()]

    edges: list[dict[str, Any]] = []
    for i, left in enumerate(features):
        left_slug = str(left.get("slug", "")).strip()
        left_tags = set(normalize_semantic_tags(left.get("semantic_tags", [])))
        if not left_slug:
            continue
        for right in features[i + 1 :]:
            right_slug = str(right.get("slug", "")).strip()
            right_tags = set(normalize_semantic_tags(right.get("semantic_tags", [])))
            if not right_slug:
                continue
            shared = sorted(left_tags.intersection(right_tags))
            if shared:
                edges.append(
                    {
                        "from": left_slug,
                        "to": right_slug,
                        "type": "shared_semantic_tags",
                        "shared_tags": shared,
                    }
                )

    return {"nodes": sorted(nodes), "edges": edges}


def build_ai_navigation(registry: dict[str, Any], workflow_root: Path) -> dict[str, Any]:
    features = _registry_features(registry)

    directory_map = {
        "workflow_root": "workflow",
        "registry": "workflow/registry.json",
        "engine": "workflow/_engine",
        "validation": "workflow/validation",
        "ai_prompts": "workflow/ai_prompts",
        "ai_templates": "workflow/ai_templates",
        "visualizations": "workflow/visualizations",
    }

    artifact_categories = {
        key: str(path.relative_to(workflow_root)) for key, path in CATEGORY_DIRS.items()
    }

    semantic_lineage = []
    sync_locations: dict[str, str] = {}
    for feature in features:
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue

        propagation = feature.get("propagation", {})
        synced_targets = propagation.get("synced_targets", {}) if isinstance(propagation, dict) else {}
        if isinstance(synced_targets, dict):
            for key, value in synced_targets.items():
                if isinstance(value, str) and value:
                    sync_locations[key] = value

        semantic_lineage.append(
            {
                "slug": slug,
                "feature_lineage": str(feature.get("feature_lineage", f"workflow/{slug}")),
                "mlas_tier": str(feature.get("mlas_tier", "")),
                "btif_route": str(propagation.get("btif_route", assign_btif_route(feature)))
                if isinstance(propagation, dict)
                else assign_btif_route(feature),
            }
        )

    visualization_outputs = {
        "feature_visualizations": "workflow/visualizations/features/{slug}.visualization.md",
        "global_graphs": [
            "workflow/visualizations/feature-dependency-graph.mmd",
            "workflow/visualizations/mlas-tier-map.mmd",
            "workflow/visualizations/btif-routing-map.mmd",
        ],
    }

    registry_schema = {
        "required_fields": sorted(REQUIRED_FIELDS),
        "schema_version": str(registry.get("schema_version", "")),
        "workflow_version": str(registry.get("workflow_version", "")),
    }

    dependency_graph = build_feature_dependency_graph(registry)

    return {
        "version": "1.0.0",
        "generated_at": _utc_timestamp(),
        "directory_map": directory_map,
        "artifact_categories": artifact_categories,
        "semantic_lineage": semantic_lineage,
        "sync_output_locations": sync_locations,
        "visualization_output_locations": visualization_outputs,
        "registry_schema": registry_schema,
        "feature_dependency_graph": dependency_graph,
    }


def build_semantic_context(registry: dict[str, Any]) -> dict[str, Any]:
    features = _registry_features(registry)
    tags = _collect_example_tags(features)
    tiers = _collect_mlas_tiers(features)
    btif_classes = _collect_btif_classes(features)

    semantic_intents = sorted(
        {
            str(feature.get("semantic_intent", "")).strip()
            for feature in features
            if str(feature.get("semantic_intent", "")).strip()
        }
    )

    lineage = [
        {
            "slug": str(feature.get("slug", "")).strip(),
            "mlas": classify_feature_mlas(feature),
            "btif_route": assign_btif_route(feature),
        }
        for feature in features
        if str(feature.get("slug", "")).strip()
    ]

    drift_rules = [
        "propagation.mlas.semantic_tags must match normalized semantic_tags",
        "propagation.mlas.mlas_tier must match feature mlas_tier",
        "propagation.btif_route must match computed BTIF route",
        "required artifact files must exist and include expected slug marker when applicable",
        "propagation.synced_targets must point to existing files when populated",
    ]

    inference_rules = [
        "prefer explicit registry metadata over inferred defaults",
        "fallback semantic_intent default is CaptureAndRoute",
        "fallback mlas_tier default is Semantic Utility",
        "fallback btif_classification default is GeneralFlow",
        "fallback semantic_tags derive from slug tokens",
    ]

    conflict_rules = [
        "mlas_conflict when propagation.mlas differs from derived MLAS block",
        "btif_conflict when propagation.btif_route differs from derived route",
        "sync_conflict when propagated sync target path does not exist",
        "tag_conflict when semantic_tags are empty after normalization",
    ]

    return {
        "version": "1.0.0",
        "generated_at": _utc_timestamp(),
        "mlas_tier_definitions": [
            {"name": tier, "definition": "Observed MLAS tier from workflow registry"}
            for tier in tiers
        ],
        "btif_routing_definitions": {
            "route_pattern": "btif://{btif_classification}/{semantic_intent}/{slug}",
            "known_classes": btif_classes,
        },
        "semantic_intent_definitions": [
            {"name": intent, "definition": "Observed semantic intent from workflow registry"}
            for intent in semantic_intents
        ],
        "tag_ontology": tags,
        "semantic_lineage": lineage,
        "drift_rules": drift_rules,
        "inference_rules": inference_rules,
        "conflict_rules": conflict_rules,
        "confidence_thresholds": {
            "default_min_confidence": INFERENCE_CONFIDENCE_DEFAULT,
            "fields": ["mlas_tier", "btif_classification", "semantic_intent", "semantic_tags"],
        },
        "autofix_safety_gates": {
            "safe_conflict_types": sorted(SAFE_AUTOFIX_TYPES),
            "requires_force_unsafe_for_other_types": True,
        },
    }


def build_ai_context_bundle(registry: dict[str, Any], workflow_root: Path) -> dict[str, Any]:
    return {
        "ai_hints": build_ai_hints(registry, workflow_root),
        "ai_navigation": build_ai_navigation(registry, workflow_root),
        "semantic_context": build_semantic_context(registry),
    }


def write_json_file(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path.as_posix()
