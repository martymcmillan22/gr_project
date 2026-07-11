#!/usr/bin/env python3
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

from _engine.ai_native import build_ai_context_bundle, write_json_file
from _engine.btif_router import build_btif_routing_table
from _engine.config import REGISTRY_PATH, WORKFLOW_ROOT
from _engine.release_notes import build_release_notes, write_release_notes
from _engine.release_pipeline import run_release_pipeline
from _engine.semantic_conflicts import apply_conflict_autofix, build_autofix_plan, build_conflict_report
from _engine.semantic_drift import build_drift_report
from _engine.semantic_infer import INFERENCE_CONFIDENCE_DEFAULT, build_inference_report, evaluate_inference_policy
from _engine.semantic_propagation import propagate_feature_semantics, propagate_registry_semantics
from _engine.mlas_integration import build_mlas_report
from _engine.registry import add_feature, feature_exists, load_registry, save_registry
from _engine.scaffold import create_feature_scaffold, slugify
from _engine.sync_erd import sync_erd_to_backend_model_stub
from _engine.sync_sequence import sync_sequence_to_backend_logic_stub
from _engine.sync_ui_component import sync_ui_component_to_design_system
from _engine.sync_ui_template import sync_ui_template_to_react_page
from _engine.validate import validate_registry_shape
from _engine.versioning import bump_all_versions, get_version_report, load_version_state, save_version_state
from _engine.visualize import write_feature_visualization, write_global_visualizations
from feature_expansion import (
    apply_expansion_report_to_registry,
    build_expansion_report,
    load_expansion_governance,
    validate_expansion_approvals,
)
from semantic_evolution import (
    apply_evolution_report_to_registry,
    build_evolution_report,
    load_long_term_governance,
    validate_evolution_approvals,
)
from semantic_refactor import (
    apply_refactor_report_to_registry,
    build_refactor_report,
    load_refactor_governance,
    validate_refactor_approvals,
)
from semantic_improvement_cycle import (
    apply_improvement_cycle_plan,
    build_improvement_cycle_plan,
    load_cycle_governance,
    validate_cycle_approvals,
)
from validation.suite import run_workflow_validation


AI_HINTS_PATH = WORKFLOW_ROOT / "ai_hints.json"
AI_NAVIGATION_PATH = WORKFLOW_ROOT / "ai_navigation.json"
AI_SEMANTIC_CONTEXT_PATH = WORKFLOW_ROOT / "semantic_context.json"
AI_FEATURE_TEMPLATE_PATH = WORKFLOW_ROOT / "ai_templates" / "feature.json"
VERSION_PATH = WORKFLOW_ROOT / "version.json"
RELEASE_NOTES_PATH = WORKFLOW_ROOT / "release_notes.json"
SEMANTIC_CHANGELOG_PATH = WORKFLOW_ROOT / "semantic_changelog.md"
GOVERNANCE_POLICY_PATH = WORKFLOW_ROOT / "governance_policy.json"
GOVERNANCE_LONG_TERM_PATH = WORKFLOW_ROOT / "governance_long_term.json"
AI_EVOLUTION_PATH = WORKFLOW_ROOT / "ai_evolution.json"
AI_EXPANSION_PATH = WORKFLOW_ROOT / "ai_expansion.json"
AI_REFACTOR_PATH = WORKFLOW_ROOT / "ai_refactor.json"
AI_CYCLE_PATH = WORKFLOW_ROOT / "ai_cycle.json"
CYCLE_PLAN_PATH = WORKFLOW_ROOT / "cycle_plan.json"
QUARTERLY_CYCLE_PLAN_PATH = WORKFLOW_ROOT / "cycle_plan_quarterly.json"
ANNUAL_CYCLE_PLAN_PATH = WORKFLOW_ROOT / "cycle_plan_annual.json"
SEMANTIC_HEALTH_PATH = WORKFLOW_ROOT / "semantic_health_report.json"
SEMANTIC_HEALTH_QUARTERLY_PATH = WORKFLOW_ROOT / "semantic_health_report_quarterly.json"
SEMANTIC_HEALTH_ANNUAL_PATH = WORKFLOW_ROOT / "semantic_health_report_annual.json"
SEMANTIC_SCORECARD_PATH = WORKFLOW_ROOT / "semantic_scorecard.json"
SEMANTIC_SCORECARD_QUARTERLY_PATH = WORKFLOW_ROOT / "semantic_scorecard_quarterly.json"
SEMANTIC_SCORECARD_ANNUAL_PATH = WORKFLOW_ROOT / "semantic_scorecard_annual.json"
MONTHLY_STRATEGY_REPORT_PATH = WORKFLOW_ROOT / "monthly_semantic_strategy_report.json"
QUARTERLY_STRATEGY_REPORT_PATH = WORKFLOW_ROOT / "quarterly_semantic_strategy_report.json"
ANNUAL_STRATEGY_REPORT_PATH = WORKFLOW_ROOT / "annual_semantic_strategy_report.json"
ANNUAL_DRIFT_FORECAST_PATH = WORKFLOW_ROOT / "annual_semantic_drift_forecast.json"


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
    repo_root = WORKFLOW_ROOT.parent
    suite_errors = run_workflow_validation(WORKFLOW_ROOT, registry)
    drift_report = build_drift_report(registry, WORKFLOW_ROOT, repo_root)
    conflict_report = build_conflict_report(registry, repo_root)

    drift_errors = []
    for slug, payload in drift_report.get("features", {}).items():
        if payload.get("drift_count", 0) > 0:
            drift_errors.append(f"drift detected for {slug}: {payload.get('drift_count')}")

    conflict_errors = []
    for slug, payload in conflict_report.get("features", {}).items():
        if payload.get("conflict_count", 0) > 0:
            conflict_errors.append(f"conflicts detected for {slug}: {payload.get('conflict_count')}")

    errors = shape_errors + suite_errors + drift_errors + conflict_errors
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
    repo_root = WORKFLOW_ROOT.parent
    suite_errors = run_workflow_validation(WORKFLOW_ROOT, registry)
    drift_report = build_drift_report(registry, WORKFLOW_ROOT, repo_root)
    conflict_report = build_conflict_report(registry, repo_root)

    drift_errors = []
    for slug, payload in drift_report.get("features", {}).items():
        if payload.get("drift_count", 0) > 0:
            drift_errors.append(f"drift detected for {slug}: {payload.get('drift_count')}")

    conflict_errors = []
    for slug, payload in conflict_report.get("features", {}).items():
        if payload.get("conflict_count", 0) > 0:
            conflict_errors.append(f"conflicts detected for {slug}: {payload.get('conflict_count')}")

    errors = shape_errors + suite_errors + drift_errors + conflict_errors
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


def cmd_semantic_drift(_: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    repo_root = WORKFLOW_ROOT.parent
    report = build_drift_report(registry, WORKFLOW_ROOT, repo_root)
    print(json.dumps(report, indent=2))
    return 0


def cmd_semantic_infer(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    report = build_inference_report(registry, WORKFLOW_ROOT)
    policy = evaluate_inference_policy(report, args.min_confidence)
    print(json.dumps({"inference": report, "policy": policy}, indent=2))
    if args.enforce_threshold and not policy.get("passes", False):
        print("ERROR: semantic inference confidence policy failed")
        return 1
    return 0


def cmd_semantic_resolve(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    repo_root = WORKFLOW_ROOT.parent
    conflict_report = build_conflict_report(registry, repo_root)
    autofix_plan = build_autofix_plan(conflict_report)

    if args.apply:
        unsafe = autofix_plan.get("unsafe_features", [])
        if unsafe and not args.force_unsafe:
            print(
                json.dumps(
                    {
                        "conflicts": conflict_report,
                        "autofix_plan": autofix_plan,
                        "autofix_applied": False,
                    },
                    indent=2,
                )
            )
            print("ERROR: unsafe conflicts detected; rerun with --force-unsafe to override")
            return 1

        safe_slugs = set(autofix_plan.get("safe_feature_slugs", []))
        for feature in registry.get("features", []):
            slug = str(feature.get("slug", "")).strip()
            if not args.force_unsafe and slug not in safe_slugs:
                continue
            apply_conflict_autofix(feature)
        save_registry(REGISTRY_PATH, registry)

    print(
        json.dumps(
            {
                "conflicts": conflict_report,
                "autofix_plan": autofix_plan,
                "autofix_applied": bool(args.apply),
                "force_unsafe": bool(args.force_unsafe),
            },
            indent=2,
        )
    )
    return 0


def cmd_semantic_health(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    repo_root = WORKFLOW_ROOT.parent

    shape_errors = validate_registry_shape(registry)
    suite_errors = run_workflow_validation(WORKFLOW_ROOT, registry)
    drift_report = build_drift_report(registry, WORKFLOW_ROOT, repo_root)
    inference_report = build_inference_report(registry, WORKFLOW_ROOT)
    inference_policy = evaluate_inference_policy(inference_report, args.min_confidence)
    conflict_report = build_conflict_report(registry, repo_root)
    autofix_plan = build_autofix_plan(conflict_report)
    cycle_policy = load_cycle_governance(GOVERNANCE_LONG_TERM_PATH)
    cycle_preview = build_improvement_cycle_plan(registry, WORKFLOW_ROOT, cycle_policy)

    drift_total = sum(
        int(payload.get("drift_count", 0))
        for payload in drift_report.get("features", {}).values()
        if isinstance(payload, dict)
    )
    conflict_total = sum(
        int(payload.get("conflict_count", 0))
        for payload in conflict_report.get("features", {}).values()
        if isinstance(payload, dict)
    )
    low_confidence_total = len(inference_policy.get("below_threshold", []))
    unsafe_conflict_features = len(autofix_plan.get("unsafe_features", []))
    feature_count = len(registry.get("features", []))

    report = {
        "generated_at": cycle_preview.get("generated_at"),
        "target": "all",
        "profile": args.profile,
        "feature_count": feature_count,
        "health_dimensions": {
            "semantic_aging_and_drift": drift_report,
            "metadata_inference": {
                "inference": inference_report,
                "policy": inference_policy,
                "min_confidence": args.min_confidence,
            },
            "sync_and_conflicts": {
                "conflicts": conflict_report,
                "autofix_plan": autofix_plan,
            },
            "validation": {
                "registry_shape_errors": shape_errors,
                "artifact_errors": suite_errors,
            },
            "improvement_cycle_preview": cycle_preview,
        },
        "summary": {
            "drift_total": drift_total,
            "conflict_total": conflict_total,
            "unsafe_conflict_features": unsafe_conflict_features,
            "low_confidence_total": low_confidence_total,
            "validation_error_total": len(shape_errors) + len(suite_errors),
            "cycle_proposal_count": cycle_preview.get("proposal_count", 0),
        },
        "passes": (
            drift_total == 0
            and conflict_total == 0
            and low_confidence_total == 0
            and not shape_errors
            and not suite_errors
        ),
    }

    if args.profile in {"monthly", "quarterly", "annual"}:
        tags: list[str] = []
        missing_intent: list[str] = []
        mlas_btif_gaps: list[str] = []
        for feature in registry.get("features", []):
            if not isinstance(feature, dict):
                continue
            slug = str(feature.get("slug", "")).strip()
            tags.extend(str(tag).strip().lower() for tag in feature.get("semantic_tags", []) if str(tag).strip())
            if not str(feature.get("semantic_intent", "")).strip() and slug:
                missing_intent.append(slug)
            if (not str(feature.get("mlas_tier", "")).strip() or not str(feature.get("btif_classification", "")).strip()) and slug:
                mlas_btif_gaps.append(slug)

        tag_counter = Counter(tags)
        low_reuse_tags = sorted([tag for tag, count in tag_counter.items() if count == 1])
        total_tags = sum(tag_counter.values())
        entropy = 0.0
        if total_tags > 0:
            for count in tag_counter.values():
                p = count / total_tags
                entropy -= p * math.log(p, 2)

        features = [f for f in registry.get("features", []) if isinstance(f, dict)]
        alignment_pairs = 0
        compared_pairs = 0
        for i, left in enumerate(features):
            left_tags = set(str(t).strip().lower() for t in left.get("semantic_tags", []) if str(t).strip())
            for right in features[i + 1 :]:
                compared_pairs += 1
                right_tags = set(str(t).strip().lower() for t in right.get("semantic_tags", []) if str(t).strip())
                if left_tags.intersection(right_tags):
                    alignment_pairs += 1

        drift_risk_score = round(
            min(
                1.0,
                (
                    (drift_total * 0.35)
                    + (conflict_total * 0.25)
                    + (low_confidence_total * 0.2)
                    + (int(cycle_preview.get("proposal_count", 0)) * 0.05)
                )
                / 10.0,
            ),
            3,
        )

        if args.profile == "monthly":
            scope_label = "monthly"
            drift_horizon = "next_month"
        elif args.profile == "quarterly":
            scope_label = "quarterly"
            drift_horizon = "next_quarter"
        else:
            scope_label = "annual"
            drift_horizon = "next_12_months"
        structural_entropy = round((len(low_reuse_tags) / len(tag_counter)), 4) if tag_counter else 0.0
        semantic_noise_index = round((len(low_reuse_tags) / total_tags), 4) if total_tags else 0.0
        stability_index = round(
            max(
                0.0,
                1.0
                - (
                    (drift_total * 0.06)
                    + (conflict_total * 0.05)
                    + (low_confidence_total * 0.08)
                    + (semantic_noise_index * 0.2)
                    + (drift_risk_score * 0.15)
                ),
            ),
            4,
        )

        report["health_dimensions"][f"{scope_label}_deep_scan"] = {
            "semantic_aging_analysis": {
                "drift_total": drift_total,
                "drift_by_feature": {
                    slug: payload.get("drift_count", 0)
                    for slug, payload in drift_report.get("features", {}).items()
                },
            },
            "ontology_aging_analysis": {
                "unique_tag_count": len(tag_counter),
                "low_reuse_tag_count": len(low_reuse_tags),
                "low_reuse_tags": low_reuse_tags,
                "structural_entropy": structural_entropy,
            },
            "mlas_btif_tier_drift_analysis": {
                "features_missing_mlas_or_btif": mlas_btif_gaps,
                "missing_count": len(mlas_btif_gaps),
            },
            "intent_coverage_gaps": {
                "features_missing_intent": missing_intent,
                "missing_count": len(missing_intent),
            },
            "cross_feature_semantic_alignment": {
                "aligned_pairs": alignment_pairs,
                "compared_pairs": compared_pairs,
                "alignment_ratio": round((alignment_pairs / compared_pairs), 3) if compared_pairs else 1.0,
            },
            "long_term_drift_risk_forecasting": {
                "risk_score": drift_risk_score,
                "horizon": drift_horizon,
                "risk_level": "high" if drift_risk_score >= 0.67 else "medium" if drift_risk_score >= 0.34 else "low",
            },
            "ai_context_entropy_analysis": {
                "semantic_tag_entropy_bits": round(entropy, 4),
                "semantic_noise_index": semantic_noise_index,
                "interpretation": "higher entropy indicates broader semantic spread",
            },
        }

        if args.profile in {"quarterly", "annual"}:
            deep_scan_key = f"{scope_label}_deep_scan"
            compared_pairs = report["health_dimensions"][deep_scan_key]["cross_feature_semantic_alignment"]["compared_pairs"]
            aligned_pairs = report["health_dimensions"][deep_scan_key]["cross_feature_semantic_alignment"]["aligned_pairs"]
            report["health_dimensions"][deep_scan_key]["dependency_graph_health"] = {
                "connected_pair_ratio": round((aligned_pairs / compared_pairs), 3) if compared_pairs else 1.0,
                "isolated_feature_risk": "high" if aligned_pairs == 0 and compared_pairs > 0 else "low",
            }
            index_key = "quarterly_semantic_stability_index" if args.profile == "quarterly" else "annual_semantic_stability_index"
            report["health_dimensions"][deep_scan_key][index_key] = {
                "value": stability_index,
                "interpretation": "higher is more stable",
            }

    if args.profile == "quarterly":
        health_out_path = SEMANTIC_HEALTH_QUARTERLY_PATH
    elif args.profile == "annual":
        health_out_path = SEMANTIC_HEALTH_ANNUAL_PATH
    else:
        health_out_path = SEMANTIC_HEALTH_PATH
    out = write_json_file(health_out_path, report)
    print(json.dumps({"semantic_health": report, "written": out}, indent=2))
    return 0


def cmd_semantic_drift_forecast(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    repo_root = WORKFLOW_ROOT.parent
    drift_report = build_drift_report(registry, WORKFLOW_ROOT, repo_root)
    conflict_report = build_conflict_report(registry, repo_root)

    drift_total = sum(
        int(payload.get("drift_count", 0))
        for payload in drift_report.get("features", {}).values()
        if isinstance(payload, dict)
    )
    conflict_total = sum(
        int(payload.get("conflict_count", 0))
        for payload in conflict_report.get("features", {}).values()
        if isinstance(payload, dict)
    )

    weighted_risk = min(1.0, ((drift_total * 0.55) + (conflict_total * 0.45)) / 10.0)
    forecast = {
        "generated_at": build_improvement_cycle_plan(registry, WORKFLOW_ROOT, load_cycle_governance(GOVERNANCE_LONG_TERM_PATH)).get("generated_at"),
        "profile": args.profile,
        "horizon_months": args.horizon_months,
        "drift_forecast": {
            "semantic_drift_risk": round(weighted_risk, 4),
            "ontology_drift_risk": round(min(1.0, weighted_risk * 1.05), 4),
            "mlas_btif_tier_drift_risk": round(min(1.0, weighted_risk * 0.95), 4),
            "tag_ontology_drift_risk": round(min(1.0, weighted_risk * 1.1), 4),
            "semantic_intent_drift_risk": round(min(1.0, weighted_risk * 0.9), 4),
            "ai_context_drift_risk": round(min(1.0, weighted_risk * 1.0), 4),
        },
        "inputs": {
            "drift_total": drift_total,
            "conflict_total": conflict_total,
        },
        "recommended_actions": [
            "Prioritize low-reuse ontology tags for normalization",
            "Review MLAS and BTIF lineage consistency before annual apply mode",
            "Run semantic-scorecard with annual profile before governance decisions",
        ],
    }

    forecast_out = ANNUAL_DRIFT_FORECAST_PATH if args.profile == "annual" else WORKFLOW_ROOT / "semantic_drift_forecast.json"
    out = write_json_file(forecast_out, forecast)
    print(json.dumps({"semantic_drift_forecast": forecast, "written": out}, indent=2))
    return 0


def cmd_semantic_scorecard(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    repo_root = WORKFLOW_ROOT.parent

    cycle_policy = load_cycle_governance(GOVERNANCE_LONG_TERM_PATH)
    cycle_plan = build_improvement_cycle_plan(registry, WORKFLOW_ROOT, cycle_policy)
    drift_report = build_drift_report(registry, WORKFLOW_ROOT, repo_root)
    conflict_report = build_conflict_report(registry, repo_root)
    inference_report = build_inference_report(registry, WORKFLOW_ROOT)
    inference_policy = evaluate_inference_policy(inference_report, args.min_confidence)

    drift_total = sum(
        int(payload.get("drift_count", 0))
        for payload in drift_report.get("features", {}).values()
        if isinstance(payload, dict)
    )
    conflict_total = sum(
        int(payload.get("conflict_count", 0))
        for payload in conflict_report.get("features", {}).values()
        if isinstance(payload, dict)
    )
    low_confidence_total = len(inference_policy.get("below_threshold", []))

    features = [f for f in registry.get("features", []) if isinstance(f, dict)]
    total = len(features)
    with_mlas_btif = 0
    with_intent = 0
    tags: list[str] = []
    for feature in features:
        if str(feature.get("mlas_tier", "")).strip() and str(feature.get("btif_classification", "")).strip():
            with_mlas_btif += 1
        if str(feature.get("semantic_intent", "")).strip():
            with_intent += 1
        tags.extend(str(tag).strip().lower() for tag in feature.get("semantic_tags", []) if str(tag).strip())

    tag_counter = Counter(tags)
    low_reuse_tags = [tag for tag, count in tag_counter.items() if count == 1]

    scorecard = {
        "generated_at": cycle_plan.get("generated_at"),
        "scope": args.profile,
        "metrics": {
            "semantic_consistency": {
                "drift_total": drift_total,
                "conflict_total": conflict_total,
                "score": max(0, 100 - ((drift_total * 10) + (conflict_total * 8))),
            },
            "ontology_health": {
                "unique_tag_count": len(tag_counter),
                "low_reuse_tag_count": len(low_reuse_tags),
                "score": max(0, 100 - (len(low_reuse_tags) * 3)),
            },
            "mlas_btif_tier_alignment": {
                "coverage_ratio": round(with_mlas_btif / total, 3) if total else 1.0,
                "score": round((with_mlas_btif / total) * 100) if total else 100,
            },
            "intent_coverage": {
                "coverage_ratio": round(with_intent / total, 3) if total else 1.0,
                "score": round((with_intent / total) * 100) if total else 100,
            },
            "ai_context_alignment": {
                "below_confidence_threshold": low_confidence_total,
                "score": max(0, 100 - (low_confidence_total * 20)),
                "min_confidence": args.min_confidence,
            },
        },
        "cycle_summary": {
            "proposal_count": cycle_plan.get("proposal_count", 0),
            "engine_order": cycle_plan.get("engine_order", []),
        },
        "council_decision_template": {
            "approve": [],
            "reject": [],
            "defer": [],
            "request_revision": [],
        },
    }

    if args.profile in {"quarterly", "annual"}:
        index_key = "quarterly_semantic_stability_index" if args.profile == "quarterly" else "annual_semantic_stability_index"
        scorecard["metrics"]["quarterly_semantic_stability_index"] = {
            "value": round(
                max(
                    0,
                    100
                    - (
                        (drift_total * 12)
                        + (conflict_total * 10)
                        + (low_confidence_total * 15)
                        + (len(low_reuse_tags) * 2)
                    ),
                ),
                2,
            ),
            "interpretation": "higher is more stable over long-range horizon",
        }
        if args.profile == "annual":
            scorecard["metrics"]["annual_semantic_stability_index"] = scorecard["metrics"].pop("quarterly_semantic_stability_index")

    if args.profile == "quarterly":
        scorecard_out = SEMANTIC_SCORECARD_QUARTERLY_PATH
    elif args.profile == "annual":
        scorecard_out = SEMANTIC_SCORECARD_ANNUAL_PATH
    else:
        scorecard_out = SEMANTIC_SCORECARD_PATH
    out = write_json_file(scorecard_out, scorecard)
    print(json.dumps({"semantic_scorecard": scorecard, "written": out}, indent=2))
    return 0


def cmd_semantic_strategy_report(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    cycle_policy = load_cycle_governance(GOVERNANCE_LONG_TERM_PATH)
    cycle_plan = build_improvement_cycle_plan(registry, WORKFLOW_ROOT, cycle_policy)

    scorecard = {
        "generated_at": cycle_plan.get("generated_at"),
        "scope": args.profile,
        "note": "Run semantic-scorecard to generate full scorecard artifact before council publication.",
    }
    if args.profile == "quarterly":
        scorecard_path = SEMANTIC_SCORECARD_QUARTERLY_PATH
    elif args.profile == "annual":
        scorecard_path = SEMANTIC_SCORECARD_ANNUAL_PATH
    else:
        scorecard_path = SEMANTIC_SCORECARD_PATH
    if scorecard_path.exists():
        try:
            scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    top_proposals = []
    for proposal in cycle_plan.get("aggregated_proposals", [])[:10]:
        if not isinstance(proposal, dict):
            continue
        top_proposals.append(
            {
                "engine": proposal.get("engine"),
                "category": proposal.get("category"),
                "confidence": proposal.get("confidence"),
                "governance_requirements": proposal.get("governance_requirements", []),
            }
        )

    report = {
        "generated_at": cycle_plan.get("generated_at"),
        "period": args.period or ("annual" if args.profile == "annual" else "quarterly" if args.profile == "quarterly" else "monthly"),
        "quarterly_alignment": bool(args.quarterly_alignment or args.profile in {"quarterly", "annual"}),
        "scope": args.profile,
        "semantic_scorecard": scorecard,
        "ontology_evolution_summary": {
            "source": "cycle_plan aggregated proposals",
            "proposal_count": cycle_plan.get("proposal_count", 0),
            "top_proposals": top_proposals,
        },
        "mlas_btif_evolution_summary": {
            "note": "Derived from approved evolution and expansion proposals in cycle governance review.",
        },
        "tag_ontology_evolution_summary": {
            "note": "Use low-reuse tag and ontology normalization proposals during council decisions.",
        },
        "governance_decisions": {
            "approved": args.approved,
            "rejected": args.rejected,
            "deferred": args.deferred,
            "requested_revisions": args.request_revision,
        },
        "applied_changes": {
            "requires_apply_mode": True,
            "command": "python3 workflow/cli.py improve-all --apply --approve-evolution --approve-expansion --approve-refactor --approve-semantic --approve-structural --approve-sync",
        },
        "next_priorities": args.next_priority,
    }

    if args.profile == "quarterly":
        strategy_path = QUARTERLY_STRATEGY_REPORT_PATH
    elif args.profile == "annual":
        strategy_path = ANNUAL_STRATEGY_REPORT_PATH
    else:
        strategy_path = MONTHLY_STRATEGY_REPORT_PATH
    out = write_json_file(strategy_path, report)
    print(json.dumps({"semantic_strategy_report": report, "written": out}, indent=2))
    return 0


def cmd_ai_context(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    bundle = build_ai_context_bundle(registry, WORKFLOW_ROOT)
    if args.write:
        hints_out = write_json_file(AI_HINTS_PATH, bundle["ai_hints"])
        nav_out = write_json_file(AI_NAVIGATION_PATH, bundle["ai_navigation"])
        semantic_out = write_json_file(AI_SEMANTIC_CONTEXT_PATH, bundle["semantic_context"])
        print(
            json.dumps(
                {
                    "context": bundle,
                    "written": {
                        "ai_hints": hints_out,
                        "ai_navigation": nav_out,
                        "semantic_context": semantic_out,
                    },
                },
                indent=2,
            )
        )
        return 0

    print(json.dumps(bundle, indent=2))
    return 0


def cmd_ai_export(_: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    bundle = build_ai_context_bundle(registry, WORKFLOW_ROOT)
    hints_out = write_json_file(AI_HINTS_PATH, bundle["ai_hints"])
    nav_out = write_json_file(AI_NAVIGATION_PATH, bundle["ai_navigation"])
    semantic_out = write_json_file(AI_SEMANTIC_CONTEXT_PATH, bundle["semantic_context"])
    print(
        json.dumps(
            {
                "exported": {
                    "ai_hints": hints_out,
                    "ai_navigation": nav_out,
                    "semantic_context": semantic_out,
                }
            },
            indent=2,
        )
    )
    return 0


def _load_ai_feature_template(path: Path) -> dict:
    if not path.exists():
        print(f"ERROR: AI feature template not found: {path.as_posix()}")
        raise FileNotFoundError(path.as_posix())
    return json.loads(path.read_text(encoding="utf-8"))


def _planned_feature_paths(slug: str) -> dict[str, str]:
    return {
        "erd": f"database_design/mermaid_erds/{slug}.erd.mmd",
        "sequence": f"logic_design/mermaid_sequences/{slug}.sequence.mmd",
        "ui_template": f"ui_templates/penpot_templates/features/{slug}/template.md",
        "ui_component": f"ui_components/penpot_components/features/{slug}/component.md",
    }


def cmd_ai_new_feature(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    template_path = Path(args.template_path)
    template = _load_ai_feature_template(template_path)

    name = args.name.strip()
    slug = slugify(name)
    if not slug:
        print("ERROR: generated slug is empty")
        return 1
    if feature_exists(registry, slug):
        print(f"ERROR: feature already exists: {slug}")
        return 1

    mlas_tier = str(args.mlas_tier or template.get("mlas_tier", "Semantic Utility")).strip()
    btif_classification = str(args.btif_classification or template.get("btif_classification", "GeneralFlow")).strip()
    semantic_intent = str(args.semantic_intent or template.get("semantic_intent", "CaptureAndRoute")).strip()

    template_tags = template.get("semantic_tags", [])
    provided_tags = args.semantic_tags if args.semantic_tags else template_tags
    semantic_tags = sorted(set(str(tag).strip() for tag in provided_tags if str(tag).strip()))

    if args.dry_run:
        preview = {
            "name": name,
            "slug": slug,
            "mlas_tier": mlas_tier,
            "btif_classification": btif_classification,
            "semantic_intent": semantic_intent,
            "semantic_tags": semantic_tags,
            "paths": _planned_feature_paths(slug),
            "status": "scaffolded",
            "dry_run": True,
        }
        print(json.dumps({"preview": preview}, indent=2))
        return 0

    paths = create_feature_scaffold(name, slug, mlas_tier, btif_classification)
    feature = {
        "name": name,
        "slug": slug,
        "mlas_tier": mlas_tier,
        "btif_classification": btif_classification,
        "semantic_intent": semantic_intent,
        "semantic_tags": semantic_tags,
        "paths": paths,
        "status": "scaffolded",
    }
    add_feature(registry, feature)
    save_registry(REGISTRY_PATH, registry)

    repo_root = WORKFLOW_ROOT.parent
    if args.sync:
        synced_targets = _sync_feature(feature, repo_root)
        propagate_feature_semantics(feature, synced_targets)
        save_registry(REGISTRY_PATH, registry)

    validation_errors = []
    if args.validate:
        validation_errors = validate_registry_shape(registry) + run_workflow_validation(WORKFLOW_ROOT, registry)

    visualization_path = ""
    if args.visualize:
        visualization_path = write_feature_visualization(feature, WORKFLOW_ROOT)

    result = {
        "feature": feature,
        "validated": args.validate,
        "validation_errors": validation_errors,
        "visualized": args.visualize,
        "visualization_path": visualization_path,
        "synced": args.sync,
    }
    if validation_errors:
        print(json.dumps(result, indent=2))
        print("ERROR: ai-new-feature generated invalid artifacts")
        return 1

    print(json.dumps(result, indent=2))
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    state = load_version_state(VERSION_PATH)
    print(json.dumps(get_version_report(state), indent=2))
    return 0


def cmd_bump_version(args: argparse.Namespace) -> int:
    state = load_version_state(VERSION_PATH)
    result = bump_all_versions(state, args.part)
    save_version_state(VERSION_PATH, state)
    print(
        json.dumps(
            {
                "part": result.part,
                "previous": result.previous,
                "current": result.current,
                "version": get_version_report(state),
            },
            indent=2,
        )
    )
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    code, payload = run_release_pipeline(
        workflow_root=WORKFLOW_ROOT,
        registry_path=REGISTRY_PATH,
        version_path=VERSION_PATH,
        semantic_changelog_path=SEMANTIC_CHANGELOG_PATH,
        release_notes_path=RELEASE_NOTES_PATH,
        ai_hints_path=AI_HINTS_PATH,
        ai_navigation_path=AI_NAVIGATION_PATH,
        semantic_context_path=AI_SEMANTIC_CONTEXT_PATH,
        governance_policy_path=GOVERNANCE_POLICY_PATH,
        bump_part=args.bump,
        enforce_confidence=args.enforce_confidence,
        min_confidence=args.min_confidence,
        approve_semantic_changes=args.approve_semantic_changes,
    )
    print(json.dumps(payload, indent=2))
    return code


def cmd_release_notes(_: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    state = load_version_state(VERSION_PATH)
    context_bundle = build_ai_context_bundle(registry, WORKFLOW_ROOT)
    notes = build_release_notes(
        version_state=state,
        registry=registry,
        semantic_context=context_bundle["semantic_context"],
        ai_hints=context_bundle["ai_hints"],
        ai_navigation=context_bundle["ai_navigation"],
        validation_checks={"generated_by": "workflow/cli.py release-notes"},
    )
    path = write_release_notes(RELEASE_NOTES_PATH, notes)
    print(json.dumps({"release_notes": path}, indent=2))
    return 0


def _evolution_approvals_from_args(args: argparse.Namespace) -> dict[str, bool]:
    return {
        "evolution_approval": bool(args.approve_evolution),
        "semantic_approval": bool(args.approve_semantic),
        "structural_approval": bool(args.approve_structural),
        "sync_approval": bool(args.approve_sync),
    }


def cmd_evolve_feature(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_long_term_governance(GOVERNANCE_LONG_TERM_PATH)
    report = build_evolution_report(registry, WORKFLOW_ROOT, policy, feature_slug=args.feature)

    if report.get("feature_count", 0) == 0:
        print(json.dumps({"error": f"feature not found: {args.feature}"}, indent=2))
        return 1

    if args.apply:
        missing = validate_evolution_approvals(report, _evolution_approvals_from_args(args))
        if missing:
            print(
                json.dumps(
                    {
                        "report": report,
                        "applied": False,
                        "missing_approvals": missing,
                    },
                    indent=2,
                )
            )
            print("ERROR: evolution apply blocked by governance approval gates")
            return 1

        apply_evolution_report_to_registry(registry, report)
        save_registry(REGISTRY_PATH, registry)

    print(json.dumps({"report": report, "applied": bool(args.apply)}, indent=2))
    return 0


def cmd_evolve_all(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_long_term_governance(GOVERNANCE_LONG_TERM_PATH)
    report = build_evolution_report(registry, WORKFLOW_ROOT, policy)

    if args.apply:
        missing = validate_evolution_approvals(report, _evolution_approvals_from_args(args))
        if missing:
            print(
                json.dumps(
                    {
                        "report": report,
                        "applied": False,
                        "missing_approvals": missing,
                    },
                    indent=2,
                )
            )
            print("ERROR: evolution apply blocked by governance approval gates")
            return 1

        apply_evolution_report_to_registry(registry, report)
        save_registry(REGISTRY_PATH, registry)

    print(json.dumps({"report": report, "applied": bool(args.apply)}, indent=2))
    return 0


def cmd_evolve_preview(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_long_term_governance(GOVERNANCE_LONG_TERM_PATH)
    report = build_evolution_report(registry, WORKFLOW_ROOT, policy)

    if args.write:
        out = write_json_file(AI_EVOLUTION_PATH, report)
        print(json.dumps({"report": report, "written": out}, indent=2))
        return 0

    print(json.dumps({"report": report}, indent=2))
    return 0


def _expansion_approvals_from_args(args: argparse.Namespace) -> dict[str, bool]:
    return {
        "expansion_approval": bool(args.approve_expansion),
        "semantic_approval": bool(args.approve_semantic),
        "structural_approval": bool(args.approve_structural),
        "sync_approval": bool(args.approve_sync),
    }


def cmd_expand(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_expansion_governance(GOVERNANCE_LONG_TERM_PATH)
    report = build_expansion_report(registry, policy, target_slug=args.target)

    if args.apply:
        missing = validate_expansion_approvals(report, _expansion_approvals_from_args(args))
        if missing:
            print(
                json.dumps(
                    {
                        "report": report,
                        "applied": False,
                        "missing_approvals": missing,
                    },
                    indent=2,
                )
            )
            print("ERROR: expansion apply blocked by governance approval gates")
            return 1

        apply_expansion_report_to_registry(registry, report, create_scaffolds=True)
        save_registry(REGISTRY_PATH, registry)

    print(json.dumps({"report": report, "applied": bool(args.apply)}, indent=2))
    return 0


def cmd_expand_all(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_expansion_governance(GOVERNANCE_LONG_TERM_PATH)
    report = build_expansion_report(registry, policy)

    if args.apply:
        missing = validate_expansion_approvals(report, _expansion_approvals_from_args(args))
        if missing:
            print(
                json.dumps(
                    {
                        "report": report,
                        "applied": False,
                        "missing_approvals": missing,
                    },
                    indent=2,
                )
            )
            print("ERROR: expansion apply blocked by governance approval gates")
            return 1

        apply_expansion_report_to_registry(registry, report, create_scaffolds=True)
        save_registry(REGISTRY_PATH, registry)

    print(json.dumps({"report": report, "applied": bool(args.apply)}, indent=2))
    return 0


def cmd_expand_preview(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_expansion_governance(GOVERNANCE_LONG_TERM_PATH)
    report = build_expansion_report(registry, policy)

    if args.write:
        out = write_json_file(AI_EXPANSION_PATH, report)
        print(json.dumps({"report": report, "written": out}, indent=2))
        return 0

    print(json.dumps({"report": report}, indent=2))
    return 0


def _refactor_approvals_from_args(args: argparse.Namespace) -> dict[str, bool]:
    return {
        "refactor_approval": bool(args.approve_refactor),
        "semantic_approval": bool(args.approve_semantic),
        "structural_approval": bool(args.approve_structural),
        "sync_approval": bool(args.approve_sync),
    }


def cmd_refactor_feature(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_refactor_governance(GOVERNANCE_LONG_TERM_PATH)
    report = build_refactor_report(registry, WORKFLOW_ROOT, policy, feature_slug=args.feature)

    if args.apply:
        missing = validate_refactor_approvals(report, _refactor_approvals_from_args(args))
        if missing:
            print(
                json.dumps(
                    {
                        "report": report,
                        "applied": False,
                        "missing_approvals": missing,
                    },
                    indent=2,
                )
            )
            print("ERROR: refactor apply blocked by governance approval gates")
            return 1

        apply_refactor_report_to_registry(registry, report)
        save_registry(REGISTRY_PATH, registry)

    print(json.dumps({"report": report, "applied": bool(args.apply)}, indent=2))
    return 0


def cmd_refactor_all(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_refactor_governance(GOVERNANCE_LONG_TERM_PATH)
    report = build_refactor_report(registry, WORKFLOW_ROOT, policy)

    if args.apply:
        missing = validate_refactor_approvals(report, _refactor_approvals_from_args(args))
        if missing:
            print(
                json.dumps(
                    {
                        "report": report,
                        "applied": False,
                        "missing_approvals": missing,
                    },
                    indent=2,
                )
            )
            print("ERROR: refactor apply blocked by governance approval gates")
            return 1

        apply_refactor_report_to_registry(registry, report)
        save_registry(REGISTRY_PATH, registry)

    print(json.dumps({"report": report, "applied": bool(args.apply)}, indent=2))
    return 0


def cmd_refactor_preview(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_refactor_governance(GOVERNANCE_LONG_TERM_PATH)
    report = build_refactor_report(registry, WORKFLOW_ROOT, policy)

    if args.write:
        out = write_json_file(AI_REFACTOR_PATH, report)
        print(json.dumps({"report": report, "written": out}, indent=2))
        return 0

    print(json.dumps({"report": report}, indent=2))
    return 0


def _cycle_approvals_from_args(args: argparse.Namespace) -> dict[str, bool]:
    return {
        "evolution_approval": bool(args.approve_evolution),
        "expansion_approval": bool(args.approve_expansion),
        "refactor_approval": bool(args.approve_refactor),
        "semantic_approval": bool(args.approve_semantic),
        "structural_approval": bool(args.approve_structural),
        "sync_approval": bool(args.approve_sync),
    }


def cmd_improve_feature(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_cycle_governance(GOVERNANCE_LONG_TERM_PATH)
    plan = build_improvement_cycle_plan(registry, WORKFLOW_ROOT, policy, feature_slug=args.feature)
    write_json_file(CYCLE_PLAN_PATH, plan)

    if args.apply:
        missing = validate_cycle_approvals(plan, _cycle_approvals_from_args(args), policy)
        if missing:
            print(
                json.dumps(
                    {
                        "plan": plan,
                        "applied": False,
                        "missing_approvals": missing,
                    },
                    indent=2,
                )
            )
            print("ERROR: improvement cycle apply blocked by governance approval gates")
            return 1

        apply_improvement_cycle_plan(registry, plan)
        save_registry(REGISTRY_PATH, registry)

    print(json.dumps({"plan": plan, "cycle_plan": str(CYCLE_PLAN_PATH), "applied": bool(args.apply)}, indent=2))
    return 0


def cmd_improve_all(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_cycle_governance(GOVERNANCE_LONG_TERM_PATH)
    plan = build_improvement_cycle_plan(registry, WORKFLOW_ROOT, policy)
    if args.profile == "quarterly":
        cycle_out = QUARTERLY_CYCLE_PLAN_PATH
    elif args.profile == "annual":
        cycle_out = ANNUAL_CYCLE_PLAN_PATH
    else:
        cycle_out = CYCLE_PLAN_PATH
    write_json_file(cycle_out, plan)

    if args.apply:
        missing = validate_cycle_approvals(plan, _cycle_approvals_from_args(args), policy)
        if missing:
            print(
                json.dumps(
                    {
                        "plan": plan,
                        "applied": False,
                        "missing_approvals": missing,
                    },
                    indent=2,
                )
            )
            print("ERROR: improvement cycle apply blocked by governance approval gates")
            return 1

        apply_improvement_cycle_plan(registry, plan)
        save_registry(REGISTRY_PATH, registry)

    print(json.dumps({"plan": plan, "cycle_plan": str(cycle_out), "applied": bool(args.apply), "profile": args.profile}, indent=2))
    return 0


def cmd_improve_preview(args: argparse.Namespace) -> int:
    registry = load_registry(REGISTRY_PATH)
    policy = load_cycle_governance(GOVERNANCE_LONG_TERM_PATH)
    plan = build_improvement_cycle_plan(registry, WORKFLOW_ROOT, policy)

    if args.write:
        out = write_json_file(AI_CYCLE_PATH, plan)
        print(json.dumps({"plan": plan, "written": out}, indent=2))
        return 0

    print(json.dumps({"plan": plan}, indent=2))
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

    semantic_drift = sub.add_parser(
        "semantic-drift",
        help="Detect semantic drift across registry, artifacts, and propagation",
    )
    semantic_drift.set_defaults(func=cmd_semantic_drift)

    semantic_infer = sub.add_parser(
        "semantic-infer",
        help="Infer semantic metadata recommendations",
    )
    semantic_infer.add_argument(
        "--min-confidence",
        type=float,
        default=INFERENCE_CONFIDENCE_DEFAULT,
        help="Minimum confidence threshold for inference policy checks",
    )
    semantic_infer.add_argument(
        "--enforce-threshold",
        action="store_true",
        help="Fail command when any semantic confidence score is below --min-confidence",
    )
    semantic_infer.set_defaults(func=cmd_semantic_infer)

    semantic_resolve = sub.add_parser(
        "semantic-resolve",
        help="Detect semantic conflicts and optionally apply deterministic autofix",
    )
    semantic_resolve.add_argument(
        "--apply",
        action="store_true",
        help="Apply deterministic conflict autofix updates to registry",
    )
    semantic_resolve.add_argument(
        "--force-unsafe",
        action="store_true",
        help="Override safety gate and apply autofix even when unsafe conflict types are present",
    )
    semantic_resolve.set_defaults(func=cmd_semantic_resolve)

    semantic_health = sub.add_parser(
        "semantic-health",
        help="Run deterministic semantic health scan with weekly, monthly, or quarterly profile outputs",
    )
    semantic_health.add_argument(
        "--min-confidence",
        type=float,
        default=INFERENCE_CONFIDENCE_DEFAULT,
        help="Minimum confidence threshold for semantic health inference checks",
    )
    semantic_health.add_argument(
        "--profile",
        choices=["weekly", "monthly", "quarterly", "annual"],
        default="weekly",
        help="Health scan depth profile",
    )
    semantic_health.set_defaults(func=cmd_semantic_health)

    semantic_drift_forecast = sub.add_parser(
        "semantic-drift-forecast",
        help="Generate semantic drift forecast report for long-range governance planning",
    )
    semantic_drift_forecast.add_argument(
        "--profile",
        choices=["monthly", "quarterly", "annual"],
        default="annual",
        help="Forecast scope",
    )
    semantic_drift_forecast.add_argument(
        "--horizon-months",
        type=int,
        default=12,
        help="Forecast horizon in months",
    )
    semantic_drift_forecast.set_defaults(func=cmd_semantic_drift_forecast)

    semantic_scorecard = sub.add_parser(
        "semantic-scorecard",
        help="Generate monthly or quarterly semantic scorecard artifact for governance review",
    )
    semantic_scorecard.add_argument(
        "--min-confidence",
        type=float,
        default=INFERENCE_CONFIDENCE_DEFAULT,
        help="Minimum confidence threshold for AI alignment score",
    )
    semantic_scorecard.add_argument(
        "--profile",
        choices=["monthly", "quarterly", "annual"],
        default="monthly",
        help="Scorecard scope",
    )
    semantic_scorecard.set_defaults(func=cmd_semantic_scorecard)

    semantic_strategy_report = sub.add_parser(
        "semantic-strategy-report",
        help="Publish monthly or quarterly semantic strategy report artifact for governance council",
    )
    semantic_strategy_report.add_argument(
        "--period",
        default="",
        help="Reporting period label, for example 2026-07",
    )
    semantic_strategy_report.add_argument(
        "--profile",
        choices=["monthly", "quarterly", "annual"],
        default="monthly",
        help="Strategy report scope",
    )
    semantic_strategy_report.add_argument(
        "--quarterly-alignment",
        action="store_true",
        help="Mark report as quarter-end aligned",
    )
    semantic_strategy_report.add_argument(
        "--approved",
        nargs="*",
        default=[],
        help="Council approved proposal identifiers",
    )
    semantic_strategy_report.add_argument(
        "--rejected",
        nargs="*",
        default=[],
        help="Council rejected proposal identifiers",
    )
    semantic_strategy_report.add_argument(
        "--deferred",
        nargs="*",
        default=[],
        help="Council deferred proposal identifiers",
    )
    semantic_strategy_report.add_argument(
        "--request-revision",
        nargs="*",
        default=[],
        help="Proposal identifiers requiring revision",
    )
    semantic_strategy_report.add_argument(
        "--next-priority",
        nargs="*",
        default=[],
        help="Next month semantic priorities",
    )
    semantic_strategy_report.set_defaults(func=cmd_semantic_strategy_report)

    ai_context = sub.add_parser(
        "ai-context",
        help="Print AI-native context bundle for assistants",
    )
    ai_context.add_argument(
        "--write",
        action="store_true",
        help="Also write AI context files to workflow root",
    )
    ai_context.set_defaults(func=cmd_ai_context)

    ai_export = sub.add_parser(
        "ai-export",
        help="Write AI-native context files to workflow root",
    )
    ai_export.set_defaults(func=cmd_ai_export)

    ai_new_feature = sub.add_parser(
        "ai-new-feature",
        help="Create workflow feature using AI template defaults and deterministic scaffolding",
    )
    ai_new_feature.add_argument("--name", required=True, help="Human-readable feature name")
    ai_new_feature.add_argument(
        "--template-path",
        default=AI_FEATURE_TEMPLATE_PATH.as_posix(),
        help="Path to AI feature template JSON",
    )
    ai_new_feature.add_argument("--mlas-tier", help="Override MLAS tier")
    ai_new_feature.add_argument("--btif-classification", help="Override BTIF classification")
    ai_new_feature.add_argument("--semantic-intent", help="Override semantic intent")
    ai_new_feature.add_argument("--semantic-tags", nargs="+", default=[], help="Override semantic tags")
    ai_new_feature.add_argument("--dry-run", action="store_true", help="Preview feature without writing files")
    ai_new_feature.add_argument(
        "--no-validate",
        action="store_false",
        dest="validate",
        default=True,
        help="Skip validation for generated feature",
    )
    ai_new_feature.add_argument(
        "--no-visualize",
        action="store_false",
        dest="visualize",
        default=True,
        help="Skip visualization generation for feature",
    )
    ai_new_feature.add_argument(
        "--sync",
        action="store_true",
        help="Run sync layer for generated feature",
    )
    ai_new_feature.set_defaults(func=cmd_ai_new_feature)

    version_cmd = sub.add_parser(
        "version",
        help="Show workflow layer versions from workflow/version.json",
    )
    version_cmd.set_defaults(func=cmd_version)

    bump_version = sub.add_parser(
        "bump-version",
        help="Bump workflow semantic version layers",
    )
    bump_version.add_argument(
        "--part",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Semantic version bump part",
    )
    bump_version.set_defaults(func=cmd_bump_version)

    release = sub.add_parser(
        "release",
        help="Run full release pipeline with governance safety gates",
    )
    release.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Semantic version bump part",
    )
    release.add_argument(
        "--min-confidence",
        type=float,
        default=INFERENCE_CONFIDENCE_DEFAULT,
        help="Minimum confidence threshold for semantic inference release gate",
    )
    release.add_argument(
        "--no-enforce-confidence",
        action="store_false",
        dest="enforce_confidence",
        default=True,
        help="Disable semantic inference confidence gate",
    )
    release.add_argument(
        "--approve-semantic-changes",
        action="store_true",
        help="Approve release when MLAS/BTIF/intent/tag ontology changes are detected",
    )
    release.set_defaults(func=cmd_release)

    release_notes = sub.add_parser(
        "release-notes",
        help="Generate release_notes.json from current workflow state",
    )
    release_notes.set_defaults(func=cmd_release_notes)

    evolve_feature = sub.add_parser(
        "evolve-feature",
        help="Analyze one feature and produce deterministic semantic evolution proposals",
    )
    evolve_feature.add_argument("--feature", required=True, help="Feature slug to evolve")
    evolve_feature.add_argument("--apply", action="store_true", help="Apply proposal metadata to registry")
    evolve_feature.add_argument("--approve-evolution", action="store_true", help="Approve baseline evolution proposals")
    evolve_feature.add_argument("--approve-semantic", action="store_true", help="Approve semantic evolution proposals")
    evolve_feature.add_argument("--approve-structural", action="store_true", help="Approve ERD/sequence refactor proposals")
    evolve_feature.add_argument("--approve-sync", action="store_true", help="Approve UI/component sync-related proposals")
    evolve_feature.set_defaults(func=cmd_evolve_feature)

    evolve_all = sub.add_parser(
        "evolve-all",
        help="Analyze all workflow features and produce deterministic semantic evolution proposals",
    )
    evolve_all.add_argument("--apply", action="store_true", help="Apply proposal metadata to registry")
    evolve_all.add_argument("--approve-evolution", action="store_true", help="Approve baseline evolution proposals")
    evolve_all.add_argument("--approve-semantic", action="store_true", help="Approve semantic evolution proposals")
    evolve_all.add_argument("--approve-structural", action="store_true", help="Approve ERD/sequence refactor proposals")
    evolve_all.add_argument("--approve-sync", action="store_true", help="Approve UI/component sync-related proposals")
    evolve_all.set_defaults(func=cmd_evolve_all)

    evolve_preview = sub.add_parser(
        "evolve-preview",
        help="Preview evolution proposals without applying registry mutations",
    )
    evolve_preview.add_argument("--write", action="store_true", help="Write preview report to workflow/ai_evolution.json")
    evolve_preview.set_defaults(func=cmd_evolve_preview)

    expand = sub.add_parser(
        "expand",
        help="Propose deterministic feature expansion opportunities",
    )
    expand.add_argument("--target", help="Limit expansion proposal output to one proposed slug")
    expand.add_argument("--apply", action="store_true", help="Apply expansion proposals to registry")
    expand.add_argument("--approve-expansion", action="store_true", help="Approve baseline expansion proposals")
    expand.add_argument("--approve-semantic", action="store_true", help="Approve semantic expansion proposals")
    expand.add_argument("--approve-structural", action="store_true", help="Approve structural integration proposals")
    expand.add_argument("--approve-sync", action="store_true", help="Approve sync-impacting expansion proposals")
    expand.set_defaults(func=cmd_expand)

    expand_all = sub.add_parser(
        "expand-all",
        help="Propose deterministic expansion opportunities across all features",
    )
    expand_all.add_argument("--apply", action="store_true", help="Apply expansion proposals to registry")
    expand_all.add_argument("--approve-expansion", action="store_true", help="Approve baseline expansion proposals")
    expand_all.add_argument("--approve-semantic", action="store_true", help="Approve semantic expansion proposals")
    expand_all.add_argument("--approve-structural", action="store_true", help="Approve structural integration proposals")
    expand_all.add_argument("--approve-sync", action="store_true", help="Approve sync-impacting expansion proposals")
    expand_all.set_defaults(func=cmd_expand_all)

    expand_preview = sub.add_parser(
        "expand-preview",
        help="Preview expansion proposals without applying registry mutations",
    )
    expand_preview.add_argument("--write", action="store_true", help="Write preview report to workflow/ai_expansion.json")
    expand_preview.set_defaults(func=cmd_expand_preview)

    refactor_feature = sub.add_parser(
        "refactor-feature",
        help="Analyze one feature and propose deterministic semantic refactors",
    )
    refactor_feature.add_argument("--feature", required=True, help="Feature slug to refactor")
    refactor_feature.add_argument("--apply", action="store_true", help="Apply accepted refactor proposals to registry")
    refactor_feature.add_argument("--approve-refactor", action="store_true", help="Approve baseline refactor proposals")
    refactor_feature.add_argument("--approve-semantic", action="store_true", help="Approve semantic metadata refactors")
    refactor_feature.add_argument("--approve-structural", action="store_true", help="Approve ERD/sequence structural refactors")
    refactor_feature.add_argument("--approve-sync", action="store_true", help="Approve UI/component sync-affecting refactors")
    refactor_feature.set_defaults(func=cmd_refactor_feature)

    refactor_all = sub.add_parser(
        "refactor-all",
        help="Analyze all features and propose deterministic semantic refactors",
    )
    refactor_all.add_argument("--apply", action="store_true", help="Apply accepted refactor proposals to registry")
    refactor_all.add_argument("--approve-refactor", action="store_true", help="Approve baseline refactor proposals")
    refactor_all.add_argument("--approve-semantic", action="store_true", help="Approve semantic metadata refactors")
    refactor_all.add_argument("--approve-structural", action="store_true", help="Approve ERD/sequence structural refactors")
    refactor_all.add_argument("--approve-sync", action="store_true", help="Approve UI/component sync-affecting refactors")
    refactor_all.set_defaults(func=cmd_refactor_all)

    refactor_preview = sub.add_parser(
        "refactor-preview",
        help="Preview semantic refactor proposals without applying registry mutations",
    )
    refactor_preview.add_argument("--write", action="store_true", help="Write preview report to workflow/ai_refactor.json")
    refactor_preview.set_defaults(func=cmd_refactor_preview)

    improve_feature = sub.add_parser(
        "improve-feature",
        help="Run a unified semantic improvement cycle for one feature",
    )
    improve_feature.add_argument("--feature", required=True, help="Feature slug for improvement cycle")
    improve_feature.add_argument("--apply", action="store_true", help="Apply approved cycle plan to registry")
    improve_feature.add_argument("--approve-evolution", action="store_true", help="Approve evolution proposals")
    improve_feature.add_argument("--approve-expansion", action="store_true", help="Approve expansion proposals")
    improve_feature.add_argument("--approve-refactor", action="store_true", help="Approve refactor proposals")
    improve_feature.add_argument("--approve-semantic", action="store_true", help="Approve semantic-impacting proposals")
    improve_feature.add_argument("--approve-structural", action="store_true", help="Approve structural-impacting proposals")
    improve_feature.add_argument("--approve-sync", action="store_true", help="Approve sync-impacting proposals")
    improve_feature.set_defaults(func=cmd_improve_feature)

    improve_all = sub.add_parser(
        "improve-all",
        help="Run a unified semantic improvement cycle across all features",
    )
    improve_all.add_argument("--apply", action="store_true", help="Apply approved cycle plan to registry")
    improve_all.add_argument("--approve-evolution", action="store_true", help="Approve evolution proposals")
    improve_all.add_argument("--approve-expansion", action="store_true", help="Approve expansion proposals")
    improve_all.add_argument("--approve-refactor", action="store_true", help="Approve refactor proposals")
    improve_all.add_argument("--approve-semantic", action="store_true", help="Approve semantic-impacting proposals")
    improve_all.add_argument("--approve-structural", action="store_true", help="Approve structural-impacting proposals")
    improve_all.add_argument("--approve-sync", action="store_true", help="Approve sync-impacting proposals")
    improve_all.add_argument(
        "--profile",
        choices=["standard", "quarterly", "annual"],
        default="standard",
        help="Output profile for cycle plan artifact naming",
    )
    improve_all.set_defaults(func=cmd_improve_all)

    improve_preview = sub.add_parser(
        "improve-preview",
        help="Preview unified semantic improvement cycle plan without applying mutations",
    )
    improve_preview.add_argument("--write", action="store_true", help="Write preview plan to workflow/ai_cycle.json")
    improve_preview.set_defaults(func=cmd_improve_preview)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
