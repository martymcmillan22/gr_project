from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from _engine.btif_router import assign_btif_route
from _engine.mlas_integration import normalize_semantic_tags


DEFAULT_REFACTOR_GOVERNANCE = {
    "version": "1.0.0",
    "gates": {
        "refactor_proposals_require_approval": True,
        "erd_sequence_refactors_require_structural_approval": True,
        "ui_component_refactors_require_sync_approval": True,
        "semantic_metadata_refactors_require_semantic_approval": True,
        "mlas_btif_lineage_refactors_require_semantic_approval": True,
        "tag_ontology_refactors_require_semantic_approval": True,
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_refactor_governance(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_REFACTOR_GOVERNANCE
    payload = json.loads(path.read_text(encoding="utf-8"))
    gates = payload.get("gates", {}) if isinstance(payload, dict) else {}
    merged = DEFAULT_REFACTOR_GOVERNANCE.copy()
    merged["gates"] = {**DEFAULT_REFACTOR_GOVERNANCE["gates"], **gates}
    return merged


def _category_requirements(category: str, policy: dict[str, Any]) -> list[str]:
    gates = policy.get("gates", {}) if isinstance(policy, dict) else {}
    requirements: list[str] = []

    if gates.get("refactor_proposals_require_approval", True):
        requirements.append("refactor_approval")

    if category in {"erd", "sequence"} and gates.get("erd_sequence_refactors_require_structural_approval", True):
        requirements.append("structural_approval")

    if category in {"ui_template", "component"} and gates.get("ui_component_refactors_require_sync_approval", True):
        requirements.append("sync_approval")

    if category == "semantic_metadata" and gates.get("semantic_metadata_refactors_require_semantic_approval", True):
        requirements.append("semantic_approval")

    if category == "mlas_btif_lineage" and gates.get("mlas_btif_lineage_refactors_require_semantic_approval", True):
        requirements.append("semantic_approval")

    if category == "tag_ontology" and gates.get("tag_ontology_refactors_require_semantic_approval", True):
        requirements.append("semantic_approval")

    return sorted(set(requirements))


def _proposal(
    *,
    category: str,
    target: str,
    proposed_refactor: dict[str, Any],
    rationale: str,
    confidence: float,
    semantic_impact: str,
    structural_impact: str,
    governance_requirements: list[str],
) -> dict[str, Any]:
    return {
        "category": category,
        "target": target,
        "proposed_refactor": proposed_refactor,
        "rationale": rationale,
        "confidence": confidence,
        "semantic_impact": semantic_impact,
        "structural_impact": structural_impact,
        "governance_requirements": governance_requirements,
    }


def _existing_slugs(registry: dict[str, Any]) -> list[str]:
    slugs = [str(feature.get("slug", "")).strip() for feature in registry.get("features", [])]
    return sorted([slug for slug in slugs if slug])


def analyze_feature_refactor(
    feature: dict[str, Any],
    workflow_root: Path,
    registry: dict[str, Any],
    governance_policy: dict[str, Any],
) -> dict[str, Any]:
    slug = str(feature.get("slug", "")).strip()
    paths = feature.get("paths", {})
    proposals: list[dict[str, Any]] = []

    erd_rel = str(paths.get("erd", ""))
    erd_text = _read(workflow_root / erd_rel)
    if erd_text:
        entities = re.findall(r"^\s*([A-Z0-9_]+)\s*\{", erd_text, flags=re.MULTILINE)
        duplicates = sorted([name for name, count in Counter(entities).items() if count > 1])
        if duplicates:
            proposals.append(
                _proposal(
                    category="erd",
                    target=erd_rel,
                    proposed_refactor={
                        "action": "merge_duplicate_entities",
                        "entities": duplicates,
                    },
                    rationale="ERD contains duplicate entity blocks that should be normalized.",
                    confidence=0.88,
                    semantic_impact="medium",
                    structural_impact="high",
                    governance_requirements=_category_requirements("erd", governance_policy),
                )
            )

        required_metadata = [f"%% slug: {slug}", "%% mlas_tier:", "%% btif_classification:"]
        if not all(token in erd_text for token in required_metadata):
            proposals.append(
                _proposal(
                    category="erd",
                    target=erd_rel,
                    proposed_refactor={
                        "action": "normalize_header_metadata",
                        "required_tokens": required_metadata,
                    },
                    rationale="ERD header metadata is incomplete for deterministic traceability.",
                    confidence=0.8,
                    semantic_impact="low",
                    structural_impact="medium",
                    governance_requirements=_category_requirements("erd", governance_policy),
                )
            )

    sequence_rel = str(paths.get("sequence", ""))
    sequence_text = _read(workflow_root / sequence_rel)
    if sequence_text:
        message_lines = [line.strip() for line in sequence_text.splitlines() if "->" in line]
        duplicate_messages = [
            line for line, count in Counter(message_lines).items() if line and count > 1
        ]
        if duplicate_messages:
            proposals.append(
                _proposal(
                    category="sequence",
                    target=sequence_rel,
                    proposed_refactor={
                        "action": "deduplicate_messages",
                        "messages": sorted(duplicate_messages),
                    },
                    rationale="Sequence flow has duplicated message edges that reduce clarity.",
                    confidence=0.83,
                    semantic_impact="low",
                    structural_impact="medium",
                    governance_requirements=_category_requirements("sequence", governance_policy),
                )
            )

        if re.search(r"\b(dead|unused|todo)\b", sequence_text, flags=re.IGNORECASE):
            proposals.append(
                _proposal(
                    category="sequence",
                    target=sequence_rel,
                    proposed_refactor={"action": "remove_dead_paths"},
                    rationale="Sequence flow includes dead or TODO paths that should be removed or resolved.",
                    confidence=0.76,
                    semantic_impact="medium",
                    structural_impact="medium",
                    governance_requirements=_category_requirements("sequence", governance_policy),
                )
            )

    template_rel = str(paths.get("ui_template", ""))
    template_text = _read(workflow_root / template_rel)
    if template_text:
        if "- slug:" not in template_text or "- mlas_tier:" not in template_text or "- btif_classification:" not in template_text:
            proposals.append(
                _proposal(
                    category="ui_template",
                    target=template_rel,
                    proposed_refactor={
                        "action": "normalize_template_metadata",
                        "required_fields": ["slug", "mlas_tier", "btif_classification"],
                    },
                    rationale="UI template metadata fields are inconsistent with deterministic scaffold keys.",
                    confidence=0.9,
                    semantic_impact="low",
                    structural_impact="medium",
                    governance_requirements=_category_requirements("ui_template", governance_policy),
                )
            )

    component_rel = str(paths.get("ui_component", ""))
    component_text = _read(workflow_root / component_rel)
    if component_text:
        if "- slug:" not in component_text or "- mlas_tier:" not in component_text or "- btif_classification:" not in component_text:
            proposals.append(
                _proposal(
                    category="component",
                    target=component_rel,
                    proposed_refactor={
                        "action": "normalize_component_metadata",
                        "required_fields": ["slug", "mlas_tier", "btif_classification"],
                    },
                    rationale="Component metadata fields are inconsistent with deterministic scaffold keys.",
                    confidence=0.9,
                    semantic_impact="low",
                    structural_impact="medium",
                    governance_requirements=_category_requirements("component", governance_policy),
                )
            )

    semantic_intent = str(feature.get("semantic_intent", "")).strip()
    if semantic_intent and (not semantic_intent[0].isupper() or "_" in semantic_intent or "-" in semantic_intent):
        normalized_intent = re.sub(r"[^A-Za-z0-9]+", " ", semantic_intent).title().replace(" ", "")
        proposals.append(
            _proposal(
                category="semantic_metadata",
                target=f"registry.features[{slug}].semantic_intent",
                proposed_refactor={
                    "action": "normalize_semantic_intent",
                    "from": semantic_intent,
                    "to": normalized_intent,
                },
                rationale="semantic_intent naming is not normalized to canonical PascalCase.",
                confidence=0.92,
                semantic_impact="high",
                structural_impact="low",
                governance_requirements=_category_requirements("semantic_metadata", governance_policy),
            )
        )

    tags = feature.get("semantic_tags", [])
    normalized_tags = normalize_semantic_tags(tags)
    if normalized_tags != tags:
        proposals.append(
            _proposal(
                category="semantic_metadata",
                target=f"registry.features[{slug}].semantic_tags",
                proposed_refactor={
                    "action": "normalize_tags",
                    "from": tags,
                    "to": normalized_tags,
                },
                rationale="semantic_tags are not normalized to canonical lowercase kebab-case unique ordering.",
                confidence=0.96,
                semantic_impact="medium",
                structural_impact="low",
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
                proposed_refactor={
                    "action": "realign_btif_route",
                    "from": observed_route,
                    "to": expected_route,
                },
                rationale="BTIF route diverges from deterministic route generation for current metadata.",
                confidence=0.94,
                semantic_impact="high",
                structural_impact="low",
                governance_requirements=_category_requirements("mlas_btif_lineage", governance_policy),
            )
        )

    if not str(feature.get("feature_lineage", "")).strip():
        proposals.append(
            _proposal(
                category="mlas_btif_lineage",
                target=f"registry.features[{slug}].feature_lineage",
                proposed_refactor={
                    "action": "set_feature_lineage",
                    "to": f"workflow/{slug}",
                },
                rationale="Feature lineage is missing and should be set for semantic traceability.",
                confidence=0.9,
                semantic_impact="medium",
                structural_impact="low",
                governance_requirements=_category_requirements("mlas_btif_lineage", governance_policy),
            )
        )

    all_tags: list[str] = []
    for row in registry.get("features", []):
        all_tags.extend(normalize_semantic_tags(row.get("semantic_tags", [])))
    tag_counts = Counter(all_tags)
    singleton_tags = sorted([tag for tag in normalized_tags if tag_counts.get(tag, 0) == 1])
    if singleton_tags:
        proposals.append(
            _proposal(
                category="tag_ontology",
                target=f"registry.features[{slug}].semantic_tags",
                proposed_refactor={
                    "action": "deprecate_or_merge_singleton_tags",
                    "tags": singleton_tags,
                },
                rationale="Tag ontology contains singleton tags that may indicate redundant or overly-specific vocabulary.",
                confidence=0.72,
                semantic_impact="medium",
                structural_impact="low",
                governance_requirements=_category_requirements("tag_ontology", governance_policy),
            )
        )

    return {
        "slug": slug,
        "proposal_count": len(proposals),
        "proposals": proposals,
    }


def build_refactor_report(
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
        rows.append(analyze_feature_refactor(feature, workflow_root, registry, governance_policy))

    total = sum(row.get("proposal_count", 0) for row in rows)
    return {
        "generated_at": _utc_now(),
        "target": feature_slug or "all",
        "feature_count": len(rows),
        "proposal_count": total,
        "features": rows,
    }


def required_approvals_for_refactor(report: dict[str, Any]) -> list[str]:
    required: set[str] = set()
    for feature in report.get("features", []):
        for proposal in feature.get("proposals", []):
            for requirement in proposal.get("governance_requirements", []):
                required.add(str(requirement))
    return sorted(required)


def validate_refactor_approvals(report: dict[str, Any], approvals: dict[str, bool]) -> list[str]:
    required = required_approvals_for_refactor(report)
    return [item for item in required if not approvals.get(item, False)]


def apply_refactor_report_to_registry(registry: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    feature_map = {
        str(feature.get("slug", "")).strip(): feature
        for feature in registry.get("features", [])
        if str(feature.get("slug", "")).strip()
    }

    for row in report.get("features", []):
        slug = str(row.get("slug", "")).strip()
        feature = feature_map.get(slug)
        if not feature:
            continue

        for proposal in row.get("proposals", []):
            category = str(proposal.get("category", ""))
            action = str(proposal.get("proposed_refactor", {}).get("action", ""))

            if category == "semantic_metadata" and action == "normalize_tags":
                feature["semantic_tags"] = normalize_semantic_tags(feature.get("semantic_tags", []))

            if category == "semantic_metadata" and action == "normalize_semantic_intent":
                to_intent = proposal.get("proposed_refactor", {}).get("to")
                if isinstance(to_intent, str) and to_intent:
                    feature["semantic_intent"] = to_intent

            if category == "mlas_btif_lineage" and action == "realign_btif_route":
                propagation = feature.setdefault("propagation", {})
                propagation["btif_route"] = assign_btif_route(feature)

            if category == "mlas_btif_lineage" and action == "set_feature_lineage":
                feature["feature_lineage"] = f"workflow/{slug}"

        refactor_block = feature.setdefault("refactor", {})
        refactor_block["last_updated"] = report.get("generated_at")
        refactor_block["proposal_count"] = row.get("proposal_count", 0)
        refactor_block["proposals"] = row.get("proposals", [])

    return registry
