#!/usr/bin/env python3
import argparse
import json
import sys

from _engine.btif_router import build_btif_routing_table
from _engine.config import REGISTRY_PATH, WORKFLOW_ROOT
from _engine.mlas_integration import build_mlas_report
from _engine.registry import add_feature, feature_exists, load_registry, save_registry
from _engine.scaffold import create_feature_scaffold, slugify
from _engine.validate import validate_registry_shape
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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
