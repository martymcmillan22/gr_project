from __future__ import annotations

import json
from pathlib import Path

SEVM_SURFACES = [
    {"symbol": "S", "subject": "Math", "format": "SACP", "surface": "math"},
    {"symbol": "E", "subject": "Language", "format": "EDNP", "surface": "language"},
    {"symbol": "V", "subject": "Arts", "format": "VLSM", "surface": "arts"},
    {"symbol": "M", "subject": "Science", "format": "MBSP", "surface": "science"},
]

LFO_DOCUMENT_FORMATS = ["linear", "2x_linear", "12_point", "perpetual"]
SCIENCE_GUI_LENSES = ["math_logic", "biology", "social", "physical"]

SCIENCE_GUI_PROFILE_DEFINITIONS = {
    "math_logic": {
        "interaction_model": "deterministic_behavior",
        "weights": {"alignment": 0.5, "stability": 0.3, "completion": 0.2},
        "trigger_sensitivity": 0.02,
    },
    "biology": {
        "interaction_model": "organic_interaction_flow",
        "weights": {"alignment": 0.35, "stability": 0.25, "completion": 0.4},
        "trigger_sensitivity": 0.015,
    },
    "social": {
        "interaction_model": "collaborative_community_patterns",
        "weights": {"alignment": 0.45, "stability": 0.2, "completion": 0.35},
        "trigger_sensitivity": 0.01,
    },
    "physical": {
        "interaction_model": "deployment_visual_physics",
        "weights": {"alignment": 0.4, "stability": 0.15, "completion": 0.45},
        "trigger_sensitivity": 0.01,
    },
}

PHASE_PROGRESSION_FACTORS = {
    "ideas": 0.1,
    "seeds": 0.35,
    "projects": 0.7,
    "mvp": 1.0,
    "studio": 1.05,
    "enterprise": 1.1,
}


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalized_hash(token: str) -> float:
    digest = sum(ord(character) for character in token)
    return (digest % 1000) / 1000.0


def _normalize_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def load_macro_industry_groups() -> list[dict[str, object]]:
    catalog_path = (
        Path(__file__).resolve().parent.parent
        / "platform_semantic"
        / "catalogs"
        / "macro_map.json"
    )

    if not catalog_path.exists():
        return []

    try:
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    flattened: list[dict[str, object]] = []
    for sector in payload.get("sectors", []):
        sector_id = int(sector.get("sector_id") or 0)
        sector_name = str(sector.get("sector_name") or "")
        for group in sector.get("industry_groups", []):
            group_id = int(group.get("group_id") or 0)
            group_name = str(group.get("subject_name") or "")
            industries = []
            for industry in group.get("industries", []):
                industry_name = str(industry.get("industry_name") or "")
                sub_industries = [str(item) for item in industry.get("sub_industries", []) if str(item).strip()]
                industries.append(
                    {
                        "industry_name": industry_name,
                        "sub_industries": sub_industries,
                    }
                )
            flattened.append(
                {
                    "sector_id": sector_id,
                    "sector_name": sector_name,
                    "group_id": group_id,
                    "group_name": group_name,
                    "industries": industries,
                }
            )

    flattened.sort(key=lambda item: int(item.get("group_id") or 0))
    return flattened


def build_sevm_logical_branches() -> list[dict[str, object]]:
    branches: list[dict[str, object]] = []
    for surface in SEVM_SURFACES:
        for format_name in LFO_DOCUMENT_FORMATS:
            branch_id = f"{surface['symbol']}_{surface['format']}_{format_name}"
            branches.append(
                {
                    "branch_id": branch_id,
                    "symbol": surface["symbol"],
                    "subject": surface["subject"],
                    "format": surface["format"],
                    "surface": surface["surface"],
                    "archetype": format_name,
                }
            )
    return branches


def build_sevm_group_templates(
    *,
    group_catalog: list[dict[str, object]],
    timeline_snapshot: dict[str, object] | None = None,
    synthesis_snapshot: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    timeline_snapshot = timeline_snapshot if isinstance(timeline_snapshot, dict) else {}
    synthesis_snapshot = synthesis_snapshot if isinstance(synthesis_snapshot, dict) else {}
    sevm_branches = build_sevm_logical_branches()

    templates: list[dict[str, object]] = []
    for group in group_catalog:
        group_id = int(group.get("group_id") or 0)
        group_name = str(group.get("group_name") or "")
        sector_name = str(group.get("sector_name") or "")
        branch_nodes = []
        for index, branch in enumerate(sevm_branches, start=1):
            slot_index = ((group_id + index - 2) % 16) + 1
            branch_nodes.append(
                {
                    **branch,
                    "slot_index": slot_index,
                    "timeline_binding": {
                        "slot_index": slot_index,
                        "latest_slot_index": int(timeline_snapshot.get("latest_slot_index") or 0),
                        "drift_score": float(timeline_snapshot.get("drift_score") or 0.0),
                        "alignment_score": float(timeline_snapshot.get("alignment_score") or 0.0),
                    },
                }
            )

        templates.append(
            {
                "template_id": f"group_lfo_{group_id:02d}",
                "group_metadata": {
                    "group_id": group_id,
                    "group_name": group_name,
                    "sector_name": sector_name,
                    "industry_count": len(group.get("industries", [])),
                },
                "sevm_template": {
                    "logical_branch_count": len(branch_nodes),
                    "branches": branch_nodes,
                    "synthesis": {
                        "risk_level": str(synthesis_snapshot.get("risk_level") or "low"),
                        "drift_trend": str(synthesis_snapshot.get("drift_trend") or "stable"),
                        "alignment_trajectory": str(synthesis_snapshot.get("alignment_trajectory") or "stable"),
                    },
                },
                "industries": group.get("industries", []),
            }
        )

    templates.sort(key=lambda item: int(item.get("group_metadata", {}).get("group_id") or 0))
    return templates


def build_industry_lfo_templates(group_templates: list[dict[str, object]]) -> list[dict[str, object]]:
    templates: list[dict[str, object]] = []
    for group_template in group_templates:
        group_metadata = group_template.get("group_metadata", {}) if isinstance(group_template, dict) else {}
        group_id = int(group_metadata.get("group_id") or 0)
        group_name = str(group_metadata.get("group_name") or "")
        sector_name = str(group_metadata.get("sector_name") or "")
        branches = group_template.get("sevm_template", {}).get("branches", []) if isinstance(group_template, dict) else []
        industries = group_template.get("industries", []) if isinstance(group_template, dict) else []
        inherited_risk_level = str(group_template.get("sevm_template", {}).get("synthesis", {}).get("risk_level") or "low")
        inherited_drift_trend = str(group_template.get("sevm_template", {}).get("synthesis", {}).get("drift_trend") or "stable")
        inherited_alignment_trajectory = str(group_template.get("sevm_template", {}).get("synthesis", {}).get("alignment_trajectory") or "stable")

        for index, industry in enumerate(industries, start=1):
            industry_name = str(industry.get("industry_name") or "")
            sub_industries = [str(item) for item in industry.get("sub_industries", []) if str(item).strip()]
            industry_slot_index = ((group_id - 1) * 4 + index - 1) % 16 + 1
            branch_ids = [str(item.get("branch_id") or "") for item in branches]
            template_id = f"industry_lfo_{group_id:02d}_{index:02d}"
            timeline_binding = {
                "latest_slot_index": industry_slot_index,
                "latest_phase": ["Ideas", "Seeds", "Projects", "MVP"][(industry_slot_index - 1) // 4],
                "group_id": group_id,
                "group_name": group_name,
                "sector_name": sector_name,
            }
            templates.append(
                {
                    "template_id": template_id,
                    "inherits_from": str(group_template.get("template_id") or ""),
                    "group_id": group_id,
                    "group_name": group_name,
                    "sector_name": sector_name,
                    "industry_name": industry_name,
                    "sub_industries": sub_industries,
                    "branch_ids": branch_ids,
                    "sevm_branch_lineage": {
                        "group_template_id": str(group_template.get("template_id") or ""),
                        "branch_count": len(branch_ids),
                        "branch_ids": branch_ids,
                    },
                    "timeline_binding": timeline_binding,
                    "inheritance": {
                        "group_template_id": str(group_template.get("template_id") or ""),
                        "group_name": group_name,
                        "industry_name": industry_name,
                        "sub_industries": sub_industries,
                        "override_allowed": False,
                    },
                    "surface_contract": {
                        "math": {
                            "mode": "sacp_probability_surface",
                            "feature_rows": [
                                {
                                    "feature": f"{group_name or 'group'}_{industry_name or 'industry'}_feature",
                                    "slot_index": industry_slot_index,
                                    "phase": timeline_binding["latest_phase"],
                                    "probability": round(_clamp_score(0.45 + (_normalized_hash(industry_name.lower()) * 0.3)), 3),
                                    "grade": "B",
                                    "risk_level": inherited_risk_level,
                                }
                            ],
                        },
                        "language": {
                            "mode": "ednp_transcript_surface",
                            "documents": [
                                {
                                    "format": format_name,
                                    "transcript_id": f"ednp_{format_name}_{industry_slot_index}_{group_id:02d}_{index:02d}",
                                    "summary": f"{group_name} / {industry_name} deterministic transcript for {format_name}.",
                                    "risk_level": inherited_risk_level,
                                    "drift_trend": inherited_drift_trend,
                                    "alignment_trajectory": inherited_alignment_trajectory,
                                }
                                for format_name in LFO_DOCUMENT_FORMATS
                            ],
                        },
                        "arts": {
                            "mode": "vlsm_creator_surface",
                            "creator_scaffolds": [
                                {
                                    "template_id": template_id,
                                    "group_name": group_name,
                                    "industry_name": industry_name,
                                    "branch_count": len(branch_ids),
                                    "mode": "creator_only",
                                }
                            ],
                        },
                        "science": {
                            "mode": "mbsp_consumer_gui_surface",
                            "lenses": [
                                {
                                    "lens": lens,
                                    "interaction_model": {
                                        "math_logic": "deterministic_behavior",
                                        "biology": "organic_interaction_flow",
                                        "social": "collaborative_community_patterns",
                                        "physical": "deployment_visual_physics",
                                    }[lens],
                                    "behavior_score": round(_clamp_score(0.35 + (_normalized_hash(f"{industry_name}:{lens}") * 0.5)), 3),
                                    "binds_to_timeline": True,
                                    "binds_to_orchestration": True,
                                    "binds_to_unified_intelligence": True,
                                    "timeline_progression": timeline_binding,
                                    "orchestration": {
                                        "trigger_count": 0,
                                    },
                                    "unified_intelligence": {
                                        "risk_level": inherited_risk_level,
                                        "drift_trend": inherited_drift_trend,
                                        "alignment_trajectory": inherited_alignment_trajectory,
                                    },
                                    "industry_context": {
                                        "group_id": group_id,
                                        "group_name": group_name,
                                        "industry_name": industry_name,
                                        "sub_industries": sub_industries,
                                    },
                                }
                                for lens in SCIENCE_GUI_LENSES
                            ],
                        },
                    },
                }
            )

    templates.sort(key=lambda item: str(item.get("template_id") or ""))
    return templates


def build_micro_lfo_templates(industry_templates: list[dict[str, object]]) -> list[dict[str, object]]:
    templates: list[dict[str, object]] = []
    for industry_template in industry_templates:
        group_id = int(industry_template.get("group_id") or 0)
        group_name = str(industry_template.get("group_name") or "")
        sector_name = str(industry_template.get("sector_name") or "")
        industry_name = str(industry_template.get("industry_name") or "")
        branch_ids = [str(item) for item in industry_template.get("branch_ids", []) if str(item).strip()]
        sub_industries = [str(item) for item in industry_template.get("sub_industries", []) if str(item).strip()]
        timeline_binding = industry_template.get("timeline_binding", {}) if isinstance(industry_template, dict) else {}
        surface_contract = industry_template.get("surface_contract", {}) if isinstance(industry_template, dict) else {}
        inherited_math_rows = _normalize_list(surface_contract.get("math", {}).get("feature_rows", []))
        inherited_language_documents = _normalize_list(surface_contract.get("language", {}).get("documents", []))
        inherited_arts_scaffolds = _normalize_list(surface_contract.get("arts", {}).get("creator_scaffolds", []))
        inherited_science_lenses = _normalize_list(surface_contract.get("science", {}).get("lenses", []))
        inherited_unified_intelligence = {}
        if inherited_science_lenses:
            inherited_unified_intelligence = (
                inherited_science_lenses[0].get("unified_intelligence", {})
                if isinstance(inherited_science_lenses[0], dict)
                else {}
            )
        inherited_risk_level = str(inherited_unified_intelligence.get("risk_level") or "low")
        inherited_drift_trend = str(inherited_unified_intelligence.get("drift_trend") or "stable")
        inherited_alignment_trajectory = str(inherited_unified_intelligence.get("alignment_trajectory") or "stable")

        if len(branch_ids) == 0:
            branch_ids = [str(item.get("branch_id") or "") for item in _normalize_list(industry_template.get("branch_ids", [])) if str(item).strip()]

        if not sub_industries:
            sub_industries = [industry_name or "Unknown Sub-Industry"]

        for index, sub_industry_name in enumerate(sub_industries, start=1):
            micro_slot_index = int(timeline_binding.get("latest_slot_index") or 0) or (((group_id - 1) * 4 + index - 1) % 16) + 1
            micro_template_id = f"micro_lfo_{group_id:02d}_{industry_name.lower().replace(' ', '_')[:16]}_{index:02d}"
            micro_context = {
                "group_id": group_id,
                "group_name": group_name,
                "sector_name": sector_name,
                "industry_name": industry_name,
                "sub_industry_name": sub_industry_name,
            }
            micro_prob = round(_clamp_score(0.38 + (_normalized_hash(sub_industry_name.lower()) * 0.42)), 3)
            templates.append(
                {
                    "template_id": micro_template_id,
                    "inherits_from": str(industry_template.get("template_id") or ""),
                    "group_id": group_id,
                    "group_name": group_name,
                    "sector_name": sector_name,
                    "industry_name": industry_name,
                    "sub_industry_name": sub_industry_name,
                    "branch_ids": branch_ids,
                    "sevm_branch_lineage": {
                        "group_template_id": str(industry_template.get("inherits_from") or ""),
                        "industry_template_id": str(industry_template.get("template_id") or ""),
                        "branch_count": len(branch_ids),
                        "branch_ids": branch_ids,
                    },
                    "timeline_binding": {
                        "latest_slot_index": micro_slot_index,
                        "latest_phase": str(timeline_binding.get("latest_phase") or ""),
                        "group_id": group_id,
                        "group_name": group_name,
                        "sector_name": sector_name,
                        "industry_name": industry_name,
                        "sub_industry_name": sub_industry_name,
                    },
                    "inheritance": {
                        "group_template_id": str(industry_template.get("inherits_from") or ""),
                        "industry_template_id": str(industry_template.get("template_id") or ""),
                        "group_name": group_name,
                        "industry_name": industry_name,
                        "sub_industry_name": sub_industry_name,
                        "override_allowed": False,
                    },
                    "surface_contract": {
                        "math": {
                            "mode": "sacp_probability_surface",
                            "feature_rows": [
                                {
                                    "feature": f"{industry_name or 'industry'}_{sub_industry_name or 'sub_industry'}_micro_feature",
                                    "slot_index": micro_slot_index,
                                    "phase": str(timeline_binding.get("latest_phase") or ""),
                                    "probability": micro_prob,
                                    "grade": "B" if micro_prob >= 0.6 else "C",
                                    "risk_level": inherited_risk_level,
                                }
                            ],
                            "inherits_feature_rows": inherited_math_rows,
                        },
                        "language": {
                            "mode": "ednp_transcript_surface",
                            "documents": [
                                {
                                    "format": format_name,
                                    "transcript_id": f"micro_ednp_{format_name}_{group_id:02d}_{index:02d}",
                                    "summary": f"Micro transcript for {sub_industry_name} in {industry_name}.",
                                    "risk_level": inherited_risk_level,
                                }
                                for format_name in LFO_DOCUMENT_FORMATS
                            ],
                            "inherits_documents": inherited_language_documents,
                        },
                        "arts": {
                            "mode": "vlsm_creator_surface",
                            "creator_scaffolds": [
                                {
                                    "template_id": micro_template_id,
                                    "group_name": group_name,
                                    "industry_name": industry_name,
                                    "sub_industry_name": sub_industry_name,
                                    "branch_count": len(branch_ids),
                                    "mode": "creator_only",
                                }
                            ],
                            "inherits_creator_scaffolds": inherited_arts_scaffolds,
                        },
                        "science": {
                            "mode": "mbsp_consumer_gui_surface",
                            "lenses": [
                                {
                                    "lens": lens,
                                    "interaction_model": {
                                        "math_logic": "deterministic_behavior",
                                        "biology": "organic_interaction_flow",
                                        "social": "collaborative_community_patterns",
                                        "physical": "deployment_visual_physics",
                                    }[lens],
                                    "behavior_score": round(_clamp_score(0.32 + (_normalized_hash(f"{sub_industry_name}:{lens}") * 0.52)), 3),
                                    "binds_to_timeline": True,
                                    "binds_to_orchestration": True,
                                    "binds_to_unified_intelligence": True,
                                    "timeline_progression": {
                                        "latest_slot_index": micro_slot_index,
                                        "latest_phase": str(timeline_binding.get("latest_phase") or ""),
                                    },
                                    "orchestration": {
                                        "trigger_count": 0,
                                    },
                                    "unified_intelligence": {
                                        "risk_level": inherited_risk_level,
                                        "drift_trend": inherited_drift_trend,
                                        "alignment_trajectory": inherited_alignment_trajectory,
                                    },
                                    "micro_context": micro_context,
                                }
                                for lens in SCIENCE_GUI_LENSES
                            ],
                            "inherits_lenses": inherited_science_lenses,
                        },
                    },
                }
            )

    templates.sort(key=lambda item: str(item.get("template_id") or ""))
    return templates


def evaluate_feature_probability(
    *,
    feature_name: str,
    timeline_snapshot: dict[str, object] | None = None,
    synthesis_snapshot: dict[str, object] | None = None,
) -> dict[str, object]:
    timeline_snapshot = timeline_snapshot if isinstance(timeline_snapshot, dict) else {}
    synthesis_snapshot = synthesis_snapshot if isinstance(synthesis_snapshot, dict) else {}

    token = str(feature_name or "feature").strip().lower()
    signature = _normalized_hash(token)

    drift_score = _clamp_score(float(timeline_snapshot.get("drift_score") or 0.0))
    alignment_score = _clamp_score(float(timeline_snapshot.get("alignment_score") or 0.0))
    slot_ratio = _clamp_score(float(timeline_snapshot.get("completion_ratio") or 0.0))

    statistics_score = _clamp_score((0.55 * alignment_score) + (0.45 * (1.0 - drift_score)))
    algebra_score = _clamp_score((0.5 * statistics_score) + (0.3 * slot_ratio) + (0.2 * signature))
    calculus_score = _clamp_score((0.6 * algebra_score) + (0.4 * alignment_score))
    probability_score = _clamp_score((0.7 * calculus_score) + (0.2 * statistics_score) + (0.1 * (1.0 - drift_score)))

    grade = "C"
    if probability_score >= 0.8:
        grade = "A"
    elif probability_score >= 0.65:
        grade = "B"

    return {
        "feature": token,
        "pipeline": {
            "statistics": round(statistics_score, 3),
            "algebra": round(algebra_score, 3),
            "calculus": round(calculus_score, 3),
            "probability": round(probability_score, 3),
        },
        "grade": grade,
        "risk_level": str(synthesis_snapshot.get("risk_level") or "low"),
    }


def build_math_sacp_surface(
    *,
    feature_probability: list[dict[str, object]],
    timeline_snapshot: dict[str, object] | None = None,
) -> dict[str, object]:
    timeline_snapshot = timeline_snapshot if isinstance(timeline_snapshot, dict) else {}
    latest_slot_index = int(timeline_snapshot.get("latest_slot_index") or 0)
    latest_phase = str(timeline_snapshot.get("latest_phase") or "")

    return {
        "mode": "sacp_probability_surface",
        "timeline_binding": {
            "latest_slot_index": latest_slot_index,
            "latest_phase": latest_phase,
            "drift_score": round(float(timeline_snapshot.get("drift_score") or 0.0), 3),
            "stability_score": round(float(timeline_snapshot.get("stability_score") or 0.0), 3),
            "alignment_score": round(float(timeline_snapshot.get("alignment_score") or 0.0), 3),
        },
        "feature_rows": [
            {
                "feature": str(item.get("feature") or ""),
                "slot_index": latest_slot_index,
                "phase": latest_phase,
                "probability": float(item.get("pipeline", {}).get("probability") or 0.0),
                "grade": str(item.get("grade") or "C"),
                "risk_level": str(item.get("risk_level") or "low"),
            }
            for item in feature_probability
        ],
    }


def build_language_ednp_surface(
    *,
    timeline_snapshot: dict[str, object] | None = None,
    synthesis_snapshot: dict[str, object] | None = None,
) -> dict[str, object]:
    timeline_snapshot = timeline_snapshot if isinstance(timeline_snapshot, dict) else {}
    synthesis_snapshot = synthesis_snapshot if isinstance(synthesis_snapshot, dict) else {}
    latest_slot_index = int(timeline_snapshot.get("latest_slot_index") or 0)
    latest_phase = str(timeline_snapshot.get("latest_phase") or "timeline").lower() or "timeline"

    return {
        "mode": "ednp_transcript_surface",
        "timeline_binding": {
            "latest_slot_index": latest_slot_index,
            "latest_phase": latest_phase,
        },
        "documents": [
            {
                "format": format_name,
                "transcript_id": f"ednp_{format_name}_{latest_slot_index or 1}",
                "summary": f"Deterministic {format_name} transcript for {latest_phase} slot {latest_slot_index or 1}.",
                "risk_level": str(synthesis_snapshot.get("risk_level") or "low"),
                "drift_trend": str(synthesis_snapshot.get("drift_trend") or "stable"),
                "alignment_trajectory": str(synthesis_snapshot.get("alignment_trajectory") or "stable"),
            }
            for format_name in LFO_DOCUMENT_FORMATS
        ],
    }


def build_arts_vlsm_surface(
    *,
    group_templates: list[dict[str, object]],
    timeline_snapshot: dict[str, object] | None = None,
) -> dict[str, object]:
    timeline_snapshot = timeline_snapshot if isinstance(timeline_snapshot, dict) else {}
    latest_slot_index = int(timeline_snapshot.get("latest_slot_index") or 0)

    return {
        "mode": "vlsm_creator_surface",
        "timeline_binding": {
            "latest_slot_index": latest_slot_index,
            "latest_phase": str(timeline_snapshot.get("latest_phase") or ""),
        },
        "creator_scaffolds": [
            {
                "template_id": str(template.get("template_id") or ""),
                "group_id": int(template.get("group_metadata", {}).get("group_id") or 0),
                "group_name": str(template.get("group_metadata", {}).get("group_name") or "Unknown"),
                "branch_count": int(template.get("sevm_template", {}).get("logical_branch_count") or 0),
                "mode": "creator_only",
            }
            for template in group_templates
        ],
    }


def build_consumer_gui_science_surface(
    *,
    timeline_snapshot: dict[str, object] | None = None,
    synthesis_snapshot: dict[str, object] | None = None,
    trigger_count: int = 0,
) -> dict[str, object]:
    timeline_snapshot = timeline_snapshot if isinstance(timeline_snapshot, dict) else {}
    synthesis_snapshot = synthesis_snapshot if isinstance(synthesis_snapshot, dict) else {}

    drift_score = _clamp_score(float(timeline_snapshot.get("drift_score") or 0.0))
    stability_score = _clamp_score(float(timeline_snapshot.get("stability_score") or 0.0))
    alignment_score = _clamp_score(float(timeline_snapshot.get("alignment_score") or 0.0))
    completion_ratio = _clamp_score(float(timeline_snapshot.get("completion_ratio") or 0.0))
    latest_phase = str(timeline_snapshot.get("latest_phase") or "").strip().lower()
    phase_factor = PHASE_PROGRESSION_FACTORS.get(latest_phase, 0.0)

    risk_level = str(synthesis_snapshot.get("risk_level") or "low")
    drift_trend = str(synthesis_snapshot.get("drift_trend") or "stable")
    alignment_trajectory = str(synthesis_snapshot.get("alignment_trajectory") or "stable")

    def resolve_surface_phase() -> str:
        if latest_phase in {"studio", "enterprise"}:
            return latest_phase
        if completion_ratio < 1.0:
            return latest_phase or "ideas"
        enterprise_ready = (
            alignment_score >= 0.78
            and stability_score >= 0.72
            and risk_level != "high"
            and int(trigger_count) <= 3
        )
        return "enterprise" if enterprise_ready else "studio"

    surface_phase = resolve_surface_phase()

    studio_ready_score = _clamp_score(
        (0.4 * completion_ratio)
        + (0.35 * alignment_score)
        + (0.25 * stability_score)
    )
    enterprise_ready_score = _clamp_score(
        (0.45 * alignment_score)
        + (0.35 * stability_score)
        + (0.2 * completion_ratio)
        - (0.03 * float(trigger_count))
    )
    surface_tiers = {
        "studio": {
            "phase": "studio",
            "label": "creator_publisher_tier",
            "unlocked": bool(completion_ratio >= 1.0 or latest_phase in {"studio", "enterprise"}),
            "active": surface_phase == "studio",
            "readiness_score": round(studio_ready_score, 3),
        },
        "enterprise": {
            "phase": "enterprise",
            "label": "operational_organizational_tier",
            "unlocked": bool(completion_ratio >= 1.0 or latest_phase == "enterprise"),
            "active": surface_phase == "enterprise",
            "readiness_score": round(enterprise_ready_score, 3),
        },
    }

    drift_trend_adjustment = 0.0
    if drift_trend == "rising":
        drift_trend_adjustment = -0.03
    elif drift_trend == "falling":
        drift_trend_adjustment = 0.02

    alignment_trajectory_adjustment = 0.0
    if alignment_trajectory == "improving":
        alignment_trajectory_adjustment = 0.03
    elif alignment_trajectory == "declining":
        alignment_trajectory_adjustment = -0.03

    lenses = []
    for lens in SCIENCE_GUI_LENSES:
        profile = SCIENCE_GUI_PROFILE_DEFINITIONS.get(lens, SCIENCE_GUI_PROFILE_DEFINITIONS["math_logic"])
        weights = profile["weights"]

        behavior_score = (
            (float(weights["alignment"]) * alignment_score)
            + (float(weights["stability"]) * stability_score)
            + (float(weights["completion"]) * completion_ratio)
            + (0.1 * phase_factor)
            + drift_trend_adjustment
            + alignment_trajectory_adjustment
            - (float(profile["trigger_sensitivity"]) * float(trigger_count))
        )
        behavior_score = _clamp_score(behavior_score)
        lenses.append(
            {
                "lens": lens,
                "interaction_model": str(profile["interaction_model"]),
                "behavior_score": round(behavior_score, 3),
                "binds_to_timeline": True,
                "binds_to_orchestration": True,
                "binds_to_unified_intelligence": True,
                "timeline_progression": {
                    "latest_phase": latest_phase,
                    "completion_ratio": round(completion_ratio, 3),
                },
                "orchestration": {
                    "trigger_count": int(trigger_count),
                },
                "surface_tiers": surface_tiers,
                "unified_intelligence": {
                    "risk_level": risk_level,
                    "drift_trend": drift_trend,
                    "alignment_trajectory": alignment_trajectory,
                },
                "risk_level": risk_level,
            }
        )

    return {
        "mode": "mbsp_consumer_gui_surface",
        "lenses": lenses,
        "trigger_count": int(trigger_count),
        "latest_phase": latest_phase,
        "surface_phase": surface_phase,
        "surface_tiers": surface_tiers,
        "completion_ratio": round(completion_ratio, 3),
        "drift_score": round(drift_score, 3),
        "stability_score": round(stability_score, 3),
        "alignment_score": round(alignment_score, 3),
        "drift_trend": drift_trend,
        "alignment_trajectory": alignment_trajectory,
        "risk_level": risk_level,
    }


def build_lfo_engine_envelope(
    *,
    timeline_snapshot: dict[str, object] | None = None,
    synthesis_snapshot: dict[str, object] | None = None,
    trigger_count: int = 0,
    feature_pathways: list[str] | None = None,
) -> dict[str, object]:
    timeline_snapshot = timeline_snapshot if isinstance(timeline_snapshot, dict) else {}
    synthesis_snapshot = synthesis_snapshot if isinstance(synthesis_snapshot, dict) else {}
    feature_pathways = [str(item).strip() for item in (feature_pathways or []) if str(item).strip()]
    if not feature_pathways:
        feature_pathways = [
            "project_scope_lock",
            "mvp_ui_synthesis",
            "timeline_gate_progression",
            "consumer_readiness_bundle",
        ]

    group_catalog = load_macro_industry_groups()
    group_templates = build_sevm_group_templates(
        group_catalog=group_catalog,
        timeline_snapshot=timeline_snapshot,
        synthesis_snapshot=synthesis_snapshot,
    )
    industry_templates = build_industry_lfo_templates(group_templates)
    micro_templates = build_micro_lfo_templates(industry_templates)
    feature_probability = [
        evaluate_feature_probability(
            feature_name=feature_name,
            timeline_snapshot=timeline_snapshot,
            synthesis_snapshot=synthesis_snapshot,
        )
        for feature_name in feature_pathways
    ]
    math_surface = build_math_sacp_surface(
        feature_probability=feature_probability,
        timeline_snapshot=timeline_snapshot,
    )
    language_surface = build_language_ednp_surface(
        timeline_snapshot=timeline_snapshot,
        synthesis_snapshot=synthesis_snapshot,
    )
    arts_surface = build_arts_vlsm_surface(
        group_templates=group_templates,
        timeline_snapshot=timeline_snapshot,
    )
    science_surface = build_consumer_gui_science_surface(
        timeline_snapshot=timeline_snapshot,
        synthesis_snapshot=synthesis_snapshot,
        trigger_count=trigger_count,
    )

    return {
        "mode": "lfo_expansion_v1",
        "sevm_logical_branches": build_sevm_logical_branches(),
        "template_summary": {
            "group_template_count": len(group_templates),
            "industry_template_count": len(industry_templates),
        },
        "group_templates": group_templates,
        "industry_templates": industry_templates,
        "micro_templates": micro_templates,
        "micro_template_summary": {
            "micro_template_count": len(micro_templates),
        },
        "feature_probability": feature_probability,
        "math_surface": math_surface,
        "language_surface": language_surface,
        "arts_surface": arts_surface,
        "science_surface": science_surface,
    }
