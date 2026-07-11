from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from _engine.btif_router import assign_btif_route
from _engine.mlas_integration import normalize_semantic_tags


DEFAULT_LONG_TERM_GOVERNANCE = {
    "version": "1.0.0",
    "gates": {
        "evolution_proposals_require_approval": True,
        "mlas_btif_evolution_requires_semantic_approval": True,
        "tag_ontology_evolution_requires_semantic_approval": True,
        "erd_sequence_refactors_require_structural_approval": True,
        "ui_component_refactors_require_sync_approval": True,
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_long_term_governance(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_LONG_TERM_GOVERNANCE
    return json.loads(path.read_text(encoding="utf-8"))


def _proposal(
    category: str,
    target: str,
    change: str,
    rationale: str,
    confidence: float,
    semantic_impact: str,
    governance_requirements: list[str],
) -> dict[str, Any]:
    return {
        "category": category,
        "target": target,
        "proposed_change": change,
        "rationale": rationale,
        "confidence": confidence,
        "semantic_impact": semantic_impact,
        "governance_requirements": governance_requirements,
    }


def _category_requirements(category: str, policy: dict[str, Any]) -> list[str]:
    gates = policy.get("gates", {}) if isinstance(policy, dict) else {}
    requirements: list[str] = []
    if gates.get("evolution_proposals_require_approval", True):
        requirements.append("evolution_approval")

    if category in {"mlas_btif_lineage", "semantic_metadata"} and gates.get(
        "mlas_btif_evolution_requires_semantic_approval", True
    ):
        requirements.append("semantic_approval")

    if category == "tag_ontology" and gates.get("tag_ontology_evolution_requires_semantic_approval", True):
        requirements.append("semantic_approval")

    if category in {"erd", "sequence"} and gates.get("erd_sequence_refactors_require_structural_approval", True):
        requirements.append("structural_approval")

    if category in {"ui_template", "component"} and gates.get("ui_component_refactors_require_sync_approval", True):
        requirements.append("sync_approval")

    return sorted(set(requirements))


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def analyze_feature_evolution(
    feature: dict[str, Any],
    workflow_root: Path,
    registry: dict[str, Any],
    governance_policy: dict[str, Any],
) -> dict[str, Any]:
    slug = str(feature.get("slug", "")).strip()
    paths = feature.get("paths", {})
    proposals: list[dict[str, Any]] = []

    erd_text = _read(workflow_root / str(paths.get("erd", "")))
    if erd_text and "PK" not in erd_text:
        proposals.append(
            _proposal(
                category="erd",
                target=str(paths.get("erd", "")),
                change="Add explicit PK annotations to core entities.",
                rationale="ERD appears to omit primary key annotations in entity blocks.",
                confidence=0.86,
                semantic_impact="medium",
                governance_requirements=_category_requirements("erd", governance_policy),
            )
        )
    if erd_text and not any(token in erd_text for token in ["||--", "}|", "o{"]):
        proposals.append(
            _proposal(
                category="erd",
                target=str(paths.get("erd", "")),
                change="Add explicit relationship notation between entities.",
                rationale="No relationship markers detected in ERD content.",
                confidence=0.74,
                semantic_impact="low",
                governance_requirements=_category_requirements("erd", governance_policy),
            )
        )

    sequence_text = _read(workflow_root / str(paths.get("sequence", "")))
    if sequence_text and "participant" not in sequence_text:
        proposals.append(
            _proposal(
                category="sequence",
                target=str(paths.get("sequence", "")),
                change="Declare explicit participants for sequence readability.",
                rationale="Sequence diagram lacks participant declarations.",
                confidence=0.88,
                semantic_impact="low",
                governance_requirements=_category_requirements("sequence", governance_policy),
            )
        )
    if sequence_text and not any(token in sequence_text for token in ["->>", "-->>", "->"]):
        proposals.append(
            _proposal(
                category="sequence",
                target=str(paths.get("sequence", "")),
                change="Add request/response arrows for execution flow clarity.",
                rationale="Sequence diagram appears to lack message arrows.",
                confidence=0.82,
                semantic_impact="medium",
                governance_requirements=_category_requirements("sequence", governance_policy),
            )
        )

    template_text = _read(workflow_root / str(paths.get("ui_template", "")))
    if template_text and "slug:" not in template_text:
        proposals.append(
            _proposal(
                category="ui_template",
                target=str(paths.get("ui_template", "")),
                change="Add slug metadata line to template scaffold.",
                rationale="Template metadata block is missing slug for deterministic tracking.",
                confidence=0.9,
                semantic_impact="low",
                governance_requirements=_category_requirements("ui_template", governance_policy),
            )
        )

    component_text = _read(workflow_root / str(paths.get("ui_component", "")))
    if component_text and "slug:" not in component_text:
        proposals.append(
            _proposal(
                category="component",
                target=str(paths.get("ui_component", "")),
                change="Add slug metadata line to component scaffold.",
                rationale="Component spec metadata is missing slug field.",
                confidence=0.9,
                semantic_impact="low",
                governance_requirements=_category_requirements("component", governance_policy),
            )
        )

    tags = feature.get("semantic_tags", [])
    normalized = normalize_semantic_tags(tags)
    if normalized != tags:
        proposals.append(
            _proposal(
                category="semantic_metadata",
                target=f"registry.features[{slug}].semantic_tags",
                change="Normalize semantic_tags to lowercase kebab-case unique ordering.",
                rationale="semantic_tags diverge from canonical normalized form.",
                confidence=0.96,
                semantic_impact="medium",
                governance_requirements=_category_requirements("semantic_metadata", governance_policy),
            )
        )

    expected_route = assign_btif_route(feature)
    observed_route = str(feature.get("propagation", {}).get("btif_route", ""))
    if observed_route and observed_route != expected_route:
        proposals.append(
            _proposal(
                category="mlas_btif_lineage",
                target=f"registry.features[{slug}].propagation.btif_route",
                change="Align stored BTIF route with deterministic assignment.",
                rationale="Observed BTIF route diverges from deterministic route computation.",
                confidence=0.94,
                semantic_impact="high",
                governance_requirements=_category_requirements("mlas_btif_lineage", governance_policy),
            )
        )

    if not str(feature.get("feature_lineage", "")).strip():
        proposals.append(
            _proposal(
                category="mlas_btif_lineage",
                target=f"registry.features[{slug}].feature_lineage",
                change=f"Set feature_lineage to workflow/{slug}.",
                rationale="Feature lineage missing for semantic traceability.",
                confidence=0.92,
                semantic_impact="medium",
                governance_requirements=_category_requirements("mlas_btif_lineage", governance_policy),
            )
        )

    all_tags: list[str] = []
    for row in registry.get("features", []):
        all_tags.extend(normalize_semantic_tags(row.get("semantic_tags", [])))
    counts = Counter(all_tags)
    stale = sorted([tag for tag in normalized if counts.get(tag, 0) == 1])
    if stale:
        proposals.append(
            _proposal(
                category="tag_ontology",
                target=f"registry.features[{slug}].semantic_tags",
                change=f"Review low-reuse tags for ontology alignment: {', '.join(stale)}",
                rationale="Tags appear only once across registry and may be stale or overly specific.",
                confidence=0.73,
                semantic_impact="low",
                governance_requirements=_category_requirements("tag_ontology", governance_policy),
            )
        )

    return {
        "slug": slug,
        "proposal_count": len(proposals),
        "proposals": proposals,
    }


def build_evolution_report(
    registry: dict[str, Any],
    workflow_root: Path,
    governance_policy: dict[str, Any],
    feature_slug: str | None = None,
) -> dict[str, Any]:
    rows = []
    for feature in registry.get("features", []):
        slug = str(feature.get("slug", "")).strip()
        if not slug:
            continue
        if feature_slug and slug != feature_slug:
            continue
        rows.append(analyze_feature_evolution(feature, workflow_root, registry, governance_policy))

    total = sum(row.get("proposal_count", 0) for row in rows)
    return {
        "generated_at": _utc_now(),
        "target": feature_slug or "all",
        "feature_count": len(rows),
        "proposal_count": total,
        "features": rows,
    }


def required_approvals_for_report(report: dict[str, Any]) -> list[str]:
    required: set[str] = set()
    for feature in report.get("features", []):
        for proposal in feature.get("proposals", []):
            for requirement in proposal.get("governance_requirements", []):
                required.add(str(requirement))
    return sorted(required)


def validate_evolution_approvals(report: dict[str, Any], approvals: dict[str, bool]) -> list[str]:
    required = required_approvals_for_report(report)
    missing = [item for item in required if not approvals.get(item, False)]
    return missing


def apply_evolution_report_to_registry(registry: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    feature_map = {
        str(feature.get("slug", "")).strip(): feature for feature in registry.get("features", []) if str(feature.get("slug", "")).strip()
    }
    for row in report.get("features", []):
        slug = str(row.get("slug", "")).strip()
        if slug not in feature_map:
            continue
        feature = feature_map[slug]
        evolution_block = feature.setdefault("evolution", {})
        evolution_block["last_updated"] = report.get("generated_at")
        evolution_block["proposal_count"] = row.get("proposal_count", 0)
        evolution_block["proposals"] = row.get("proposals", [])
    return registry
