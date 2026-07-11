from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from _engine.mlas_integration import normalize_semantic_tags
from _engine.scaffold import slugify


DEFAULT_EXPANSION_GOVERNANCE = {
    "version": "1.0.0",
    "gates": {
        "new_feature_proposals_require_approval": True,
        "new_semantic_intents_require_approval": True,
        "new_mlas_btif_patterns_require_approval": True,
        "new_tag_ontology_entries_require_approval": True,
        "cross_feature_integrations_require_approval": True,
        "multi_feature_bundles_require_approval": True,
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_expansion_governance(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_EXPANSION_GOVERNANCE
    payload = json.loads(path.read_text(encoding="utf-8"))
    gates = payload.get("gates", {}) if isinstance(payload, dict) else {}
    merged = DEFAULT_EXPANSION_GOVERNANCE.copy()
    merged["gates"] = {**DEFAULT_EXPANSION_GOVERNANCE["gates"], **gates}
    return merged


def _req(category: str, policy: dict[str, Any]) -> list[str]:
    gates = policy.get("gates", {}) if isinstance(policy, dict) else {}
    requirements = ["expansion_approval"]

    if category in {"new_semantic_intent"} and gates.get("new_semantic_intents_require_approval", True):
        requirements.append("semantic_approval")
    if category in {"new_mlas_btif_pattern"} and gates.get("new_mlas_btif_patterns_require_approval", True):
        requirements.append("semantic_approval")
    if category in {"new_tag_ontology_entry"} and gates.get("new_tag_ontology_entries_require_approval", True):
        requirements.append("semantic_approval")
    if category in {"cross_feature_integration"} and gates.get("cross_feature_integrations_require_approval", True):
        requirements.append("structural_approval")
    if category in {"multi_feature_bundle"} and gates.get("multi_feature_bundles_require_approval", True):
        requirements.append("sync_approval")

    return sorted(set(requirements))


def _proposal(
    category: str,
    proposed_feature: dict[str, Any],
    rationale: str,
    confidence: float,
    governance_requirements: list[str],
    semantic_lineage: dict[str, Any],
    dependency_graph_impact: dict[str, Any],
) -> dict[str, Any]:
    return {
        "category": category,
        "proposed_feature": proposed_feature,
        "rationale": rationale,
        "confidence": confidence,
        "governance_requirements": governance_requirements,
        "semantic_lineage": semantic_lineage,
        "dependency_graph_impact": dependency_graph_impact,
    }


def _existing_slugs(registry: dict[str, Any]) -> set[str]:
    return {
        str(feature.get("slug", "")).strip()
        for feature in registry.get("features", [])
        if str(feature.get("slug", "")).strip()
    }


def _existing_intents(registry: dict[str, Any]) -> set[str]:
    return {
        str(feature.get("semantic_intent", "")).strip()
        for feature in registry.get("features", [])
        if str(feature.get("semantic_intent", "")).strip()
    }


def _existing_mlas(registry: dict[str, Any]) -> set[str]:
    return {
        str(feature.get("mlas_tier", "")).strip()
        for feature in registry.get("features", [])
        if str(feature.get("mlas_tier", "")).strip()
    }


def _existing_btif(registry: dict[str, Any]) -> set[str]:
    return {
        str(feature.get("btif_classification", "")).strip()
        for feature in registry.get("features", [])
        if str(feature.get("btif_classification", "")).strip()
    }


def _suggest_semantic_gaps(registry: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    tags = []
    for feature in registry.get("features", []):
        tags.extend(normalize_semantic_tags(feature.get("semantic_tags", [])))
    counts = Counter(tags)

    has_lineage_tag = any(tag == "lineage" for tag in counts)
    if not has_lineage_tag:
        slug = "lineage-governance"
        proposed = {
            "name": "Lineage Governance",
            "slug": slug,
            "semantic_intent": "LineageGovernance",
            "mlas_tier": "Semantic Utility",
            "btif_classification": "GovernanceFlow",
            "semantic_tags": ["governance", "lineage", "semantic"],
            "bundle": "semantic-governance",
        }
        proposals.append(
            _proposal(
                category="new_feature",
                proposed_feature=proposed,
                rationale="Registry lacks lineage-focused governance coverage in tag ontology.",
                confidence=0.84,
                governance_requirements=_req("new_feature", policy),
                semantic_lineage={"derived_from": "registry semantic coverage gap", "source_features": sorted(_existing_slugs(registry))},
                dependency_graph_impact={"adds_node": slug, "integration_targets": sorted(_existing_slugs(registry))[:3]},
            )
        )

    if "ExpandAndIntegrate" not in _existing_intents(registry):
        slug = "workflow-expansion-hub"
        proposed = {
            "name": "Workflow Expansion Hub",
            "slug": slug,
            "semantic_intent": "ExpandAndIntegrate",
            "mlas_tier": "Semantic Utility",
            "btif_classification": "ExpansionFlow",
            "semantic_tags": ["expansion", "integration", "workflow"],
            "bundle": "semantic-expansion",
        }
        proposals.append(
            _proposal(
                category="new_semantic_intent",
                proposed_feature=proposed,
                rationale="No feature currently expresses expansion-intent workflow semantics.",
                confidence=0.89,
                governance_requirements=_req("new_semantic_intent", policy),
                semantic_lineage={"derived_from": "missing semantic intent", "source_features": sorted(_existing_slugs(registry))},
                dependency_graph_impact={"adds_node": slug, "integration_targets": sorted(_existing_slugs(registry))},
            )
        )

    if "ExpansionFlow" not in _existing_btif(registry):
        slug = "expansion-routing-bridge"
        proposed = {
            "name": "Expansion Routing Bridge",
            "slug": slug,
            "semantic_intent": "BridgeAndRoute",
            "mlas_tier": next(iter(_existing_mlas(registry)), "Semantic Utility"),
            "btif_classification": "ExpansionFlow",
            "semantic_tags": ["btif", "expansion", "routing"],
            "bundle": "semantic-expansion",
        }
        proposals.append(
            _proposal(
                category="new_mlas_btif_pattern",
                proposed_feature=proposed,
                rationale="BTIF expansion pattern absent in current registry classifications.",
                confidence=0.86,
                governance_requirements=_req("new_mlas_btif_pattern", policy),
                semantic_lineage={"derived_from": "btif class coverage gap", "source_features": sorted(_existing_slugs(registry))},
                dependency_graph_impact={"adds_node": slug, "integration_targets": sorted(_existing_slugs(registry))},
            )
        )

    low_reuse = sorted([tag for tag, count in counts.items() if count == 1])
    if low_reuse:
        slug = "ontology-normalization"
        proposed = {
            "name": "Ontology Normalization",
            "slug": slug,
            "semantic_intent": "NormalizeOntology",
            "mlas_tier": "Semantic Utility",
            "btif_classification": "GovernanceFlow",
            "semantic_tags": ["ontology", "semantic", "tags"],
            "bundle": "semantic-governance",
            "new_tag_candidates": low_reuse,
        }
        proposals.append(
            _proposal(
                category="new_tag_ontology_entry",
                proposed_feature=proposed,
                rationale="Detected low-reuse tag set suggesting ontology normalization opportunity.",
                confidence=0.72,
                governance_requirements=_req("new_tag_ontology_entry", policy),
                semantic_lineage={"derived_from": "tag frequency analysis", "source_features": sorted(_existing_slugs(registry))},
                dependency_graph_impact={"adds_node": slug, "integration_targets": sorted(_existing_slugs(registry))[:2]},
            )
        )

    return proposals


def _suggest_bundle_and_integration(registry: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    slugs = sorted(_existing_slugs(registry))
    if len(slugs) < 1:
        return proposals

    bundle_slug = "semantic-intake-expansion-bundle"
    bundle = {
        "name": "Semantic Intake Expansion Bundle",
        "slug": bundle_slug,
        "semantic_intent": "BundleAndCoordinate",
        "mlas_tier": "Semantic Utility",
        "btif_classification": "ExpansionFlow",
        "semantic_tags": ["bundle", "expansion", "intake"],
        "bundle_members": slugs,
    }
    proposals.append(
        _proposal(
            category="multi_feature_bundle",
            proposed_feature=bundle,
            rationale="Cross-feature bundle can coordinate registry-wide evolution and expansion proposals.",
            confidence=0.78,
            governance_requirements=_req("multi_feature_bundle", policy),
            semantic_lineage={"derived_from": "cross-feature composition", "source_features": slugs},
            dependency_graph_impact={"adds_node": bundle_slug, "integration_targets": slugs},
        )
    )

    if len(slugs) >= 1:
        integration_slug = "semantic-integration-orchestrator"
        integration = {
            "name": "Semantic Integration Orchestrator",
            "slug": integration_slug,
            "semantic_intent": "IntegrateAndOrchestrate",
            "mlas_tier": "Semantic Utility",
            "btif_classification": "IntegrationFlow",
            "semantic_tags": ["integration", "orchestration", "semantic"],
            "depends_on": slugs,
        }
        proposals.append(
            _proposal(
                category="cross_feature_integration",
                proposed_feature=integration,
                rationale="Cross-feature integration orchestrator can unify semantic propagation and expansion decisions.",
                confidence=0.81,
                governance_requirements=_req("cross_feature_integration", policy),
                semantic_lineage={"derived_from": "dependency graph integration opportunity", "source_features": slugs},
                dependency_graph_impact={"adds_node": integration_slug, "integration_targets": slugs},
            )
        )

    return proposals


def build_expansion_report(
    registry: dict[str, Any],
    governance_policy: dict[str, Any],
    target_slug: str | None = None,
) -> dict[str, Any]:
    proposals = _suggest_semantic_gaps(registry, governance_policy) + _suggest_bundle_and_integration(registry, governance_policy)

    if target_slug:
        proposals = [row for row in proposals if row.get("proposed_feature", {}).get("slug") == target_slug]

    return {
        "generated_at": _utc_now(),
        "target": target_slug or "all",
        "proposal_count": len(proposals),
        "proposals": proposals,
    }


def required_approvals_for_expansion(report: dict[str, Any]) -> list[str]:
    requirements: set[str] = set()
    for row in report.get("proposals", []):
        for item in row.get("governance_requirements", []):
            requirements.add(str(item))
    return sorted(requirements)


def validate_expansion_approvals(report: dict[str, Any], approvals: dict[str, bool]) -> list[str]:
    required = required_approvals_for_expansion(report)
    return [item for item in required if not approvals.get(item, False)]


def apply_expansion_report_to_registry(registry: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    existing = _existing_slugs(registry)
    for row in report.get("proposals", []):
        feature = row.get("proposed_feature", {})
        name = str(feature.get("name", "")).strip()
        slug = str(feature.get("slug", "")).strip() or slugify(name)
        if not name or not slug or slug in existing:
            continue

        mlas_tier = str(feature.get("mlas_tier", "Semantic Utility")).strip()
        btif = str(feature.get("btif_classification", "GeneralFlow")).strip()
        intent = str(feature.get("semantic_intent", "CaptureAndRoute")).strip()
        tags = normalize_semantic_tags(feature.get("semantic_tags", []))

        registry.setdefault("features", []).append(
            {
                "name": name,
                "slug": slug,
                "mlas_tier": mlas_tier,
                "btif_classification": btif,
                "semantic_intent": intent,
                "semantic_tags": tags,
                "paths": {
                    "erd": f"database_design/mermaid_erds/{slug}.erd.mmd",
                    "sequence": f"logic_design/mermaid_sequences/{slug}.sequence.mmd",
                    "ui_template": f"ui_templates/penpot_templates/features/{slug}/template.md",
                    "ui_component": f"ui_components/penpot_components/features/{slug}/component.md",
                },
                "status": "scaffolded",
                "expansion": {
                    "proposed_by": "feature_expansion",
                    "proposal_category": row.get("category"),
                    "semantic_lineage": row.get("semantic_lineage", {}),
                    "dependency_graph_impact": row.get("dependency_graph_impact", {}),
                },
            }
        )
        existing.add(slug)

    return registry
