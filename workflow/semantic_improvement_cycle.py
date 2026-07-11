from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from feature_expansion import (
    apply_expansion_report_to_registry,
    build_expansion_report,
)
from semantic_evolution import (
    apply_evolution_report_to_registry,
    build_evolution_report,
)
from semantic_refactor import (
    apply_refactor_report_to_registry,
    build_refactor_report,
)


DEFAULT_CYCLE_GOVERNANCE = {
    "version": "1.0.0",
    "gates": {
        "cycle_apply_requires_engine_approvals": True,
        "cycle_apply_requires_cross_domain_approvals": True,
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_cycle_governance(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_CYCLE_GOVERNANCE
    payload = json.loads(path.read_text(encoding="utf-8"))
    gates = payload.get("gates", {}) if isinstance(payload, dict) else {}
    merged = DEFAULT_CYCLE_GOVERNANCE.copy()
    merged["gates"] = {**DEFAULT_CYCLE_GOVERNANCE["gates"], **gates}
    return merged


def _expansion_report_for_feature(expansion_report: dict[str, Any], feature_slug: str | None) -> dict[str, Any]:
    if not feature_slug:
        return expansion_report

    filtered = []
    for proposal in expansion_report.get("proposals", []):
        lineage = proposal.get("semantic_lineage", {})
        impact = proposal.get("dependency_graph_impact", {})
        sources = lineage.get("source_features", [])
        targets = impact.get("integration_targets", [])
        if feature_slug in sources or feature_slug in targets:
            filtered.append(proposal)

    return {
        "generated_at": expansion_report.get("generated_at"),
        "target": feature_slug,
        "proposal_count": len(filtered),
        "proposals": filtered,
    }


def _feature_summaries(
    evolution_report: dict[str, Any],
    expansion_report: dict[str, Any],
    refactor_report: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}

    for feature in evolution_report.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue
        rows.setdefault(slug, {"feature": slug, "evolution": 0, "expansion": 0, "refactor": 0, "total": 0})
        rows[slug]["evolution"] += int(feature.get("proposal_count", 0))

    for feature in refactor_report.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue
        rows.setdefault(slug, {"feature": slug, "evolution": 0, "expansion": 0, "refactor": 0, "total": 0})
        rows[slug]["refactor"] += int(feature.get("proposal_count", 0))

    for proposal in expansion_report.get("proposals", []):
        lineage = proposal.get("semantic_lineage", {})
        sources = lineage.get("source_features", []) if isinstance(lineage, dict) else []
        if not sources:
            continue
        for slug in sources:
            if not isinstance(slug, str) or not slug:
                continue
            rows.setdefault(slug, {"feature": slug, "evolution": 0, "expansion": 0, "refactor": 0, "total": 0})
            rows[slug]["expansion"] += 1

    out = []
    for slug in sorted(rows):
        row = rows[slug]
        row["total"] = int(row["evolution"]) + int(row["expansion"]) + int(row["refactor"])
        out.append(row)
    return out


def _aggregated_proposals(
    evolution_report: dict[str, Any],
    expansion_report: dict[str, Any],
    refactor_report: dict[str, Any],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []

    for feature in evolution_report.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        for proposal in feature.get("proposals", []):
            category = proposal.get("category")
            structural_impact = "medium" if category in {"erd", "sequence"} else "low"
            merged.append(
                {
                    "engine": "evolution",
                    "feature": slug,
                    "category": category,
                    "target": proposal.get("target"),
                    "confidence": proposal.get("confidence"),
                    "rationale": proposal.get("rationale"),
                    "governance_requirements": proposal.get("governance_requirements", []),
                    "semantic_impact": proposal.get("semantic_impact"),
                    "structural_impact": structural_impact,
                }
            )

    for proposal in expansion_report.get("proposals", []):
        lineage = proposal.get("semantic_lineage", {})
        sources = lineage.get("source_features", []) if isinstance(lineage, dict) else []
        merged.append(
            {
                "engine": "expansion",
                "feature": sources[0] if sources else "all",
                "category": proposal.get("category"),
                "target": proposal.get("proposed_feature", {}).get("slug"),
                "confidence": proposal.get("confidence"),
                "rationale": proposal.get("rationale"),
                "governance_requirements": proposal.get("governance_requirements", []),
                "semantic_impact": "high",
                "structural_impact": "high",
            }
        )

    for feature in refactor_report.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        for proposal in feature.get("proposals", []):
            merged.append(
                {
                    "engine": "refactor",
                    "feature": slug,
                    "category": proposal.get("category"),
                    "target": proposal.get("target"),
                    "confidence": proposal.get("confidence"),
                    "rationale": proposal.get("rationale"),
                    "governance_requirements": proposal.get("governance_requirements", []),
                    "semantic_impact": proposal.get("semantic_impact"),
                    "structural_impact": proposal.get("structural_impact"),
                }
            )

    return merged


def build_improvement_cycle_plan(
    registry: dict[str, Any],
    workflow_root: Path,
    governance_policy: dict[str, Any],
    feature_slug: str | None = None,
) -> dict[str, Any]:
    evolution_report = build_evolution_report(registry, workflow_root, governance_policy, feature_slug=feature_slug)
    expansion_raw = build_expansion_report(registry, governance_policy)
    expansion_report = _expansion_report_for_feature(expansion_raw, feature_slug)
    refactor_report = build_refactor_report(registry, workflow_root, governance_policy, feature_slug=feature_slug)

    aggregated = _aggregated_proposals(evolution_report, expansion_report, refactor_report)
    summaries = _feature_summaries(evolution_report, expansion_report, refactor_report)

    return {
        "generated_at": _utc_now(),
        "target": feature_slug or "all",
        "engine_order": ["evolution", "expansion", "refactor"],
        "reports": {
            "evolution": evolution_report,
            "expansion": expansion_report,
            "refactor": refactor_report,
        },
        "proposal_count": len(aggregated),
        "feature_summaries": summaries,
        "aggregated_proposals": aggregated,
    }


def required_approvals_for_cycle(plan: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    required: set[str] = set()
    gates = policy.get("gates", {}) if isinstance(policy, dict) else {}

    if gates.get("cycle_apply_requires_engine_approvals", True):
        if plan.get("reports", {}).get("evolution", {}).get("proposal_count", 0) > 0:
            required.add("evolution_approval")
        if plan.get("reports", {}).get("expansion", {}).get("proposal_count", 0) > 0:
            required.add("expansion_approval")
        if plan.get("reports", {}).get("refactor", {}).get("proposal_count", 0) > 0:
            required.add("refactor_approval")

    for row in plan.get("aggregated_proposals", []):
        for gate in row.get("governance_requirements", []):
            required.add(str(gate))

    if gates.get("cycle_apply_requires_cross_domain_approvals", True) and plan.get("proposal_count", 0) > 0:
        required.update(["semantic_approval", "structural_approval", "sync_approval"])

    return sorted(required)


def validate_cycle_approvals(plan: dict[str, Any], approvals: dict[str, bool], policy: dict[str, Any]) -> list[str]:
    required = required_approvals_for_cycle(plan, policy)
    return [gate for gate in required if not approvals.get(gate, False)]


def apply_improvement_cycle_plan(registry: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    reports = plan.get("reports", {})
    evolution_report = reports.get("evolution", {})
    expansion_report = reports.get("expansion", {})
    refactor_report = reports.get("refactor", {})

    apply_evolution_report_to_registry(registry, evolution_report)
    apply_expansion_report_to_registry(registry, expansion_report, create_scaffolds=True)
    apply_refactor_report_to_registry(registry, refactor_report)

    registry.setdefault("improvement_cycle", {})
    registry["improvement_cycle"]["last_updated"] = plan.get("generated_at")
    registry["improvement_cycle"]["proposal_count"] = plan.get("proposal_count", 0)
    registry["improvement_cycle"]["engine_order"] = plan.get("engine_order", [])
    return registry
