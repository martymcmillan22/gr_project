from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .ai_native import build_ai_context_bundle, write_json_file
from .release_notes import build_release_notes, write_release_notes
from .semantic_conflicts import build_autofix_plan, build_conflict_report
from .semantic_drift import build_drift_report
from .semantic_infer import INFERENCE_CONFIDENCE_DEFAULT, build_inference_report, evaluate_inference_policy
from .semantic_propagation import propagate_registry_semantics
from .sync_erd import sync_erd_to_backend_model_stub
from .sync_sequence import sync_sequence_to_backend_logic_stub
from .sync_ui_component import sync_ui_component_to_design_system
from .sync_ui_template import sync_ui_template_to_react_page
from .validate import validate_registry_shape
from .versioning import bump_all_versions, get_version_report, load_version_state, save_version_state
from .visualize import write_feature_visualization, write_global_visualizations
from validation.suite import run_workflow_validation


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sync_feature(feature: dict[str, Any], workflow_root: Path, repo_root: Path) -> dict[str, str]:
    paths = feature.get("paths", {})

    erd_out = sync_erd_to_backend_model_stub(
        workflow_root / str(paths.get("erd", "")),
        str(feature.get("slug", "")),
        str(feature.get("mlas_tier", "")),
        repo_root,
    )
    seq_out = sync_sequence_to_backend_logic_stub(
        workflow_root / str(paths.get("sequence", "")),
        str(feature.get("slug", "")),
        str(feature.get("semantic_intent", "")),
        str(feature.get("propagation", {}).get("btif_route", "")),
        repo_root,
    )
    template_out = sync_ui_template_to_react_page(
        workflow_root / str(paths.get("ui_template", "")),
        str(feature.get("slug", "")),
        feature.get("semantic_tags", []),
        repo_root,
    )
    component_out = sync_ui_component_to_design_system(
        workflow_root / str(paths.get("ui_component", "")),
        str(feature.get("slug", "")),
        repo_root,
    )
    return {
        "erd_backend_models": str(Path(erd_out).relative_to(repo_root)),
        "sequence_backend_logic": str(Path(seq_out).relative_to(repo_root)),
        "ui_template_react_page": str(Path(template_out).relative_to(repo_root)),
        "ui_component_design_system": str(Path(component_out).relative_to(repo_root)),
    }


def append_semantic_changelog(path: Path, version: str, semantic_context: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"## {version} - {_utc_now()}",
        "",
        "### Semantic Rule Changes",
        "",
    ]
    for rule in semantic_context.get("drift_rules", []):
        lines.append(f"- drift: {rule}")
    for rule in semantic_context.get("inference_rules", []):
        lines.append(f"- inference: {rule}")
    for rule in semantic_context.get("conflict_rules", []):
        lines.append(f"- conflict: {rule}")

    lines.extend([
        "",
        "### MLAS Tier Changes",
        "",
    ])
    for row in semantic_context.get("mlas_tier_definitions", []):
        lines.append(f"- {row.get('name', '')}")

    lines.extend([
        "",
        "### BTIF Routing Changes",
        "",
    ])
    for cls in semantic_context.get("btif_routing_definitions", {}).get("known_classes", []):
        lines.append(f"- {cls}")

    lines.extend([
        "",
        "### Ontology Updates",
        "",
    ])
    for tag in semantic_context.get("tag_ontology", []):
        lines.append(f"- {tag}")

    lines.extend([
        "",
        "### Threshold And Safety Gates",
        "",
        f"- confidence_thresholds: {semantic_context.get('confidence_thresholds', {})}",
        f"- autofix_safety_gates: {semantic_context.get('autofix_safety_gates', {})}",
        "",
    ])

    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = "# Semantic Changelog\n\n"
    path.write_text(existing + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return path.as_posix()


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _governance_diff(previous_context: dict[str, Any], current_context: dict[str, Any]) -> dict[str, Any]:
    prev_lineage = {item.get("slug"): item for item in previous_context.get("semantic_lineage", []) if item.get("slug")}
    curr_lineage = {item.get("slug"): item for item in current_context.get("semantic_lineage", []) if item.get("slug")}

    mlas_changes: list[dict[str, str]] = []
    btif_changes: list[dict[str, str]] = []
    intent_changes: list[dict[str, str]] = []

    for slug, curr in curr_lineage.items():
        prev = prev_lineage.get(slug)
        if not prev:
            continue
        prev_mlas = str(prev.get("mlas", {}).get("mlas_tier", ""))
        curr_mlas = str(curr.get("mlas", {}).get("mlas_tier", ""))
        if prev_mlas and curr_mlas and prev_mlas != curr_mlas:
            mlas_changes.append({"slug": slug, "from": prev_mlas, "to": curr_mlas})

        prev_intent = str(prev.get("mlas", {}).get("semantic_intent", ""))
        curr_intent = str(curr.get("mlas", {}).get("semantic_intent", ""))
        if prev_intent and curr_intent and prev_intent != curr_intent:
            intent_changes.append({"slug": slug, "from": prev_intent, "to": curr_intent})

        prev_route = str(prev.get("btif_route", ""))
        curr_route = str(curr.get("btif_route", ""))
        if prev_route and curr_route and prev_route != curr_route:
            btif_changes.append({"slug": slug, "from": prev_route, "to": curr_route})

    prev_tags = set(previous_context.get("tag_ontology", []))
    curr_tags = set(current_context.get("tag_ontology", []))
    tag_delta = {
        "added": sorted(curr_tags - prev_tags),
        "removed": sorted(prev_tags - curr_tags),
    }

    has_changes = bool(mlas_changes or btif_changes or intent_changes or tag_delta["added"] or tag_delta["removed"])
    return {
        "mlas_tier_changes": mlas_changes,
        "btif_route_changes": btif_changes,
        "semantic_intent_changes": intent_changes,
        "tag_ontology_changes": tag_delta,
        "requires_approval": has_changes,
    }


def run_release_pipeline(
    workflow_root: Path,
    registry_path: Path,
    version_path: Path,
    semantic_changelog_path: Path,
    release_notes_path: Path,
    ai_hints_path: Path,
    ai_navigation_path: Path,
    semantic_context_path: Path,
    governance_policy_path: Path,
    bump_part: str,
    enforce_confidence: bool,
    min_confidence: float,
    approve_semantic_changes: bool,
) -> tuple[int, dict[str, Any]]:
    from .registry import load_registry, save_registry

    registry = load_registry(registry_path)
    version_state = load_version_state(version_path)
    repo_root = workflow_root.parent

    governance_policy = _load_json_if_exists(governance_policy_path)
    previous_semantic_context = _load_json_if_exists(semantic_context_path)

    drift_report = build_drift_report(registry, workflow_root, repo_root)
    drift_count = sum(item.get("drift_count", 0) for item in drift_report.get("features", {}).values())

    inference_report = build_inference_report(registry, workflow_root)
    inference_policy = evaluate_inference_policy(inference_report, min_confidence)

    conflict_report = build_conflict_report(registry, repo_root)
    autofix_plan = build_autofix_plan(conflict_report)
    conflict_count = sum(item.get("conflict_count", 0) for item in conflict_report.get("features", {}).values())

    shape_errors = validate_registry_shape(registry)
    suite_errors = run_workflow_validation(workflow_root, registry)

    validation_checks = {
        "semantic_drift_passed": drift_count == 0,
        "semantic_infer_passed": (inference_policy.get("passes", False) if enforce_confidence else True),
        "semantic_resolve_passed": conflict_count == 0,
        "validate_suite_passed": not (shape_errors or suite_errors),
    }

    errors: list[str] = []
    if drift_count > 0:
        errors.append(f"semantic-drift failed with {drift_count} drifts")
    if enforce_confidence and not inference_policy.get("passes", False):
        errors.append("semantic-infer failed confidence policy")
    if conflict_count > 0:
        errors.append(f"semantic-resolve found {conflict_count} conflicts")
    if shape_errors or suite_errors:
        errors.extend(shape_errors + suite_errors)

    if errors:
        return 1, {
            "status": "failed",
            "errors": errors,
            "drift": drift_report,
            "inference": {"report": inference_report, "policy": inference_policy},
            "conflicts": {"report": conflict_report, "autofix_plan": autofix_plan},
            "validation_checks": validation_checks,
        }

    feature_outputs: dict[str, str] = {}
    sync_results: dict[str, dict[str, str]] = {}
    for feature in registry.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue
        feature_outputs[slug] = write_feature_visualization(feature, workflow_root)
        sync_results[slug] = _sync_feature(feature, workflow_root, repo_root)

    global_outputs = write_global_visualizations(registry, workflow_root)
    propagate_registry_semantics(registry, sync_results)
    save_registry(registry_path, registry)

    ai_bundle = build_ai_context_bundle(registry, workflow_root)
    governance_delta = _governance_diff(previous_semantic_context, ai_bundle["semantic_context"])
    if governance_delta.get("requires_approval") and not approve_semantic_changes:
        return 1, {
            "status": "failed",
            "errors": ["semantic governance approval required for MLAS/BTIF/intent/tag ontology changes"],
            "governance_policy": governance_policy,
            "governance_delta": governance_delta,
            "hint": "rerun release with --approve-semantic-changes after review",
        }

    write_json_file(ai_hints_path, ai_bundle["ai_hints"])
    write_json_file(ai_navigation_path, ai_bundle["ai_navigation"])
    write_json_file(semantic_context_path, ai_bundle["semantic_context"])

    bump_result = bump_all_versions(version_state, bump_part)
    save_version_state(version_path, version_state)
    append_semantic_changelog(semantic_changelog_path, version_state.get("workflow_engine_version", ""), ai_bundle["semantic_context"])

    validation_checks.update(
        {
            "visualize_all_passed": bool(global_outputs),
            "sync_all_passed": len(sync_results) == len([f for f in registry.get("features", []) if str(f.get("slug", "")).strip()]),
            "ai_export_passed": True,
            "semantic_governance_passed": (not governance_delta.get("requires_approval") or approve_semantic_changes),
        }
    )

    notes = build_release_notes(
        version_state=version_state,
        registry=registry,
        semantic_context=ai_bundle["semantic_context"],
        ai_hints=ai_bundle["ai_hints"],
        ai_navigation=ai_bundle["ai_navigation"],
        validation_checks=validation_checks,
    )
    notes_path = write_release_notes(release_notes_path, notes)

    return 0, {
        "status": "released",
        "bump": {
            "part": bump_result.part,
            "previous": bump_result.previous,
            "current": bump_result.current,
        },
        "version": get_version_report(version_state),
        "visualizations": {"features": feature_outputs, "global": global_outputs},
        "sync": sync_results,
        "ai_export": {
            "ai_hints": ai_hints_path.as_posix(),
            "ai_navigation": ai_navigation_path.as_posix(),
            "semantic_context": semantic_context_path.as_posix(),
        },
        "semantic_changelog": semantic_changelog_path.as_posix(),
        "release_notes": notes_path,
        "validation_checks": validation_checks,
        "governance_policy": governance_policy,
        "governance_delta": governance_delta,
    }
