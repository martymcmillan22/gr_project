#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

from _engine.btif_router import build_btif_routing_table
from _engine.config import REGISTRY_PATH, WORKFLOW_ROOT
from _engine.semantic_propagation import propagate_feature_semantics, propagate_registry_semantics
from _engine.mlas_integration import build_mlas_report
from _engine.registry import add_feature, feature_exists, load_registry, save_registry
from _engine.scaffold import create_feature_scaffold, slugify
from _engine.sync_erd import sync_erd_to_backend_model_stub
from _engine.sync_sequence import sync_sequence_to_backend_logic_stub
from _engine.sync_ui_component import sync_ui_component_to_design_system
from _engine.sync_ui_template import sync_ui_template_to_react_page
from _engine.validate import validate_registry_shape
from _engine.visualize import write_feature_visualization, write_global_visualizations
from validation.suite import run_workflow_validation


def cmd_new_feature(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    slug = slugify(args.name)

    if not slug:
        print("ERROR: generated slug is empty")
        return 1
    if feature_exists(registry, slug):
        print(f"ERROR: feature already exists: {slug}")
        return 1

    paths = create_feature_scaffold(args.name, slug, args.mlas_tier, args.btif_classification)
    feature = {
        "name": args.name,
        "slug": slug,
        "mlas_tier": args.mlas_tier,
        "btif_classification": args.btif_classification,
        "semantic_intent": args.semantic_intent,
        "semantic_tags": sorted(set(args.semantic_tags)),
        "paths": paths,
        "status": "scaffolded",
    }
    add_feature(registry, feature)
    save_registry(REGISTRY_PATH, registry)
    print(f"OK: scaffolded feature '{args.name}' as '{slug}'")
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    errors = validate_registry_shape(registry)
    if errors:
        print("ERROR: registry validation failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OK: registry validation passed")
    return 0


def cmd_validate_suite(_: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    shape_errors = validate_registry_shape(registry)
    suite_errors = run_workflow_validation(WORKFLOW_ROOT, registry)
    errors = shape_errors + suite_errors
    if errors:
        print("ERROR: workflow validation suite failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OK: workflow validation suite passed")
    return 0


def cmd_classify(_: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    mlas_report = build_mlas_report(registry)
    btif_routes = build_btif_routing_table(registry)
    print(json.dumps({"mlas": mlas_report, "btif": btif_routes}, indent=2))
    return 0


def cmd_semantic_check(_: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    shape_errors = validate_registry_shape(registry)
    suite_errors = run_workflow_validation(WORKFLOW_ROOT, registry)
    errors = shape_errors + suite_errors
    if errors:
        print("ERROR: semantic-check failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OK: semantic-check passed")
    return 0


def _sync_feature(feature: dict, repo_root: Path) -> dict[str, str]:
    synced: dict[str, str] = {}
    paths = feature.get("paths", {})

    erd_path = repo_root / "workflow" / paths.get("erd", "")
    sequence_path = repo_root / "workflow" / paths.get("sequence", "")
    template_path = repo_root / "workflow" / paths.get("ui_template", "")
    component_spec_path = repo_root / "workflow" / paths.get("ui_component", "")

    erd_out = sync_erd_to_backend_model_stub(
        erd_path,
        feature["slug"],
        feature.get("mlas_tier", ""),
        repo_root,
    )
    synced["erd_backend_models"] = str(Path(erd_out).relative_to(repo_root))
    btif_route = feature.get("propagation", {}).get("btif_route", "")
    if not btif_route:
        btif_route = build_btif_routing_table({"features": [feature]})[0]["route"]

    seq_out = sync_sequence_to_backend_logic_stub(
        sequence_path,
        feature["slug"],
        feature.get("semantic_intent", ""),
        btif_route,
        repo_root,
    )
    synced["sequence_backend_logic"] = str(Path(seq_out).relative_to(repo_root))

    template_out = sync_ui_template_to_react_page(
        template_path,
        feature["slug"],
        feature.get("semantic_tags", []),
        repo_root,
    )
    synced["ui_template_react_page"] = str(Path(template_out).relative_to(repo_root))

    component_out = sync_ui_component_to_design_system(
        component_spec_path,
        feature["slug"],
        repo_root,
    )
    synced["ui_component_design_system"] = str(Path(component_out).relative_to(repo_root))
    return synced


def cmd_sync(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    feature = next((f for f in registry.get("features", []) if f.get("slug") == args.feature), None)
    if not feature:
        print(f"ERROR: feature not found: {args.feature}")
        return 1

    repo_root = WORKFLOW_ROOT.parent
    synced_targets = _sync_feature(feature, repo_root)
    propagate_feature_semantics(feature, synced_targets)
    save_registry(REGISTRY_PATH, registry)
    print(json.dumps({"feature": args.feature, "synced": synced_targets}, indent=2))
    return 0


def cmd_sync_all(_: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    repo_root = WORKFLOW_ROOT.parent
    all_results: dict[str, dict[str, str]] = {}

    for feature in registry.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue
        all_results[slug] = _sync_feature(feature, repo_root)

    propagate_registry_semantics(registry, all_results)
    save_registry(REGISTRY_PATH, registry)
    print(json.dumps({"synced": all_results}, indent=2))
    return 0


def cmd_visualize(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    feature = next((f for f in registry.get("features", []) if f.get("slug") == args.feature), None)
    if not feature:
        print(f"ERROR: feature not found: {args.feature}")
        return 1

    out_path = write_feature_visualization(feature, WORKFLOW_ROOT)
    print(json.dumps({"feature": args.feature, "visualization": out_path}, indent=2))
    return 0


def cmd_visualize_all(_: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    feature_outputs: dict[str, str] = {}
    for feature in registry.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue
        feature_outputs[slug] = write_feature_visualization(feature, WORKFLOW_ROOT)

    global_outputs = write_global_visualizations(registry, WORKFLOW_ROOT)
    print(json.dumps({"features": feature_outputs, "global": global_outputs}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Workflow command center CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    new_feature = sub.add_parser("new-feature", help="Generate deterministic feature scaffolds")
    new_feature.add_argument("--name", required=True, help="Human-readable feature name")
    new_feature.add_argument("--mlas-tier", required=True, help="MLAS tier tag")
    new_feature.add_argument("--btif-classification", required=True, help="BTIF classification tag")
    new_feature.add_argument("--semantic-intent", required=True, help="Semantic intent for routing")
    new_feature.add_argument(
        "--semantic-tags",
        nargs="+",
        default=[],
        help="Space-separated semantic tags",
    )
    new_feature.set_defaults(func=cmd_new_feature)

    validate = sub.add_parser("validate", help="Validate workflow registry shape")
    validate.set_defaults(func=cmd_validate)

    validate_suite = sub.add_parser(
        "validate-suite",
        help="Run registry and artifact validation suite",
    )
    validate_suite.set_defaults(func=cmd_validate_suite)

    classify = sub.add_parser(
        "classify",
        help="Generate MLAS classification and BTIF routing report",
    )
    classify.set_defaults(func=cmd_classify)

    semantic_check = sub.add_parser(
        "semantic-check",
        help="Run semantic validation checks for MLAS + BTIF consistency",
    )
    semantic_check.set_defaults(func=cmd_semantic_check)

    sync_cmd = sub.add_parser(
        "sync",
        help="Run sync layer for one feature and propagate semantics",
    )
    sync_cmd.add_argument("--feature", required=True, help="Feature slug to sync")
    sync_cmd.set_defaults(func=cmd_sync)

    sync_all = sub.add_parser(
        "sync-all",
        help="Run sync layer for all features and propagate semantics",
    )
    sync_all.set_defaults(func=cmd_sync_all)

    visualize = sub.add_parser(
        "visualize",
        help="Generate Mermaid visualization bundle for one feature",
    )
    visualize.add_argument("--feature", required=True, help="Feature slug to visualize")
    visualize.set_defaults(func=cmd_visualize)

    visualize_all = sub.add_parser(
        "visualize-all",
        help="Generate Mermaid visualizations for all features and global maps",
    )
    visualize_all.set_defaults(func=cmd_visualize_all)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
