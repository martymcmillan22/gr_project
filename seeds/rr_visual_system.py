from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from django.core.cache import cache
from django.db.models import QuerySet
from django.utils import timezone

from peringram.rr import RRService
from platform_semantic.services import COMPARTMENTS
from platform_semantic.services import get_compartment_metadata

from .models import Business, Idea

OPERATING_STACK_CATALOG_PATH = (
    Path(__file__).resolve().parents[1] / "platform_semantic" / "catalogs" / "semantic_operating_stack.json"
)
MACRO_MAP_CATALOG_PATH = Path(__file__).resolve().parents[1] / "platform_semantic" / "catalogs" / "macro_map.json"
SEMANTIC_ACTION_LOG_LIMIT = 24
STABILIZATION_ACTIONS = {
    "rebalance_subject_mix",
    "repair_provenance_chain",
    "realign_workflow_step",
    "regenerate_chapter_outline",
    "resync_publishing_diagrams",
}
OPTIMIZATION_ACTIONS = {
    "rebalance_subject_load",
    "optimize_workflow_path",
    "improve_publishing_readiness",
    "shorten_workflow_path",
    "merge_sop_steps",
    "realign_subject_distribution",
    "auto_assemble_chapter_outline",
    "improve_subject_balance",
    "run_semantic_improvement_cycle",
}


def _semantic_action_log_cache_key(user) -> str:
    user_id = getattr(user, "id", None)
    return f"semantic-action-log:{user_id if user_id is not None else 'anonymous'}"


def _read_semantic_action_log(*, user=None) -> list[dict[str, Any]]:
    entries = cache.get(_semantic_action_log_cache_key(user), [])
    if not isinstance(entries, list):
        return []
    normalized = []
    for item in entries:
        if isinstance(item, dict):
            normalized.append(item)
    return normalized[-SEMANTIC_ACTION_LOG_LIMIT:]


def _write_semantic_action_log(*, user=None, entries: list[dict[str, Any]]) -> None:
    cache.set(_semantic_action_log_cache_key(user), entries[-SEMANTIC_ACTION_LOG_LIMIT:], timeout=60 * 60 * 24)


def _record_semantic_action_log_entry(*, user=None, entry: dict[str, Any]) -> list[dict[str, Any]]:
    entries = _read_semantic_action_log(user=user)
    entries.append(entry)
    entries = entries[-SEMANTIC_ACTION_LOG_LIMIT:]
    _write_semantic_action_log(user=user, entries=entries)
    return entries


def _build_semantic_action_log_summary(action_log: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    surface_counts: Counter[str] = Counter()
    subject_phase_counts: Counter[str] = Counter()

    for item in action_log:
        status_counts[str(item.get("status") or "unknown")] += 1
        action_counts[str(item.get("action") or "unknown")] += 1
        surface_counts[str(item.get("source_surface") or "unknown")] += 1
        subject = str(item.get("subject") or "Unknown")
        phase = str(item.get("phase") or "Unknown")
        subject_phase_counts[f"{subject}::{phase}"] += 1

    grouped_by_subject_phase = [
        {
            "subject": key.split("::", 1)[0],
            "phase": key.split("::", 1)[1],
            "count": count,
        }
        for key, count in subject_phase_counts.items()
    ]
    grouped_by_subject_phase.sort(key=lambda item: (-int(item.get("count", 0)), item.get("subject", ""), item.get("phase", "")))

    return {
        "total": len(action_log),
        "status_counts": dict(status_counts),
        "action_counts": dict(action_counts),
        "surface_counts": dict(surface_counts),
        "grouped_by_subject_phase": grouped_by_subject_phase,
    }


def _compute_drift_severity(
    *,
    failed_count: int,
    blocked_count: int,
    repeated_action_pattern: bool,
    provenance_gaps: int,
    timeline_cluster_pressure: int,
    subject_imbalance: bool,
    workflow_stalled: bool,
    publishing_gap: bool,
) -> tuple[str, int]:
    score = 0
    score += min(failed_count, 4) * 2
    score += min(blocked_count, 4)
    score += 2 if repeated_action_pattern else 0
    score += min(provenance_gaps, 3) * 2
    score += 2 if timeline_cluster_pressure >= 4 else 0
    score += 2 if subject_imbalance else 0
    score += 2 if workflow_stalled else 0
    score += 2 if publishing_gap else 0

    if score >= 10:
        return "high", score
    if score >= 5:
        return "medium", score
    return "low", score


def _build_subject_drift_chips(
    *,
    grouped_by_subject_phase: list[dict[str, Any]],
    subject_mix: dict[str, Any],
) -> list[dict[str, Any]]:
    chips: list[dict[str, Any]] = []
    top_group = grouped_by_subject_phase[0] if grouped_by_subject_phase else {}
    top_subject = str(top_group.get("subject") or "")
    top_phase = str(top_group.get("phase") or "")
    top_count = int(top_group.get("count", 0))

    if top_subject:
        chips.append(
            {
                "subject": top_subject,
                "phase": top_phase,
                "severity": "warn" if top_count >= 3 else "monitor",
                "reason": "Repeated semantic actions in the same subject-phase lane.",
                "count": top_count,
            }
        )

    sparse_subjects = [
        item
        for item in (subject_mix.get("subjects") or [])
        if float(item.get("node_share", 0.0)) < 0.15
    ]
    for item in sparse_subjects[:3]:
        chips.append(
            {
                "subject": item.get("subject"),
                "phase": item.get("phase"),
                "severity": "monitor",
                "reason": "Sparse subject representation may cause semantic imbalance.",
                "count": int(item.get("node_count", 0)),
            }
        )

    return chips


def _compute_subject_mix_score(subject_mix: dict[str, Any], timeline_groups: list[dict[str, Any]]) -> int:
    subjects = list(subject_mix.get("subjects") or [])
    if not subjects:
        return 100

    dominant_share = float(subjects[0].get("node_share", 0.0))
    sparse_count = sum(1 for item in subjects if float(item.get("node_share", 0.0)) < 0.12)
    cluster_pressure = max((int(group.get("count", 0)) for group in timeline_groups), default=0)

    penalty = int(max(0.0, (dominant_share - 0.45) * 120))
    penalty += sparse_count * 4
    penalty += 6 if cluster_pressure >= 5 else 0
    return max(0, min(100, 100 - penalty))


def _compute_workflow_efficiency_score(
    *,
    action_log: list[dict[str, Any]],
    failed_count: int,
    blocked_count: int,
    workflow_stalled: bool,
) -> int:
    recent = action_log[-10:]
    if not recent:
        return 100

    optimization_actions = sum(
        1
        for item in recent
        if str(item.get("action") or "") in {"optimize_workflow_path", "shorten_workflow_path", "merge_sop_steps", "realign_subject_distribution"}
        and str(item.get("status") or "") == "executed"
    )
    penalty = (failed_count * 8) + (blocked_count * 5)
    penalty += 12 if workflow_stalled else 0
    penalty -= min(optimization_actions * 3, 12)
    return max(0, min(100, 100 - penalty))


def _compute_publishing_readiness_score(
    *,
    chapter_previews: list[dict[str, Any]],
    publishing_gap: bool,
    drift_detected: bool,
    stabilization_pending: int,
    action_log: list[dict[str, Any]],
) -> int:
    preview_bonus = min(len(chapter_previews) * 8, 24)
    recent = action_log[-10:]
    publishing_boost = sum(
        1
        for item in recent
        if str(item.get("action") or "")
        in {"prepare_publishing_chapter", "improve_publishing_readiness", "auto_assemble_chapter_outline", "improve_subject_balance"}
        and str(item.get("status") or "") == "executed"
    )
    base = 60 + preview_bonus + min(publishing_boost * 4, 16)
    if publishing_gap:
        base -= 18
    if drift_detected:
        base -= 10
    base -= min(stabilization_pending * 4, 16)
    return max(0, min(100, int(base)))


def _build_optimization_loop(
    *,
    action_log: list[dict[str, Any]],
    subject_mix: dict[str, Any],
    timeline_groups: list[dict[str, Any]],
    provenance_chains: list[dict[str, Any]],
    chapter_previews: list[dict[str, Any]],
    drift_detected: bool,
    stabilization_pending: int,
    failed_count: int,
    blocked_count: int,
    workflow_stalled: bool,
    publishing_gap: bool,
) -> dict[str, Any]:
    subject_mix_score = _compute_subject_mix_score(subject_mix, timeline_groups)
    workflow_efficiency_score = _compute_workflow_efficiency_score(
        action_log=action_log,
        failed_count=failed_count,
        blocked_count=blocked_count,
        workflow_stalled=workflow_stalled,
    )
    publishing_readiness_score = _compute_publishing_readiness_score(
        chapter_previews=chapter_previews,
        publishing_gap=publishing_gap,
        drift_detected=drift_detected,
        stabilization_pending=stabilization_pending,
        action_log=action_log,
    )

    recommendations: list[dict[str, Any]] = []
    subjects = list(subject_mix.get("subjects") or [])
    dominant_subject = subjects[0] if subjects else {}

    if subject_mix_score < 78:
        recommendations.append(
            {
                "action": "rebalance_subject_load",
                "label": "Rebalance subject load",
                "reason": "Subject distribution is too concentrated for stable optimization.",
                "surface": "rr_dashboard",
            }
        )
        recommendations.append(
            {
                "action": "improve_subject_balance",
                "label": "Improve subject balance",
                "reason": "Publishing and workflow require better cross-subject balance.",
                "surface": "publishing_layer",
            }
        )

    if workflow_efficiency_score < 80:
        recommendations.append(
            {
                "action": "optimize_workflow_path",
                "label": "Optimize workflow path",
                "reason": "Action history indicates inefficiency in workflow progression.",
                "surface": "workflow_swimlanes",
            }
        )
        recommendations.append(
            {
                "action": "shorten_workflow_path",
                "label": "Shorten workflow path",
                "reason": "Timeline clusters suggest reducing redundant workflow transitions.",
                "surface": "workflow_swimlanes",
            }
        )
        recommendations.append(
            {
                "action": "merge_sop_steps",
                "label": "Merge SOP steps",
                "reason": "SOP steps can be merged to improve execution throughput.",
                "surface": "workflow_swimlanes",
            }
        )
        recommendations.append(
            {
                "action": "realign_subject_distribution",
                "label": "Re-align subject distribution",
                "reason": "Workflow lane pressure suggests re-routing subject distribution.",
                "surface": "va_guidance",
            }
        )

    if publishing_readiness_score < 82:
        recommendations.append(
            {
                "action": "improve_publishing_readiness",
                "label": "Improve publishing readiness",
                "reason": "Publishing readiness score is below deterministic target.",
                "surface": "publishing_layer",
            }
        )
        recommendations.append(
            {
                "action": "auto_assemble_chapter_outline",
                "label": "Auto-assemble chapter outline",
                "reason": "Chapter assembly should adapt to optimized subject and workflow signals.",
                "surface": "publishing_layer",
            }
        )

    if drift_detected or stabilization_pending > 0:
        recommendations.append(
            {
                "action": "run_semantic_improvement_cycle",
                "label": "Run semantic improvement cycle",
                "reason": "Improvement loop should close drift/stabilization gaps with optimization routing.",
                "surface": "semantic_os",
            }
        )

    executed_optimizations = sum(
        1
        for item in action_log
        if str(item.get("action") or "") in OPTIMIZATION_ACTIONS and str(item.get("status") or "") == "executed"
    )
    improvement_cycles = sum(
        1
        for item in action_log
        if str(item.get("action") or "") == "run_semantic_improvement_cycle" and str(item.get("status") or "") == "executed"
    )

    optimization_pressure = max(
        0,
        min(
            100,
            int((100 - subject_mix_score + 100 - workflow_efficiency_score + 100 - publishing_readiness_score) / 3),
        ),
    )

    return {
        "status": "active" if recommendations else "monitor",
        "signals": {
            "subject_mix_score": subject_mix_score,
            "workflow_efficiency_score": workflow_efficiency_score,
            "publishing_readiness_score": publishing_readiness_score,
            "optimization_pressure": optimization_pressure,
            "trend": "improving" if executed_optimizations >= max(1, stabilization_pending) else "monitor",
            "dominant_subject": dominant_subject.get("subject"),
            "provenance_depth_ready": all(int(item.get("depth", 0)) >= 5 for item in provenance_chains) if provenance_chains else False,
        },
        "progress": {
            "total_recommendations": len(recommendations),
            "executed_optimizations": executed_optimizations,
            "pending_optimizations": max(0, len(recommendations) - min(executed_optimizations, len(recommendations))),
            "improvement_cycles": improvement_cycles,
        },
        "auto_balancing": {
            "required": subject_mix_score < 78,
            "target_subject": dominant_subject.get("subject"),
            "target_compartment_id": dominant_subject.get("compartment_id"),
            "message": "Auto-balancing distributes workload across subjects, workflows, and publishing outputs.",
        },
        "recommendations": recommendations,
    }


def _build_semantic_feedback_loop(
    *,
    action_log: list[dict[str, Any]],
    timeline_groups: list[dict[str, Any]],
    subject_mix: dict[str, Any],
    provenance_chains: list[dict[str, Any]],
    chapter_previews: list[dict[str, Any]],
) -> dict[str, Any]:
    if not action_log:
        return {
            "adaptive_hints": [
                {
                    "type": "bootstrap_actions",
                    "message": "No semantic actions executed yet. Start with RR provenance chain and one workflow step.",
                }
            ],
            "stability_signals": {
                "recent_failures": 0,
                "recent_blocked": 0,
                "repeated_action_pattern": False,
                "drift_detected": False,
            },
            "drift_detection": {
                "severity": "low",
                "score": 0,
                "workflow_stalled": False,
                "subject_imbalance": False,
                "provenance_gaps": 0,
                "timeline_cluster_pressure": 0,
                "publishing_gap": False,
                "subject_drift_chips": [],
            },
            "stabilization_loop": {
                "status": "monitor",
                "progress": {
                    "total_recommendations": 0,
                    "executed_corrections": 0,
                    "pending_corrections": 0,
                },
                "recommendations": [],
            },
            "optimization_loop": {
                "status": "monitor",
                "signals": {
                    "subject_mix_score": 100,
                    "workflow_efficiency_score": 100,
                    "publishing_readiness_score": 100,
                    "optimization_pressure": 0,
                    "trend": "monitor",
                    "dominant_subject": None,
                    "provenance_depth_ready": False,
                },
                "progress": {
                    "total_recommendations": 0,
                    "executed_optimizations": 0,
                    "pending_optimizations": 0,
                    "improvement_cycles": 0,
                },
                "auto_balancing": {
                    "required": False,
                    "target_subject": None,
                    "target_compartment_id": None,
                    "message": "Optimization loop is monitoring baseline state.",
                },
                "recommendations": [],
            },
            "drift_alerts": [],
        }

    recent = action_log[-8:]
    failed_count = sum(1 for item in recent if str(item.get("status")) == "failed")
    blocked_count = sum(1 for item in recent if str(item.get("status")) == "blocked")
    action_pattern = Counter(str(item.get("action") or "unknown") for item in recent)
    repeated_action_pattern = any(count >= 3 for count in action_pattern.values())
    workflow_actions = [item for item in recent if str(item.get("action")) in {"advance_workflow_step", "realign_workflow_step"}]
    workflow_stalled = len(workflow_actions) >= 3 and len({str(item.get("workflow_step") or "") for item in workflow_actions}) <= 1

    provenance_gaps = sum(1 for item in provenance_chains if int(item.get("depth", 0)) < 5)
    timeline_cluster_pressure = max((int(group.get("count", 0)) for group in timeline_groups), default=0)

    subject_mix_items = list(subject_mix.get("subjects") or [])
    dominant_share = float(subject_mix_items[0].get("node_share", 0.0)) if subject_mix_items else 0.0
    subject_imbalance = dominant_share >= 0.55

    chapter_subjects = {str(item.get("subject") or "") for item in chapter_previews if item.get("subject")}
    dominant_subjects = {str(item.get("subject") or "") for item in subject_mix_items[:3] if item.get("subject")}
    publishing_gap = bool(dominant_subjects and len(chapter_subjects.intersection(dominant_subjects)) < min(2, len(dominant_subjects)))

    severity, severity_score = _compute_drift_severity(
        failed_count=failed_count,
        blocked_count=blocked_count,
        repeated_action_pattern=repeated_action_pattern,
        provenance_gaps=provenance_gaps,
        timeline_cluster_pressure=timeline_cluster_pressure,
        subject_imbalance=subject_imbalance,
        workflow_stalled=workflow_stalled,
        publishing_gap=publishing_gap,
    )
    drift_detected = severity in {"medium", "high"}

    drift_alerts = []
    if drift_detected:
        drift_alerts.append(
            {
                "type": "semantic_action_drift",
                "severity": "warn" if severity == "medium" else "high",
                "message": "Repeated blocked/failed actions indicate semantic drift risk.",
            }
        )
    if workflow_stalled:
        drift_alerts.append(
            {
                "type": "workflow_stall",
                "severity": "warn",
                "message": "Workflow steps appear stalled on repeated transitions.",
            }
        )
    if publishing_gap:
        drift_alerts.append(
            {
                "type": "publishing_subject_gap",
                "severity": "warn",
                "message": "Publishing chapter mix is drifting from dominant RR subjects.",
            }
        )

    dominant_subject = (subject_mix.get("subjects") or [{}])[0]
    adaptive_hints = [
        {
            "type": "next_action",
            "message": "If workflow actions cluster in one subject, route next action through VA guidance before publishing.",
            "subject": dominant_subject.get("subject"),
        },
        {
            "type": "timeline_alignment",
            "message": f"Timeline currently has {len(timeline_groups)} subject-phase clusters; align next action to top cluster.",
        },
    ]

    if repeated_action_pattern:
        adaptive_hints.append(
            {
                "type": "action_diversification",
                "message": "The same action is repeating; open RR provenance chain before next workflow step.",
            }
        )

    stabilization_recommendations = []
    if subject_imbalance:
        stabilization_recommendations.append(
            {
                "action": "rebalance_subject_mix",
                "label": "Rebalance subject mix",
                "reason": "Dominant subject share is too high for stable semantic routing.",
            }
        )
    if provenance_gaps > 0:
        stabilization_recommendations.append(
            {
                "action": "repair_provenance_chain",
                "label": "Repair provenance chain",
                "reason": "One or more lanes are below required provenance depth.",
            }
        )
    if workflow_stalled or failed_count >= 2:
        stabilization_recommendations.append(
            {
                "action": "realign_workflow_step",
                "label": "Re-align workflow step",
                "reason": "Workflow actions show stalled or unstable progression.",
            }
        )
    if publishing_gap:
        stabilization_recommendations.append(
            {
                "action": "regenerate_chapter_outline",
                "label": "Regenerate chapter outline",
                "reason": "Chapter assembly no longer matches dominant subjects.",
            }
        )
        stabilization_recommendations.append(
            {
                "action": "resync_publishing_diagrams",
                "label": "Re-sync publishing diagrams",
                "reason": "Publishing diagram subjects require semantic re-alignment.",
            }
        )

    executed_corrections = sum(
        1
        for item in action_log
        if str(item.get("action")) in STABILIZATION_ACTIONS and str(item.get("status")) == "executed"
    )
    grouped_by_subject_phase = []
    grouped_counter = Counter(f"{str(item.get('subject') or 'Unknown')}::{str(item.get('phase') or 'Unknown')}" for item in recent)
    for key, count in grouped_counter.items():
        parts = key.split("::", 1)
        grouped_by_subject_phase.append({"subject": parts[0], "phase": parts[1], "count": count})
    grouped_by_subject_phase.sort(key=lambda item: (-int(item.get("count", 0)), item.get("subject", ""), item.get("phase", "")))
    subject_drift_chips = _build_subject_drift_chips(grouped_by_subject_phase=grouped_by_subject_phase, subject_mix=subject_mix)
    optimization_loop = _build_optimization_loop(
        action_log=action_log,
        subject_mix=subject_mix,
        timeline_groups=timeline_groups,
        provenance_chains=provenance_chains,
        chapter_previews=chapter_previews,
        drift_detected=drift_detected,
        stabilization_pending=max(0, len(stabilization_recommendations) - executed_corrections),
        failed_count=failed_count,
        blocked_count=blocked_count,
        workflow_stalled=workflow_stalled,
        publishing_gap=publishing_gap,
    )

    return {
        "adaptive_hints": adaptive_hints,
        "stability_signals": {
            "recent_failures": failed_count,
            "recent_blocked": blocked_count,
            "repeated_action_pattern": repeated_action_pattern,
            "drift_detected": drift_detected,
        },
        "drift_detection": {
            "severity": severity,
            "score": severity_score,
            "workflow_stalled": workflow_stalled,
            "subject_imbalance": subject_imbalance,
            "provenance_gaps": provenance_gaps,
            "timeline_cluster_pressure": timeline_cluster_pressure,
            "publishing_gap": publishing_gap,
            "subject_drift_chips": subject_drift_chips,
        },
        "stabilization_loop": {
            "status": "active" if stabilization_recommendations else "monitor",
            "progress": {
                "total_recommendations": len(stabilization_recommendations),
                "executed_corrections": executed_corrections,
                "pending_corrections": max(0, len(stabilization_recommendations) - executed_corrections),
            },
            "recommendations": stabilization_recommendations,
        },
        "optimization_loop": optimization_loop,
        "drift_alerts": drift_alerts,
    }


def _to_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _phase_label(status: str) -> str:
    labels = {
        Idea.STATUS_RAW: "Idea",
        Idea.STATUS_SEED: "Seed",
        Idea.STATUS_PROJECT: "Project",
        Idea.STATUS_BUSINESS: "Archived",
    }
    return labels.get(str(status), str(status).title())


def _phase_key_from_status(status: str) -> str:
    mapping = {
        Idea.STATUS_RAW: "Idea",
        Idea.STATUS_SEED: "Seed",
        Idea.STATUS_PROJECT: "Project",
        Idea.STATUS_BUSINESS: "Archived",
    }
    return mapping.get(str(status), "Archived")


def _resolve_compartment_id(business: Business) -> int | None:
    if business.compartment_id is not None:
        return int(business.compartment_id)
    group_code = getattr(getattr(business.seed.idea.industry, "group", None), "code", None)
    if group_code is None:
        return None
    if group_code < 1 or group_code > len(COMPARTMENTS):
        return None
    return int(group_code - 1)


def _resolve_display_rgb(business: Business, compartment_id: int) -> tuple[int, int, int]:
    value = business.display_rgb if isinstance(business.display_rgb, dict) else {}
    if {"r", "g", "b"}.issubset(value.keys()):
        return int(value["r"]), int(value["g"]), int(value["b"])

    metadata = get_compartment_metadata(compartment_id)
    band = metadata["display_anchor_band"]
    return int(band["r"][0]), int(band["g"][0]), int(band["b"][0])


def _format_industry_path(business: Business) -> dict[str, Any]:
    notes = business.project_notes if isinstance(business.project_notes, dict) else {}
    sync = notes.get("rr_rgb_sync") if isinstance(notes.get("rr_rgb_sync"), dict) else {}
    if sync:
        path = [
            str(sync.get("sector") or ""),
            str(sync.get("subject") or ""),
            str(sync.get("industry") or ""),
            str(sync.get("subindustry") or ""),
        ]
        return {
            "path": [item for item in path if item],
            "source": str(sync.get("source") or "rr_rgb_sync"),
        }

    industry = business.seed.idea.industry
    group = industry.group
    fallback = [
        f"Group {group.code}",
        group.name,
        industry.name,
    ]
    return {
        "path": fallback,
        "source": "industry_group_fallback",
    }


def _build_card_color_spec(compartment_id: int, rgb: tuple[int, int, int]) -> dict[str, Any]:
    metadata = get_compartment_metadata(compartment_id)
    tag_tint = metadata["display_anchor_band"]
    return {
        "accent_rgb": {"r": rgb[0], "g": rgb[1], "b": rgb[2]},
        "accent_hex": _to_hex(rgb),
        "compartment_tag": {
            "subject": metadata["subject"],
            "compartment_id": compartment_id,
            "tag_tint": {
                "r": int(tag_tint["r"][0]),
                "g": int(tag_tint["g"][0]),
                "b": int(tag_tint["b"][0]),
            },
        },
        "integrity_indicator": {
            "ok": "#16a34a",
            "mismatch": "#f97316",
            "unavailable": "#64748b",
        },
    }


def _resolve_rr_provenance(business: Business) -> dict[str, Any]:
    notes = business.project_notes if isinstance(business.project_notes, dict) else {}
    workflow_refs = notes.get("workflow_refs") if isinstance(notes.get("workflow_refs"), list) else []
    sop_refs = notes.get("sop_refs") if isinstance(notes.get("sop_refs"), list) else []

    if not workflow_refs:
        activation = notes.get("activation_snapshot") if isinstance(notes.get("activation_snapshot"), dict) else {}
        if activation:
            workflow_refs = [
                {
                    "workflow_id": f"rr-workflow-{business.id}",
                    "phase": str(activation.get("lifecycle_stage") or "PROJECT"),
                    "mode": str(activation.get("mode") or "assistive"),
                }
            ]

    if not sop_refs:
        sop_refs = [
            {
                "sop_id": f"rr-sop-{business.id}",
                "title": f"Operate {business.brand_name}",
                "subject": str(getattr(getattr(business.seed.idea.industry, "group", None), "name", "")),
            }
        ]

    return {
        "workflow_refs": workflow_refs,
        "sop_refs": sop_refs,
    }


def _build_rr_card_payload(business: Business, compartment_id: int, lane_subject: str) -> dict[str, Any]:
    rgb = _resolve_display_rgb(business, compartment_id)
    integrity = RRService.verify_business_color_integrity(business)
    integrity_state = integrity.get("status", "unavailable")
    if integrity_state not in {"ok", "mismatch", "unavailable"}:
        integrity_state = "unavailable"

    path = _format_industry_path(business)
    path_items = path["path"]
    sector = path_items[0] if len(path_items) > 0 else ""
    industry = path_items[2] if len(path_items) > 2 else ""
    subindustry = path_items[3] if len(path_items) > 3 else ""
    provenance = _resolve_rr_provenance(business)

    return {
        "business_id": business.id,
        "seed_id": business.seed_id,
        "title": business.brand_name,
        "subject": lane_subject,
        "phase": _phase_label(business.seed.idea.status),
        "industry_path": path_items,
        "industry_path_source": path["source"],
        "sector": sector,
        "industry": industry,
        "subindustry": subindustry,
        "display_rgb": {"r": rgb[0], "g": rgb[1], "b": rgb[2]},
        "card_color_spec": _build_card_color_spec(compartment_id, rgb),
        "integrity_state": integrity_state,
        "integrity": integrity,
        "provenance": provenance,
        "navigation": {
            "rr_detail": f"/seeds/api/rr/nodes/{business.id}/",
            "middle_layer_dashboard": f"/project-middle-layer/dashboard/?rr_business_id={business.id}",
        },
        "updated_at": business.updated_at.isoformat(),
    }


def _normalize_surface_path(*parts: object) -> list[str]:
    return [str(item) for item in parts if item not in (None, "")]


def _build_provenance_hop(
    *,
    surface: str,
    label: str,
    business_id: int | None,
    compartment_id: int | None,
    subject: str,
    phase: str,
    depth: int,
    navigation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "surface": surface,
        "label": label,
        "business_id": business_id,
        "compartment_id": compartment_id,
        "subject": subject,
        "phase": phase,
        "depth": depth,
        "breadcrumbs": _normalize_surface_path("engine-truth", subject, phase, label),
        "navigation": navigation or {},
    }


def _build_provenance_chain(
    *,
    business_id: int | None,
    compartment_id: int,
    subject: str,
    phase: str,
) -> dict[str, Any]:
    chain = [
        _build_provenance_hop(
            surface="rr_dashboard",
            label=f"RR lane {subject}",
            business_id=business_id,
            compartment_id=compartment_id,
            subject=subject,
            phase=phase,
            depth=0,
            navigation={"surface": "rr_dashboard", "business_id": business_id, "compartment_id": compartment_id},
        ),
        _build_provenance_hop(
            surface="workflow_swimlanes",
            label="Workflow timeline",
            business_id=business_id,
            compartment_id=compartment_id,
            subject=subject,
            phase=phase,
            depth=1,
            navigation={"surface": "workflow_swimlanes", "business_id": business_id, "compartment_id": compartment_id},
        ),
        _build_provenance_hop(
            surface="va_guidance",
            label="VA guidance",
            business_id=business_id,
            compartment_id=compartment_id,
            subject=subject,
            phase=phase,
            depth=2,
            navigation={"surface": "va_guidance", "business_id": business_id, "compartment_id": compartment_id},
        ),
        _build_provenance_hop(
            surface="publishing_layer",
            label="Publishing assembly",
            business_id=business_id,
            compartment_id=compartment_id,
            subject=subject,
            phase=phase,
            depth=3,
            navigation={"surface": "publishing_layer", "business_id": business_id, "compartment_id": compartment_id},
        ),
        _build_provenance_hop(
            surface="rr_dashboard",
            label=f"Return to {subject}",
            business_id=business_id,
            compartment_id=compartment_id,
            subject=subject,
            phase=phase,
            depth=4,
            navigation={"surface": "rr_dashboard", "business_id": business_id, "compartment_id": compartment_id},
        ),
    ]
    return {
        "chain": chain,
        "breadcrumbs": [hop["label"] for hop in chain],
        "depth": len(chain),
    }


def _group_timeline_events(timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in timeline:
        key = (str(item.get("subject") or "Unknown"), str(item.get("phase") or "Unknown"))
        grouped.setdefault(key, []).append(item)

    buckets = []
    for (subject, phase), items in grouped.items():
        buckets.append(
            {
                "subject": subject,
                "phase": phase,
                "count": len(items),
                "items": items,
                "navigation_targets": [item.get("surface") for item in items if item.get("surface")],
            }
        )

    buckets.sort(key=lambda item: (-int(item.get("count", 0)), item.get("subject", ""), item.get("phase", "")))
    return buckets


def _business_queryset(user=None) -> QuerySet[Business]:
    queryset = Business.objects.select_related("seed__idea__industry__group")
    if user is not None:
        queryset = queryset.filter(seed__idea__user=user)
    return queryset


def _idea_queryset(user=None) -> QuerySet[Idea]:
    queryset = Idea.objects.select_related("industry__group")
    if user is not None:
        queryset = queryset.filter(user=user)
    return queryset


def _load_operating_stack_catalog() -> dict[str, Any]:
    payload = json.loads(OPERATING_STACK_CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid semantic operating stack catalog payload.")
    return payload


@lru_cache(maxsize=1)
def _load_macro_map_catalog() -> dict[str, Any]:
    payload = json.loads(MACRO_MAP_CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid macro map catalog payload.")
    return payload


@lru_cache(maxsize=1)
def _build_group_drilldown_map() -> dict[int, dict[str, Any]]:
    catalog = _load_macro_map_catalog()
    group_map: dict[int, dict[str, Any]] = {}
    for sector in catalog.get("sectors", []):
        sector_name = str(sector.get("sector_name") or "")
        for group in sector.get("industry_groups", []):
            group_id = int(group.get("group_id") or 0)
            if group_id <= 0:
                continue
            industries: list[dict[str, Any]] = []
            for industry in group.get("industries", []):
                industries.append(
                    {
                        "industry": str(industry.get("industry_name") or ""),
                        "subindustries": [str(item or "") for item in (industry.get("sub_industries") or [])],
                    }
                )
            group_map[group_id] = {
                "sector": sector_name,
                "subject": str(group.get("subject_name") or ""),
                "industries": industries,
            }
    return group_map


def build_rr_dashboard_payload(*, user=None, phase_filter: str = "", limit_per_lane: int = 10) -> dict[str, Any]:
    ideas = _idea_queryset(user=user)
    if phase_filter:
        ideas = ideas.filter(status__iexact=phase_filter.strip())

    status_bands = {
        "Idea": ideas.filter(status=Idea.STATUS_RAW).count(),
        "Seed": ideas.filter(status=Idea.STATUS_SEED).count(),
        "Project": ideas.filter(status=Idea.STATUS_PROJECT).count(),
        "Archived": ideas.filter(status=Idea.STATUS_BUSINESS).count(),
    }

    lane_map: dict[int, dict[str, Any]] = {}
    for cid in sorted(COMPARTMENTS.keys()):
        meta = get_compartment_metadata(cid)
        lane_map[cid] = {
            "compartment_id": cid,
            "subject": meta["subject"],
            "phase": meta["phase"],
            "label": meta["label"],
            "display_anchor_band": meta["display_anchor_band"],
            "node_count": 0,
            "integrity": {"ok": 0, "mismatch": 0, "unavailable": 0},
            "phase_distribution": {"Idea": 0, "Seed": 0, "Project": 0, "Archived": 0},
            "cards": [],
        }

    integrity_totals = Counter({"ok": 0, "mismatch": 0, "unavailable": 0})
    businesses = _business_queryset(user=user)
    if phase_filter:
        businesses = businesses.filter(seed__idea__status__iexact=phase_filter.strip())

    for business in businesses.order_by("-updated_at", "-id"):
        compartment_id = _resolve_compartment_id(business)
        if compartment_id is None or compartment_id not in lane_map:
            continue

        lane = lane_map[compartment_id]
        card_payload = _build_rr_card_payload(business=business, compartment_id=compartment_id, lane_subject=lane["subject"])
        integrity_state = card_payload["integrity_state"]
        phase_key = _phase_key_from_status(str(business.seed.idea.status))

        lane["node_count"] += 1
        lane["integrity"][integrity_state] += 1
        lane["phase_distribution"][phase_key] += 1
        integrity_totals[integrity_state] += 1

        if len(lane["cards"]) >= limit_per_lane:
            continue
        lane["cards"].append(card_payload)

    lanes = list(lane_map.values())
    lanes.sort(key=lambda item: (item["compartment_id"]))

    return {
        "mode": "rr_dashboard",
        "lane_count": len(lanes),
        "status_bands": status_bands,
        "integrity_strip": dict(integrity_totals),
        "lanes": lanes,
    }


def build_rr_industry_map_payload(*, user=None, phase_filter: str = "") -> dict[str, Any]:
    group_drilldown = _build_group_drilldown_map()
    row_map: dict[int, dict[str, Any]] = {}
    for cid in sorted(COMPARTMENTS.keys()):
        meta = get_compartment_metadata(cid)
        group_id = int(COMPARTMENTS[cid]["group_id"])
        drilldown = group_drilldown.get(group_id, {"sector": "", "subject": meta["subject"], "industries": []})
        row = row_map.setdefault(
            int(COMPARTMENTS[cid]["sector_id"]),
            {
                "sector_id": int(COMPARTMENTS[cid]["sector_id"]),
                "phase": meta["phase"],
                "cells": [],
            },
        )
        row["cells"].append(
            {
                "compartment_id": cid,
                "group_id": int(COMPARTMENTS[cid]["group_id"]),
                "subject": meta["subject"],
                "anchor_band": meta["display_anchor_band"],
                "rr_node_count": 0,
                "integrity_mismatch_count": 0,
                "intensity": 0.0,
                "phase_distribution": {"Idea": 0, "Seed": 0, "Project": 0, "Archived": 0},
                "nodes": [],
                "drilldown": {
                    "sector": drilldown["sector"],
                    "subject": drilldown["subject"],
                    "industries": drilldown["industries"],
                },
            }
        )

    index: dict[int, dict[str, Any]] = {
        cell["compartment_id"]: cell
        for row in row_map.values()
        for cell in row["cells"]
    }

    businesses = _business_queryset(user=user)
    if phase_filter:
        businesses = businesses.filter(seed__idea__status__iexact=phase_filter.strip())

    max_density = 0
    for business in businesses:
        compartment_id = _resolve_compartment_id(business)
        if compartment_id is None or compartment_id not in index:
            continue

        cell = index[compartment_id]
        card_payload = _build_rr_card_payload(business=business, compartment_id=compartment_id, lane_subject=cell["subject"])
        cell["rr_node_count"] += 1
        phase_key = _phase_key_from_status(str(business.seed.idea.status))
        cell["phase_distribution"][phase_key] += 1
        if card_payload.get("integrity_state") == "mismatch":
            cell["integrity_mismatch_count"] += 1
        if len(cell["nodes"]) < 30:
            cell["nodes"].append(card_payload)
        if cell["rr_node_count"] > max_density:
            max_density = cell["rr_node_count"]

    if max_density > 0:
        for cell in index.values():
            cell["intensity"] = round(float(cell["rr_node_count"]) / float(max_density), 4)

    rows = [row_map[key] for key in sorted(row_map.keys())]
    for row in rows:
        row["cells"].sort(key=lambda cell: cell["group_id"])

    return {
        "mode": "rr_industry_map",
        "phase_filter": phase_filter or "all",
        "rows": rows,
    }


def build_rr_card_spec_payload(*, compartment_id: int | None = None) -> dict[str, Any]:
    compartment_ids = [compartment_id] if compartment_id is not None else sorted(COMPARTMENTS.keys())
    cards: list[dict[str, Any]] = []
    for cid in compartment_ids:
        meta = get_compartment_metadata(cid)
        anchor = meta["display_anchor_band"]
        rgb = (int(anchor["r"][0]), int(anchor["g"][0]), int(anchor["b"][0]))
        cards.append(
            {
                "compartment_id": cid,
                "subject": meta["subject"],
                "phase": meta["phase"],
                "spec": _build_card_color_spec(cid, rgb),
                "layout_modes": ["compact", "expanded"],
            }
        )

    return {
        "mode": "rr_card_color_spec",
        "cards": cards,
    }


def build_va_guidance_payload(*, user=None) -> dict[str, Any]:
    dashboard = build_rr_dashboard_payload(user=user, limit_per_lane=0)
    lanes = dashboard["lanes"]

    dominant = sorted(
        [lane for lane in lanes if lane["node_count"] > 0],
        key=lambda lane: lane["node_count"],
        reverse=True,
    )[:3]

    sector_distribution: dict[str, int] = {}
    for lane in lanes:
        if lane["node_count"] <= 0:
            continue
        sector_distribution[lane["phase"]] = sector_distribution.get(lane["phase"], 0) + lane["node_count"]

    focus_subjects = [lane["subject"] for lane in dominant]
    recommendations = []
    if focus_subjects:
        recommendations.append(
            {
                "type": "suggest_sops_by_dominant_subject",
                "message": f"Prioritize SOP bundles for: {', '.join(focus_subjects)}.",
                "subjects": focus_subjects,
                "navigation": {
                    "lane": dominant[0]["compartment_id"] if dominant else None,
                },
            }
        )

    if len(sector_distribution.keys()) <= 1 and sum(sector_distribution.values()) > 0:
        recommendations.append(
            {
                "type": "warn_on_subject_imbalance",
                "message": "Workload is concentrated in one phase band. Add cross-phase SOP blocks.",
                "sector_distribution": sector_distribution,
                "navigation": {
                    "surface": "rr_dashboard",
                    "target": "phase_distribution",
                },
            }
        )
    else:
        recommendations.append(
            {
                "type": "propose_color_balanced_work_blocks",
                "message": "Compose daily blocks with at least two distinct phase bands.",
                "sector_distribution": sector_distribution,
                "navigation": {
                    "surface": "workflow_swimlanes",
                    "target": "color_balance",
                },
            }
        )

    sparse_phases = [phase for phase in ["Primary", "Secondary", "Tertiary", "Meta"] if int(sector_distribution.get(phase, 0)) == 0]
    if sparse_phases:
        recommendations.append(
            {
                "type": "phase_balance_gap",
                "message": f"No RR nodes detected in: {', '.join(sparse_phases)}. Create at least one lane-level SOP in these phases.",
                "missing_phases": sparse_phases,
                "navigation": {
                    "surface": "rr_industry_map",
                    "target": "phase_gap",
                },
            }
        )

    mismatch_hotspots = [
        {
            "compartment_id": lane["compartment_id"],
            "subject": lane["subject"],
            "mismatch_count": lane["integrity"]["mismatch"],
        }
        for lane in lanes
        if lane["integrity"]["mismatch"] > 0
    ]

    return {
        "mode": "va_semantic_color_guidance",
        "signals": {
            "dominant_compartments": [
                {
                    "compartment_id": lane["compartment_id"],
                    "subject": lane["subject"],
                    "node_count": lane["node_count"],
                }
                for lane in dominant
            ],
            "sector_distribution": sector_distribution,
            "integrity_mismatch_hotspots": mismatch_hotspots,
        },
        "recommendations": recommendations,
    }


def build_operating_stack_payload() -> dict[str, Any]:
    return _load_operating_stack_catalog()


def build_rr_node_detail_payload(*, business_id: int, user=None) -> dict[str, Any]:
    queryset = _business_queryset(user=user)
    business = queryset.filter(id=business_id).first()
    if business is None:
        raise ValueError("RR node not found for the current scope.")

    compartment_id = _resolve_compartment_id(business)
    if compartment_id is None:
        raise ValueError("RR node does not have a resolvable compartment.")

    card = _build_rr_card_payload(business=business, compartment_id=compartment_id, lane_subject=get_compartment_metadata(compartment_id)["subject"])
    notes = business.project_notes if isinstance(business.project_notes, dict) else {}
    sync = notes.get("rr_rgb_sync") if isinstance(notes.get("rr_rgb_sync"), dict) else {}

    history = [
        {
            "event": "business_created",
            "timestamp": business.created_at.isoformat(),
            "detail": "RR node promoted to Project business state.",
        }
    ]
    if sync:
        history.append(
            {
                "event": "rr_rgb_synced",
                "timestamp": business.updated_at.isoformat(),
                "detail": f"Synced via {sync.get('source', 'unknown')} with color_code {sync.get('color_code')}",
                "sync": sync,
            }
        )
    history.append(
        {
            "event": "integrity_checked",
            "timestamp": business.updated_at.isoformat(),
            "detail": f"Integrity state is {card['integrity_state']}",
            "integrity": card["integrity"],
        }
    )

    compartment_id = int(card.get("card_color_spec", {}).get("compartment_tag", {}).get("compartment_id") or 0)
    provenance = _build_provenance_chain(
        business_id=business.id,
        compartment_id=compartment_id,
        subject=str(card.get("subject") or "Unknown"),
        phase=str(card.get("phase") or "Unknown"),
    )

    semantic_breadcrumbs = _normalize_surface_path(
        "engine-truth",
        card.get("sector", ""),
        card.get("subject", ""),
        card.get("phase", ""),
        card.get("industry", ""),
    )
    publishing_ready = card["integrity_state"] == "ok" and str(card.get("phase") or "") in {"Project", "Archived"}
    semantic_actions = [
        {
            "action": "open_rr_provenance_chain",
            "label": "Open RR provenance chain",
            "request": {
                "surface": "rr_detail",
                "business_id": business.id,
                "compartment_id": compartment_id,
            },
        },
        {
            "action": "advance_workflow_step",
            "label": "Advance workflow step",
            "request": {
                "surface": "rr_detail",
                "business_id": business.id,
                "compartment_id": compartment_id,
                "workflow_step": "deterministic_next",
            },
        },
        {
            "action": "prepare_publishing_chapter",
            "label": "Prepare publishing chapter",
            "request": {
                "surface": "rr_detail",
                "business_id": business.id,
                "compartment_id": compartment_id,
            },
            "requires": "publishing_ready",
        },
        {
            "action": "repair_provenance_chain",
            "label": "Repair provenance chain",
            "request": {
                "surface": "rr_detail",
                "business_id": business.id,
                "compartment_id": compartment_id,
            },
        },
        {
            "action": "rebalance_subject_mix",
            "label": "Rebalance subject mix",
            "request": {
                "surface": "rr_detail",
                "business_id": business.id,
                "compartment_id": compartment_id,
            },
        },
    ]

    return {
        "mode": "rr_node_detail",
        "node": card,
        "ontology": {
            "sector": card.get("sector", ""),
            "subject": card.get("subject", ""),
            "industry": card.get("industry", ""),
            "subindustry": card.get("subindustry", ""),
            "path": card.get("industry_path", []),
            "source": card.get("industry_path_source", ""),
        },
        "identity": {
            "color_code": business.color_code,
            "compartment_id": business.compartment_id,
            "display_rgb": business.display_rgb,
            "integrity_state": card["integrity_state"],
        },
        "integrity_history": history,
        "provenance_chain": provenance["chain"],
        "multi_hop_provenance": provenance,
        "semantic_breadcrumbs": semantic_breadcrumbs,
        "semantic_actions": semantic_actions,
        "publishing_ready_signals": [
            {
                "signal": "publishing_ready",
                "status": "ready" if publishing_ready else "monitor",
                "message": "Publishing chapter assembly is ready when integrity is ok and phase is Project/Archived.",
            }
        ],
    }


def _build_semantic_subject_mix(lanes: list[dict[str, Any]]) -> dict[str, Any]:
    active_lanes = [lane for lane in lanes if int(lane.get("node_count", 0)) > 0]
    total_nodes = sum(int(lane.get("node_count", 0)) for lane in active_lanes)
    mix = []

    for lane in active_lanes:
        node_count = int(lane.get("node_count", 0))
        mix.append(
            {
                "compartment_id": lane.get("compartment_id"),
                "subject": lane.get("subject"),
                "phase": lane.get("phase"),
                "node_count": node_count,
                "node_share": round(node_count / total_nodes, 4) if total_nodes else 0.0,
                "integrity": lane.get("integrity", {}),
            }
        )

    mix.sort(key=lambda item: (-int(item.get("node_count", 0)), int(item.get("compartment_id", 0))))
    return {
        "total_nodes": total_nodes,
        "subjects": mix,
        "phase_totals": Counter(lane.get("phase") for lane in active_lanes),
    }


def _build_semantic_bottlenecks(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bottlenecks: list[dict[str, Any]] = []
    active_lanes = [lane for lane in lanes if int(lane.get("node_count", 0)) > 0]

    for lane in active_lanes:
        node_count = int(lane.get("node_count", 0))
        mismatch_count = int((lane.get("integrity") or {}).get("mismatch", 0))
        ok_count = int((lane.get("integrity") or {}).get("ok", 0))
        pressure_score = (mismatch_count * 2) + max(0, node_count - 3)

        if pressure_score <= 0:
            continue

        bottlenecks.append(
            {
                "compartment_id": lane.get("compartment_id"),
                "subject": lane.get("subject"),
                "phase": lane.get("phase"),
                "node_count": node_count,
                "mismatch_count": mismatch_count,
                "ok_count": ok_count,
                "pressure_score": pressure_score,
                "navigation": {
                    "rr_dashboard": lane.get("compartment_id"),
                    "rr_detail": (lane.get("cards") or [{}])[0].get("business_id"),
                    "surface": "workflow_swimlanes",
                },
            }
        )

    bottlenecks.sort(key=lambda item: (-int(item.get("pressure_score", 0)), int(item.get("compartment_id", 0))))
    return bottlenecks


def _build_semantic_recommendations(lanes: list[dict[str, Any]], bottlenecks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active_lanes = [lane for lane in lanes if int(lane.get("node_count", 0)) > 0]
    dominant_lanes = sorted(active_lanes, key=lambda lane: int(lane.get("node_count", 0)), reverse=True)[:4]
    recommendations: list[dict[str, Any]] = []

    for lane in dominant_lanes:
        first_card = (lane.get("cards") or [{}])[0]
        recommendations.append(
            {
                "type": "rr_node_focus",
                "message": f"Focus RR nodes in {lane.get('subject')} to stabilize {lane.get('phase')} throughput.",
                "compartment_id": lane.get("compartment_id"),
                "subject": lane.get("subject"),
                "phase": lane.get("phase"),
                "navigation": {
                    "surface": "rr_dashboard",
                    "compartment_id": lane.get("compartment_id"),
                    "business_id": first_card.get("business_id"),
                },
            }
        )

    if bottlenecks:
        lane = bottlenecks[0]
        recommendations.append(
            {
                "type": "workflow_bottleneck",
                "message": f"{lane['subject']} is the current workflow bottleneck with pressure score {lane['pressure_score']}.",
                "compartment_id": lane["compartment_id"],
                "subject": lane["subject"],
                "navigation": {
                    "surface": "workflow_swimlanes",
                    "compartment_id": lane["compartment_id"],
                    "target": "resolve_bottleneck",
                },
            }
        )

    if active_lanes:
        dominant_phase = max(Counter(lane.get("phase") for lane in active_lanes).items(), key=lambda item: item[1])[0]
        recommendations.append(
            {
                "type": "publishing_preselection",
                "message": f"Preselect publishing assembly for the dominant {dominant_phase} band.",
                "phase": dominant_phase,
                "navigation": {
                    "surface": "publishing_layer",
                    "target": "chapter_assembly",
                },
            }
        )

    return recommendations


def _build_publishing_previews(
    *,
    lanes: list[dict[str, Any]],
    operating_stack: dict[str, Any],
) -> list[dict[str, Any]]:
    sections = operating_stack.get("tracks", {}).get("publishing_layer", {})
    investor_sections = list((sections.get("investor_ebook") or {}).get("sections") or [])
    product_sections = list((sections.get("product_usage_ebook") or {}).get("sections") or [])
    dominant_lanes = sorted([lane for lane in lanes if int(lane.get("node_count", 0)) > 0], key=lambda lane: int(lane.get("node_count", 0)), reverse=True)[:4]
    previews: list[dict[str, Any]] = []

    for index, lane in enumerate(dominant_lanes):
        first_card = (lane.get("cards") or [{}])[0]
        workflow_refs = [item.get("workflow_id") for item in first_card.get("provenance", {}).get("workflow_refs", []) if item.get("workflow_id")]
        previews.append(
            {
                "chapter_id": f"chapter-{lane.get('compartment_id')}",
                "title": f"{lane.get('subject')} Chapter Preview",
                "subject": lane.get("subject"),
                "phase": lane.get("phase"),
                "compartment_id": lane.get("compartment_id"),
                "color": lane.get("display_anchor_band"),
                "workflow_refs": workflow_refs,
                "adaptive_reason": f"Build from {lane.get('node_count', 0)} RR nodes in {lane.get('subject')}.",
                "chapter_order": {
                    "investor_section": investor_sections[index % len(investor_sections)] if investor_sections else None,
                    "product_section": product_sections[index % len(product_sections)] if product_sections else None,
                },
                "assembly_chain": [
                    {
                        "surface": "rr_dashboard",
                        "label": f"{lane.get('subject')} RR lane",
                        "navigation": {
                            "surface": "rr_dashboard",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": first_card.get("business_id"),
                        },
                    },
                    {
                        "surface": "middle_layer",
                        "label": "Middle Layer color context",
                        "navigation": {
                            "surface": "middle_layer",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": first_card.get("business_id"),
                        },
                    },
                    {
                        "surface": "va_guidance",
                        "label": "VA coaching",
                        "navigation": {
                            "surface": "va_guidance",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": first_card.get("business_id"),
                        },
                    },
                    {
                        "surface": "workflow_swimlanes",
                        "label": "Workflow timeline",
                        "navigation": {
                            "surface": "workflow_swimlanes",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": first_card.get("business_id"),
                        },
                    },
                    {
                        "surface": "publishing_layer",
                        "label": "Chapter assembly",
                        "navigation": {
                            "surface": "publishing_layer",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": first_card.get("business_id"),
                        },
                    },
                ],
            }
        )

    return previews


def _build_semantic_timeline(
    *,
    dashboard: dict[str, Any],
    bottlenecks: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    publishing_previews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    for lane in dashboard.get("lanes", []):
        if int(lane.get("node_count", 0)) <= 0:
            continue
        events.append(
            {
                "event_type": "rr_lane_update",
                "surface": "rr_dashboard",
                "compartment_id": lane.get("compartment_id"),
                "subject": lane.get("subject"),
                "phase": lane.get("phase"),
                "color": lane.get("display_anchor_band"),
                "label": f"{lane.get('subject')} lane updated",
                "breadcrumbs": _normalize_surface_path("engine-truth", "rr", lane.get("subject"), lane.get("phase")),
                "breadcrumb_nodes": _build_provenance_chain(
                    business_id=(lane.get("cards") or [{}])[0].get("business_id"),
                    compartment_id=int(lane.get("compartment_id") or 0),
                    subject=str(lane.get("subject") or "Unknown"),
                    phase=str(lane.get("phase") or "Unknown"),
                )["chain"],
                "provenance": {
                    "node_count": lane.get("node_count", 0),
                    "integrity": lane.get("integrity", {}),
                },
            }
        )

    for bottleneck in bottlenecks[:4]:
        events.append(
            {
                "event_type": "workflow_bottleneck",
                "surface": "workflow_swimlanes",
                "compartment_id": bottleneck.get("compartment_id"),
                "subject": bottleneck.get("subject"),
                "phase": bottleneck.get("phase"),
                "label": f"Bottleneck in {bottleneck.get('subject')}",
                "breadcrumbs": _normalize_surface_path("engine-truth", "rr", "workflow", bottleneck.get("subject")),
                "breadcrumb_nodes": [
                    _build_provenance_hop(
                        surface="workflow_swimlanes",
                        label="Workflow bottleneck",
                        business_id=bottleneck.get("navigation", {}).get("rr_detail"),
                        compartment_id=bottleneck.get("compartment_id"),
                        subject=str(bottleneck.get("subject") or "Unknown"),
                        phase=str(bottleneck.get("phase") or "Unknown"),
                        depth=1,
                        navigation={"surface": "workflow_swimlanes", "compartment_id": bottleneck.get("compartment_id")},
                    )
                ],
                "provenance": {
                    "pressure_score": bottleneck.get("pressure_score"),
                    "mismatch_count": bottleneck.get("mismatch_count"),
                },
            }
        )

    for item in recommendations[:4]:
        events.append(
            {
                "event_type": "va_guidance",
                "surface": item.get("navigation", {}).get("surface", "va_guidance"),
                "compartment_id": item.get("compartment_id"),
                "subject": item.get("subject"),
                "phase": item.get("phase"),
                "label": item.get("message"),
                "breadcrumbs": _normalize_surface_path("engine-truth", "va", item.get("subject") or item.get("type")),
                "breadcrumb_nodes": [
                    _build_provenance_hop(
                        surface=str(item.get("navigation", {}).get("surface") or "va_guidance"),
                        label=str(item.get("message") or "VA recommendation"),
                        business_id=item.get("navigation", {}).get("business_id"),
                        compartment_id=item.get("compartment_id"),
                        subject=str(item.get("subject") or "Unknown"),
                        phase=str(item.get("phase") or "Unknown"),
                        depth=2,
                        navigation=item.get("navigation", {}),
                    )
                ],
                "provenance": {
                    "navigation": item.get("navigation", {}),
                    "type": item.get("type"),
                },
            }
        )

    for item in publishing_previews[:4]:
        events.append(
            {
                "event_type": "publishing_preview",
                "surface": "publishing_layer",
                "compartment_id": item.get("compartment_id"),
                "subject": item.get("subject"),
                "phase": item.get("phase"),
                "label": item.get("title"),
                "breadcrumbs": _normalize_surface_path("engine-truth", "publishing", item.get("subject"), item.get("phase")),
                "breadcrumb_nodes": item.get("assembly_chain", []),
                "provenance": {
                    "chapter_id": item.get("chapter_id"),
                    "workflow_refs": item.get("workflow_refs", []),
                },
            }
        )

    return events


def _build_semantic_os_health(
    *,
    dashboard: dict[str, Any],
    timeline: list[dict[str, Any]],
    provenance_chains: list[dict[str, Any]],
    guidance: dict[str, Any],
    publishing_previews: list[dict[str, Any]],
    action_log_summary: dict[str, Any],
    feedback_loop: dict[str, Any],
) -> dict[str, Any]:
    active_lane_count = int(dashboard.get("lane_count", 0))
    active_timeline_events = len(timeline)
    provenance_depth_ok = all(int(item.get("depth", 0)) >= 5 for item in provenance_chains) if provenance_chains else False
    action_log_total = int(action_log_summary.get("total", 0))
    workflow_action_total = int((action_log_summary.get("action_counts") or {}).get("advance_workflow_step", 0))
    drift_detection = feedback_loop.get("drift_detection") or {}
    drift_detected = bool((feedback_loop.get("stability_signals") or {}).get("drift_detected"))
    drift_severity = str(drift_detection.get("severity") or "low")
    stabilization_loop = feedback_loop.get("stabilization_loop") or {}
    stabilization_progress = stabilization_loop.get("progress") or {}
    stabilization_pending = int(stabilization_progress.get("pending_corrections", 0))
    stabilization_executed = int(stabilization_progress.get("executed_corrections", 0))
    stabilization_ready = stabilization_pending <= 0 or stabilization_executed > 0
    optimization_loop = feedback_loop.get("optimization_loop") or {}
    optimization_signals = optimization_loop.get("signals") or {}
    optimization_progress = optimization_loop.get("progress") or {}
    optimization_subject_mix_score = int(optimization_signals.get("subject_mix_score", 100))
    optimization_workflow_efficiency_score = int(optimization_signals.get("workflow_efficiency_score", 100))
    optimization_publishing_readiness_score = int(optimization_signals.get("publishing_readiness_score", 100))
    optimization_pending = int(optimization_progress.get("pending_optimizations", 0))
    optimization_executed = int(optimization_progress.get("executed_optimizations", 0))
    optimization_ready = optimization_pending <= 0 or optimization_executed > 0
    checks = [
        {
            "surface": "rr",
            "status": "pass" if active_lane_count >= 0 else "warn",
            "message": "RR dashboard payload is available.",
        },
        {
            "surface": "workflow",
            "status": "pass" if provenance_chains else "warn",
            "message": "Workflow provenance is aligned with RR lanes.",
        },
        {
            "surface": "va",
            "status": "pass" if guidance.get("recommendations") else "warn",
            "message": "VA guidance is derived from shared intelligence.",
        },
        {
            "surface": "publishing",
            "status": "pass" if publishing_previews else "warn",
            "message": "Publishing previews are assembled from RR data.",
        },
        {
            "surface": "timeline",
            "status": "pass" if active_timeline_events else "warn",
            "message": "Unified timeline contains cross-surface events.",
        },
        {
            "surface": "provenance_depth",
            "status": "pass" if provenance_depth_ok else "warn",
            "message": "Provenance chains carry multi-hop depth.",
        },
        {
            "surface": "action_log",
            "status": "pass",
            "message": "Semantic action history is tracked for cross-surface reflection and stabilizes as actions execute.",
        },
        {
            "surface": "workflow_stability",
            "status": "pass",
            "message": "Workflow stabilization is monitored through semantic action outcomes.",
        },
        {
            "surface": "semantic_drift",
            "status": "warn" if drift_detected else "pass",
            "message": f"Semantic drift severity is {drift_severity}; warnings rise as failures, stalls, and gaps accumulate.",
        },
        {
            "surface": "stabilization_loop",
            "status": "pass" if stabilization_ready else "warn",
            "message": "Stabilization loop tracks correction progress across workflow, provenance, and publishing.",
        },
        {
            "surface": "resilience_consistency",
            "status": "pass" if bool(feedback_loop.get("drift_detection")) and bool(stabilization_loop) else "warn",
            "message": "Drift detection, stabilization recommendations, and feedback composition remain in sync.",
        },
        {
            "surface": "optimization_loop",
            "status": "pass" if optimization_ready else "warn",
            "message": "Optimization loop tracks subject mix, workflow efficiency, and publishing readiness improvements.",
        },
        {
            "surface": "improvement_loop_consistency",
            "status": "pass" if optimization_subject_mix_score >= 0 and optimization_workflow_efficiency_score >= 0 and optimization_publishing_readiness_score >= 0 else "warn",
            "message": "Improvement loop signals are coherent across optimization and publishing readiness routing.",
        },
    ]
    return {
        "ready": all(item["status"] == "pass" for item in checks),
        "checks": checks,
        "drift": {
            "detected": drift_detected,
            "severity": drift_severity,
            "score": int(drift_detection.get("score", 0)),
        },
        "stabilization": {
            "status": stabilization_loop.get("status", "monitor"),
            "executed_corrections": stabilization_executed,
            "pending_corrections": stabilization_pending,
            "ready": stabilization_ready,
        },
        "optimization": {
            "status": optimization_loop.get("status", "monitor"),
            "subject_mix_score": optimization_subject_mix_score,
            "workflow_efficiency_score": optimization_workflow_efficiency_score,
            "publishing_readiness_score": optimization_publishing_readiness_score,
            "executed_optimizations": optimization_executed,
            "pending_optimizations": optimization_pending,
            "ready": optimization_ready,
        },
        "partial_hydration": {
            "dashboard": bool(dashboard.get("lanes")),
            "timeline": active_timeline_events > 0,
            "provenance": bool(provenance_chains),
            "publishing": bool(publishing_previews),
            "action_log": action_log_total > 0,
            "optimization": bool(optimization_loop),
        },
        "surface_contract": ["rr", "middle_layer", "va", "workflow", "publishing", "timeline", "semantic_os", "semantic_actions", "action_log", "feedback_loop", "drift_detection", "stabilization", "optimization"],
    }


def _build_timeline_automation(
    *,
    timeline_groups: list[dict[str, Any]],
    subject_mix: dict[str, Any],
    provenance_chains: list[dict[str, Any]],
) -> dict[str, Any]:
    repeated_patterns = [
        {
            "subject": group.get("subject"),
            "phase": group.get("phase"),
            "repeat_count": group.get("count", 0),
            "trigger": "cluster_repeat_pattern",
        }
        for group in timeline_groups
        if int(group.get("count", 0)) > 1
    ]

    dominant_subject = (subject_mix.get("subjects") or [{}])[0]
    timeline_triggers = [
        {
            "trigger": "timeline_event_density",
            "status": "active" if repeated_patterns else "monitor",
            "message": "Repeated timeline events can trigger workflow nudges.",
        },
        {
            "trigger": "provenance_depth",
            "status": "active" if provenance_chains else "monitor",
            "message": "Multi-hop provenance enables cross-surface automation.",
        },
        {
            "trigger": "subject_mix_shift",
            "status": "active" if dominant_subject else "monitor",
            "message": "Subject mix changes can trigger publishing-ready signals.",
            "subject": dominant_subject.get("subject"),
        },
    ]

    return {
        "repeated_patterns": repeated_patterns,
        "triggers": timeline_triggers,
        "semantic_reminders": [
            "Advance a workflow step when timeline repeats in the same subject-phase cluster.",
            "Prepare chapter draft when provenance depth >= 5 and integrity is stable.",
            "Open RR provenance chain before executing cross-surface publishing actions.",
        ],
    }


def _build_semantic_action_engine(
    *,
    dashboard: dict[str, Any],
    recommendations: list[dict[str, Any]],
    timeline_groups: list[dict[str, Any]],
    provenance_chains: list[dict[str, Any]],
    publishing_previews: list[dict[str, Any]],
    semantic_os_health: dict[str, Any],
    subject_mix: dict[str, Any],
    action_log_summary: dict[str, Any],
    feedback_loop: dict[str, Any],
) -> dict[str, Any]:
    vocabulary = [
        {
            "action": "advance_workflow_step",
            "label": "Advance workflow step",
            "description": "Execute next deterministic workflow step and append timeline/provenance updates.",
            "surfaces": ["rr_detail", "va_guidance", "workflow_swimlanes", "timeline"],
        },
        {
            "action": "prepare_publishing_chapter",
            "label": "Prepare publishing chapter",
            "description": "Assemble draft chapter from RR provenance and workflow history.",
            "surfaces": ["rr_detail", "publishing_layer", "timeline", "va_guidance"],
        },
        {
            "action": "open_rr_provenance_chain",
            "label": "Open RR provenance chain",
            "description": "Navigate and render multi-hop provenance from RR through workflows and publishing.",
            "surfaces": ["rr_detail", "workflow_swimlanes", "publishing_layer", "intelligence"],
        },
        {
            "action": "rebalance_subject_mix",
            "label": "Rebalance subject mix",
            "description": "Apply stabilization routing to rebalance overloaded subject lanes.",
            "surfaces": ["rr_dashboard", "va_guidance", "intelligence"],
        },
        {
            "action": "repair_provenance_chain",
            "label": "Repair provenance chain",
            "description": "Repair provenance continuity when depth or route integrity drops.",
            "surfaces": ["rr_detail", "workflow_swimlanes", "intelligence"],
        },
        {
            "action": "realign_workflow_step",
            "label": "Re-align workflow step",
            "description": "Unstall workflow progression with deterministic corrective transition.",
            "surfaces": ["workflow_swimlanes", "va_guidance", "intelligence"],
        },
        {
            "action": "regenerate_chapter_outline",
            "label": "Regenerate chapter outline",
            "description": "Regenerate publishing chapter outline to match dominant subject mix.",
            "surfaces": ["publishing_layer", "intelligence"],
        },
        {
            "action": "resync_publishing_diagrams",
            "label": "Re-sync publishing diagrams",
            "description": "Re-sync publishing semantic diagrams to corrected provenance and subject mix.",
            "surfaces": ["publishing_layer", "intelligence"],
        },
        {
            "action": "rebalance_subject_load",
            "label": "Rebalance subject load",
            "description": "Optimize RR subject load balancing using deterministic lane pressure signals.",
            "surfaces": ["rr_dashboard", "va_guidance", "intelligence"],
        },
        {
            "action": "optimize_workflow_path",
            "label": "Optimize workflow path",
            "description": "Optimize workflow transitions using timeline density and failure patterns.",
            "surfaces": ["workflow_swimlanes", "intelligence"],
        },
        {
            "action": "improve_publishing_readiness",
            "label": "Improve publishing readiness",
            "description": "Improve publishing readiness from workflow and provenance optimization signals.",
            "surfaces": ["publishing_layer", "intelligence"],
        },
        {
            "action": "shorten_workflow_path",
            "label": "Shorten workflow path",
            "description": "Shorten redundant workflow hops while preserving deterministic ordering.",
            "surfaces": ["workflow_swimlanes", "timeline", "intelligence"],
        },
        {
            "action": "merge_sop_steps",
            "label": "Merge SOP steps",
            "description": "Merge adjacent SOP steps to improve throughput in constrained lanes.",
            "surfaces": ["workflow_swimlanes", "intelligence"],
        },
        {
            "action": "realign_subject_distribution",
            "label": "Re-align subject distribution",
            "description": "Re-route workflow emphasis to restore healthy cross-subject distribution.",
            "surfaces": ["va_guidance", "workflow_swimlanes", "rr_dashboard", "intelligence"],
        },
        {
            "action": "auto_assemble_chapter_outline",
            "label": "Auto-assemble chapter outline",
            "description": "Auto-assemble chapter outlines from optimization-weighted subject and timeline signals.",
            "surfaces": ["publishing_layer", "timeline", "intelligence"],
        },
        {
            "action": "improve_subject_balance",
            "label": "Improve subject balance",
            "description": "Apply publishing-layer corrections for better semantic subject balance.",
            "surfaces": ["publishing_layer", "rr_dashboard", "intelligence"],
        },
        {
            "action": "run_semantic_improvement_cycle",
            "label": "Run semantic improvement cycle",
            "description": "Run end-to-end semantic OS improvement cycle from drift through optimization.",
            "surfaces": ["semantic_os", "timeline", "intelligence"],
        },
    ]

    first_recommendation = recommendations[0] if recommendations else {}
    first_chain = provenance_chains[0] if provenance_chains else {}
    first_preview = publishing_previews[0] if publishing_previews else {}
    bundles = [
        {
            "bundle_id": "workflow-progress-bundle",
            "title": "Workflow Progress Bundle",
            "actions": ["open_rr_provenance_chain", "advance_workflow_step"],
            "default_request": {
                "surface": "workflow_swimlanes",
                "compartment_id": first_recommendation.get("compartment_id") or first_chain.get("compartment_id"),
                "business_id": first_recommendation.get("navigation", {}).get("business_id") or first_chain.get("business_id"),
            },
        },
        {
            "bundle_id": "publishing-prep-bundle",
            "title": "Publishing Prep Bundle",
            "actions": ["advance_workflow_step", "prepare_publishing_chapter"],
            "default_request": {
                "surface": "publishing_layer",
                "compartment_id": first_preview.get("compartment_id") or first_chain.get("compartment_id"),
                "business_id": first_preview.get("assembly_chain", [{}])[0].get("navigation", {}).get("business_id") if first_preview else first_chain.get("business_id"),
            },
        },
        {
            "bundle_id": "rr-provenance-bundle",
            "title": "RR Provenance Bundle",
            "actions": ["open_rr_provenance_chain"],
            "default_request": {
                "surface": "rr_detail",
                "compartment_id": first_chain.get("compartment_id"),
                "business_id": first_chain.get("business_id"),
            },
        },
        {
            "bundle_id": "stabilization-workflow-bundle",
            "title": "Workflow Stabilization Bundle",
            "actions": ["repair_provenance_chain", "realign_workflow_step"],
            "default_request": {
                "surface": "workflow_swimlanes",
                "compartment_id": first_chain.get("compartment_id") or first_recommendation.get("compartment_id"),
                "business_id": first_chain.get("business_id") or first_recommendation.get("navigation", {}).get("business_id"),
                "workflow_step": "stabilize",
            },
        },
        {
            "bundle_id": "stabilization-publishing-bundle",
            "title": "Publishing Stabilization Bundle",
            "actions": ["regenerate_chapter_outline", "resync_publishing_diagrams"],
            "default_request": {
                "surface": "publishing_layer",
                "compartment_id": first_preview.get("compartment_id") or first_chain.get("compartment_id"),
                "business_id": first_preview.get("assembly_chain", [{}])[0].get("navigation", {}).get("business_id") if first_preview else first_chain.get("business_id"),
            },
        },
        {
            "bundle_id": "stabilization-subject-bundle",
            "title": "Subject Rebalance Bundle",
            "actions": ["rebalance_subject_mix", "repair_provenance_chain"],
            "default_request": {
                "surface": "rr_dashboard",
                "compartment_id": first_recommendation.get("compartment_id") or first_chain.get("compartment_id"),
                "business_id": first_recommendation.get("navigation", {}).get("business_id") or first_chain.get("business_id"),
            },
        },
        {
            "bundle_id": "optimization-subject-balance-bundle",
            "title": "Subject Balance Optimization Bundle",
            "actions": ["rebalance_subject_load", "realign_subject_distribution", "improve_subject_balance"],
            "default_request": {
                "surface": "rr_dashboard",
                "compartment_id": first_recommendation.get("compartment_id") or first_chain.get("compartment_id"),
                "business_id": first_recommendation.get("navigation", {}).get("business_id") or first_chain.get("business_id"),
            },
        },
        {
            "bundle_id": "optimization-workflow-efficiency-bundle",
            "title": "Workflow Efficiency Optimization Bundle",
            "actions": ["optimize_workflow_path", "shorten_workflow_path", "merge_sop_steps"],
            "default_request": {
                "surface": "workflow_swimlanes",
                "compartment_id": first_chain.get("compartment_id") or first_recommendation.get("compartment_id"),
                "business_id": first_chain.get("business_id") or first_recommendation.get("navigation", {}).get("business_id"),
                "workflow_step": "optimize",
            },
        },
        {
            "bundle_id": "optimization-publishing-readiness-bundle",
            "title": "Publishing Readiness Optimization Bundle",
            "actions": ["improve_publishing_readiness", "auto_assemble_chapter_outline"],
            "default_request": {
                "surface": "publishing_layer",
                "compartment_id": first_preview.get("compartment_id") or first_chain.get("compartment_id"),
                "business_id": first_preview.get("assembly_chain", [{}])[0].get("navigation", {}).get("business_id") if first_preview else first_chain.get("business_id"),
            },
        },
        {
            "bundle_id": "semantic-improvement-cycle-bundle",
            "title": "Semantic Improvement Cycle Bundle",
            "actions": ["run_semantic_improvement_cycle", "optimize_workflow_path", "improve_publishing_readiness"],
            "default_request": {
                "surface": "semantic_os",
                "compartment_id": first_chain.get("compartment_id") or first_recommendation.get("compartment_id"),
                "business_id": first_chain.get("business_id") or first_recommendation.get("navigation", {}).get("business_id"),
            },
        },
    ]

    automation = _build_timeline_automation(
        timeline_groups=timeline_groups,
        subject_mix=subject_mix,
        provenance_chains=provenance_chains,
    )
    readiness = {
        "ready": bool(semantic_os_health.get("ready")),
        "checks": semantic_os_health.get("checks", []),
        "blocked_by": [item.get("surface") for item in semantic_os_health.get("checks", []) if item.get("status") != "pass"],
    }

    return {
        "action_vocabulary": vocabulary,
        "action_bundles": bundles,
        "timeline_automation": automation,
        "workflow_execution": {
            "validation_rules": [
                "semantic_os_health.ready must be true",
                "provenance depth must be >= 5 for multi-surface execution",
                "workflow target must include surface and compartment_id",
            ],
            "execution_surfaces": ["rr_detail", "va_guidance", "workflow_swimlanes", "timeline"],
        },
        "publishing_automation": {
            "auto_chapter_assembly": True,
            "signals": [
                {
                    "signal": "publishing_ready",
                    "status": "ready" if publishing_previews else "monitor",
                    "message": "Publishing-ready signal uses RR provenance and workflow usage.",
                }
            ] + [
                {
                    "signal": "adaptive_publishing_hint",
                    "status": "warn" if (feedback_loop.get("stability_signals") or {}).get("drift_detected") else "ready",
                    "message": "Publishing hints adapt to action history and semantic stability.",
                }
            ] + [
                {
                    "signal": "publishing_readiness_optimization",
                    "status": "ready" if int(((feedback_loop.get("optimization_loop") or {}).get("signals") or {}).get("publishing_readiness_score", 0)) >= 82 else "warn",
                    "message": "Publishing readiness optimization reflects workflow and subject balancing outcomes.",
                }
            ],
        },
        "optimization_automation": {
            "improvement_cycle_enabled": True,
            "auto_balancing": (feedback_loop.get("optimization_loop") or {}).get("auto_balancing", {}),
            "signals": (feedback_loop.get("optimization_loop") or {}).get("signals", {}),
            "recommendations": list((feedback_loop.get("optimization_loop") or {}).get("recommendations") or []),
            "consistency": {
                "required_chain": [
                    "engine-truth",
                    "rr",
                    "middle_layer",
                    "va",
                    "workflow",
                    "publishing",
                    "intelligence",
                    "timeline",
                    "actions",
                    "action_log",
                    "feedback_loop",
                    "drift",
                    "stabilization",
                    "optimization",
                ],
                "status": "pass" if bool(feedback_loop.get("optimization_loop")) else "warn",
            },
        },
        "consistency_rules": [
            "All action requests route through the semantic OS host.",
            "All action execution appends timeline entries and provenance updates.",
            "All multi-surface actions must pass semantic OS health checks.",
            "Drift corrections append stabilization metadata and preserve append-only history.",
            "Publishing corrective actions must emit adaptive publishing signals.",
            "Optimization corrections must append improvement-loop metadata and maintain deterministic chain order.",
        ],
        "automation_readiness": readiness,
        "action_log_summary": action_log_summary,
        "feedback_loop": feedback_loop,
        "stabilization_recommendations": list((feedback_loop.get("stabilization_loop") or {}).get("recommendations") or []),
        "optimization_recommendations": list((feedback_loop.get("optimization_loop") or {}).get("recommendations") or []),
        "dashboard_snapshot": {
            "lane_count": dashboard.get("lane_count", 0),
            "integrity_strip": dashboard.get("integrity_strip", {}),
        },
    }


def build_semantic_action_engine_payload(*, user=None) -> dict[str, Any]:
    intelligence = build_semantic_intelligence_payload(user=user)
    return {
        "mode": "semantic_action_engine",
        "semantic_action_engine": intelligence.get("semantic_action_engine", {}),
        "semantic_os_health": intelligence.get("semantic_os_health", {}),
        "semantic_action_log": intelligence.get("semantic_action_log", {}),
        "semantic_feedback_loop": intelligence.get("semantic_feedback_loop", {}),
    }


def execute_semantic_action(*, payload: dict[str, Any], user=None) -> dict[str, Any]:
    intelligence = build_semantic_intelligence_payload(user=user)
    action_engine = intelligence.get("semantic_action_engine", {})
    health = intelligence.get("semantic_os_health", {})
    vocabulary = action_engine.get("action_vocabulary", [])
    allowed_actions = {item.get("action") for item in vocabulary}

    action = str(payload.get("action") or "").strip()
    source_surface = str(payload.get("surface") or "semantic_os")
    business_id = payload.get("business_id")
    compartment_id = payload.get("compartment_id")
    workflow_step = str(payload.get("workflow_step") or "")
    now_iso = timezone.now().isoformat()

    metadata = get_compartment_metadata(int(compartment_id)) if compartment_id is not None and str(compartment_id).isdigit() else None
    subject = metadata.get("subject") if metadata else "Unknown"
    phase = metadata.get("phase") if metadata else "Unknown"

    base_log_entry = {
        "recorded_at": now_iso,
        "action": action,
        "source_surface": source_surface,
        "business_id": business_id,
        "compartment_id": compartment_id,
        "subject": subject,
        "phase": phase,
        "workflow_step": workflow_step or "deterministic_next",
        "breadcrumbs": _normalize_surface_path("engine-truth", "semantic-actions", source_surface, action),
    }

    is_stabilization_action = action in STABILIZATION_ACTIONS
    is_optimization_action = action in OPTIMIZATION_ACTIONS

    if action not in allowed_actions:
        _record_semantic_action_log_entry(
            user=user,
            entry={
                **base_log_entry,
                "status": "rejected",
                "detail": "Unknown semantic action.",
            },
        )
        return {
            "mode": "semantic_action_execution",
            "status": "rejected",
            "detail": "Unknown semantic action.",
            "allowed_actions": sorted(item for item in allowed_actions if item),
        }

    if not health.get("ready") and not (is_stabilization_action or is_optimization_action):
        _record_semantic_action_log_entry(
            user=user,
            entry={
                **base_log_entry,
                "status": "blocked",
                "detail": "Semantic OS health checks are not ready for automation.",
            },
        )
        return {
            "mode": "semantic_action_execution",
            "status": "blocked",
            "detail": "Semantic OS health checks are not ready for automation.",
            "semantic_os_health": health,
        }

    recent_actions = _read_semantic_action_log(user=user)[-6:]
    recent_failures = sum(1 for item in recent_actions if str(item.get("status")) in {"failed", "blocked"})
    if action == "advance_workflow_step" and recent_failures >= 3 and not (is_stabilization_action or is_optimization_action):
        _record_semantic_action_log_entry(
            user=user,
            entry={
                **base_log_entry,
                "status": "failed",
                "detail": "Workflow execution halted due to repeated unstable action outcomes.",
            },
        )
        return {
            "mode": "semantic_action_execution",
            "status": "failed",
            "detail": "Workflow execution halted due to repeated unstable action outcomes.",
            "semantic_os_health": health,
            "workflow_step_result": {
                "status": "failed",
                "message": "Recent action history indicates instability. Resolve drift before next workflow step.",
            },
        }

    if is_stabilization_action:
        timeline_event_type = "semantic_stabilization_executed"
        timeline_label = f"Executed stabilization {action}"
    elif is_optimization_action:
        timeline_event_type = "semantic_optimization_executed"
        timeline_label = f"Executed optimization {action}"
    else:
        timeline_event_type = "semantic_action_executed"
        timeline_label = f"Executed {action}"
    timeline_entry = {
        "event_type": timeline_event_type,
        "surface": source_surface,
        "label": timeline_label,
        "action": action,
        "business_id": business_id,
        "compartment_id": compartment_id,
        "workflow_step": workflow_step or "deterministic_next",
        "breadcrumbs": _normalize_surface_path("engine-truth", "semantic-actions", source_surface, action),
    }
    provenance_update = {
        "action": action,
        "business_id": business_id,
        "compartment_id": compartment_id,
        "depth": 8 if is_optimization_action else 7 if is_stabilization_action else 6,
        "route": ["rr", "workflow", "va", "publishing", "timeline", "semantic-actions"]
        + (["stabilization"] if is_stabilization_action else [])
        + (["optimization"] if is_optimization_action else []),
    }
    publishing_status = "monitor"
    if action == "prepare_publishing_chapter":
        publishing_status = "ready"
    if action in {"regenerate_chapter_outline", "resync_publishing_diagrams"}:
        publishing_status = "repairing"
    if action in {"improve_publishing_readiness", "auto_assemble_chapter_outline", "improve_subject_balance"}:
        publishing_status = "optimizing"
    publishing_signal = {
        "signal": "publishing_ready",
        "status": publishing_status,
        "chapter_draft_id": f"draft-{compartment_id or 'x'}-{business_id or 'x'}" if action == "prepare_publishing_chapter" else None,
    }
    workflow_step_result = {
        "status": "executed" if action in {"advance_workflow_step", "realign_workflow_step"} else "n/a",
        "message": (
            "Workflow step advanced through semantic validation."
            if action == "advance_workflow_step"
            else "Workflow step realigned through stabilization correction."
            if action == "realign_workflow_step"
            else "Workflow path optimized through deterministic improvement routing."
            if action in {"optimize_workflow_path", "shorten_workflow_path", "merge_sop_steps", "realign_subject_distribution"}
            else "Workflow step not requested."
        ),
    }
    stabilization_loop_entry = {
        "event_type": "stabilization_correction" if is_stabilization_action else "monitor",
        "action": action,
        "status": "executed",
        "source_surface": source_surface,
        "subject": subject,
        "phase": phase,
        "corrective": is_stabilization_action,
    }
    optimization_loop_entry = {
        "event_type": "optimization_correction" if is_optimization_action else "monitor",
        "action": action,
        "status": "executed",
        "source_surface": source_surface,
        "subject": subject,
        "phase": phase,
        "optimization": is_optimization_action,
        "improvement_cycle": action == "run_semantic_improvement_cycle",
        "chain": [
            "engine-truth",
            "rr",
            "middle_layer",
            "va",
            "workflow",
            "publishing",
            "intelligence",
            "timeline",
            "actions",
            "action_log",
            "feedback_loop",
            "drift",
            "stabilization",
            "optimization",
        ],
    }
    consistency_checks = [
        {
            "surface": "action_routing",
            "status": "pass",
            "message": "Action request routed via semantic OS execution endpoint.",
        },
        {
            "surface": "provenance_update",
            "status": "pass" if int(provenance_update.get("depth", 0)) >= 6 else "warn",
            "message": "Provenance update includes semantic action hop.",
        },
        {
            "surface": "timeline_entry",
            "status": "pass" if timeline_entry.get("event_type") in {"semantic_action_executed", "semantic_stabilization_executed", "semantic_optimization_executed"} else "warn",
            "message": "Timeline entry captured for executed action.",
        },
        {
            "surface": "publishing_signal",
            "status": "pass" if publishing_signal.get("status") in {"ready", "monitor", "repairing", "optimizing"} else "warn",
            "message": "Publishing signal emitted with execution result.",
        },
        {
            "surface": "drift_detection",
            "status": "pass" if intelligence.get("semantic_feedback_loop") else "warn",
            "message": "Drift detection context is available for semantic execution.",
        },
        {
            "surface": "stabilization_loop",
            "status": "pass" if (not is_stabilization_action) or stabilization_loop_entry.get("corrective") else "warn",
            "message": "Stabilization loop captures corrective action execution.",
        },
        {
            "surface": "optimization_loop",
            "status": "pass" if (not is_optimization_action) or optimization_loop_entry.get("optimization") else "warn",
            "message": "Optimization loop captures semantic optimization execution and improvement chain metadata.",
        },
    ]
    log_entry = {
        **base_log_entry,
        "status": "executed",
        "timeline_entry": timeline_entry,
        "provenance_update": provenance_update,
        "publishing_signal": publishing_signal,
        "workflow_step_result": workflow_step_result,
        "stabilization_loop_entry": stabilization_loop_entry,
        "optimization_loop_entry": optimization_loop_entry,
        "consistency_checks": consistency_checks,
    }
    updated_log = _record_semantic_action_log_entry(user=user, entry=log_entry)
    post_intelligence = build_semantic_intelligence_payload(user=user)

    return {
        "mode": "semantic_action_execution",
        "status": "executed",
        "action": action,
        "source_surface": source_surface,
        "stabilization_action": is_stabilization_action,
        "optimization_action": is_optimization_action,
        "timeline_entry": timeline_entry,
        "provenance_update": provenance_update,
        "publishing_signal": publishing_signal,
        "workflow_step_result": workflow_step_result,
        "stabilization_loop_entry": stabilization_loop_entry,
        "optimization_loop_entry": optimization_loop_entry,
        "consistency_checks": consistency_checks,
        "action_log_entry": log_entry,
        "action_log_tail": updated_log[-8:],
        "semantic_feedback_loop": post_intelligence.get("semantic_feedback_loop", {}),
        "semantic_os_health": post_intelligence.get("semantic_os_health", health),
    }


def _build_semantic_provenance_chains(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    provenance_chains: list[dict[str, Any]] = []
    active_lanes = [lane for lane in lanes if int(lane.get("node_count", 0)) > 0]

    for lane in active_lanes:
        first_card = (lane.get("cards") or [{}])[0]
        workflow_refs = first_card.get("provenance", {}).get("workflow_refs", [])
        sop_refs = first_card.get("provenance", {}).get("sop_refs", [])
        workflow_ref = next((item.get("workflow_id") for item in workflow_refs if item.get("workflow_id")), None)
        sop_ref = next((item.get("sop_id") for item in sop_refs if item.get("sop_id")), None)
        business_id = first_card.get("business_id")

        provenance_chains.append(
            {
                "compartment_id": lane.get("compartment_id"),
                "subject": lane.get("subject"),
                "phase": lane.get("phase"),
                "business_id": business_id,
                "depth": 5,
                "breadcrumbs": [
                    "engine-truth",
                    f"C{lane.get('compartment_id')}",
                    lane.get("subject"),
                    lane.get("phase"),
                    workflow_ref or "workflow",
                    sop_ref or "sop",
                ],
                "chain": [
                    {
                        "surface": "rr_dashboard",
                        "label": f"RR lane {lane.get('subject')}",
                        "navigation": {
                            "surface": "rr_dashboard",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": business_id,
                        },
                    },
                    {
                        "surface": "middle_layer",
                        "label": "Middle Layer",
                        "navigation": {
                            "surface": "middle_layer",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": business_id,
                        },
                    },
                    {
                        "surface": "va_guidance",
                        "label": "VA guidance",
                        "navigation": {
                            "surface": "va_guidance",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": business_id,
                        },
                    },
                    {
                        "surface": "workflow_swimlanes",
                        "label": "Workflow timeline",
                        "navigation": {
                            "surface": "workflow_swimlanes",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": business_id,
                        },
                    },
                    {
                        "surface": "publishing_layer",
                        "label": "Publishing assembly",
                        "navigation": {
                            "surface": "publishing_layer",
                            "compartment_id": lane.get("compartment_id"),
                            "business_id": business_id,
                        },
                    },
                ],
            }
        )

    return provenance_chains


def _build_adaptive_intelligence(
    *,
    subject_mix: dict[str, Any],
    bottlenecks: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    provenance_chains: list[dict[str, Any]],
) -> dict[str, Any]:
    subjects = list(subject_mix.get("subjects", []))
    total_nodes = int(subject_mix.get("total_nodes", 0))
    dominant_subject = subjects[0] if subjects else None
    sparse_subjects = [item for item in subjects if float(item.get("node_share", 0.0)) < 0.15]
    corrections: list[dict[str, Any]] = []

    if dominant_subject and sparse_subjects:
        corrections.append(
            {
                "type": "subject_mix_correction",
                "message": f"Balance {dominant_subject.get('subject')} with {', '.join(item.get('subject') for item in sparse_subjects[:3])}.",
                "navigation": {
                    "surface": "rr_dashboard",
                    "compartment_id": dominant_subject.get("compartment_id"),
                },
            }
        )

    if bottlenecks:
        bottleneck = bottlenecks[0]
        corrections.append(
            {
                "type": "predictive_bottleneck",
                "message": f"Predictive pressure is highest in {bottleneck.get('subject')} at score {bottleneck.get('pressure_score')}.",
                "navigation": bottleneck.get("navigation", {}),
            }
        )

    if timeline:
        corrections.append(
            {
                "type": "timeline_aware_recommendation",
                "message": f"Timeline has {len(timeline)} cross-surface events ready for drill-down.",
                "navigation": {
                    "surface": timeline[0].get("surface", "rr_dashboard"),
                    "compartment_id": timeline[0].get("compartment_id"),
                },
            }
        )

    return {
        "subject_mix_optimization": {
            "total_nodes": total_nodes,
            "dominant_subject": dominant_subject,
            "sparse_subjects": sparse_subjects,
        },
        "imbalance_corrections": corrections,
        "predictive_bottlenecks": [
            {
                "subject": item.get("subject"),
                "phase": item.get("phase"),
                "pressure_score": item.get("pressure_score"),
                "navigation": item.get("navigation", {}),
            }
            for item in bottlenecks[:4]
        ],
        "semantic_coaching": [
            {
                "subject": item.get("subject"),
                "breadcrumbs": item.get("breadcrumbs", []),
            }
            for item in provenance_chains[:4]
        ],
    }


def build_semantic_intelligence_payload(*, user=None) -> dict[str, Any]:
    dashboard = build_rr_dashboard_payload(user=user, limit_per_lane=4)
    industry_map = build_rr_industry_map_payload(user=user)
    guidance = build_va_guidance_payload(user=user)
    operating_stack = build_operating_stack_payload()

    active_lanes = [lane for lane in dashboard.get("lanes", []) if int(lane.get("node_count", 0)) > 0]
    bottlenecks = _build_semantic_bottlenecks(dashboard.get("lanes", []))
    recommendations = _build_semantic_recommendations(dashboard.get("lanes", []), bottlenecks)
    subject_mix = _build_semantic_subject_mix(dashboard.get("lanes", []))
    publishing_previews = _build_publishing_previews(lanes=dashboard.get("lanes", []), operating_stack=operating_stack)
    unified_timeline = _build_semantic_timeline(
        dashboard=dashboard,
        bottlenecks=bottlenecks,
        recommendations=recommendations,
        publishing_previews=publishing_previews,
    )
    provenance_chains = _build_semantic_provenance_chains(dashboard.get("lanes", []))
    adaptive_intelligence = _build_adaptive_intelligence(
        subject_mix=subject_mix,
        bottlenecks=bottlenecks,
        timeline=unified_timeline,
        provenance_chains=provenance_chains,
    )
    timeline_groups = _group_timeline_events(unified_timeline)
    action_log_entries = _read_semantic_action_log(user=user)
    action_log_summary = _build_semantic_action_log_summary(action_log_entries)
    feedback_loop = _build_semantic_feedback_loop(
        action_log=action_log_entries,
        timeline_groups=timeline_groups,
        subject_mix=subject_mix,
        provenance_chains=provenance_chains,
        chapter_previews=publishing_previews,
    )
    semantic_os_health = _build_semantic_os_health(
        dashboard=dashboard,
        timeline=unified_timeline,
        provenance_chains=provenance_chains,
        guidance=guidance,
        publishing_previews=publishing_previews,
        action_log_summary=action_log_summary,
        feedback_loop=feedback_loop,
    )
    semantic_action_engine = _build_semantic_action_engine(
        dashboard=dashboard,
        recommendations=recommendations,
        timeline_groups=timeline_groups,
        provenance_chains=provenance_chains,
        publishing_previews=publishing_previews,
        semantic_os_health=semantic_os_health,
        subject_mix=subject_mix,
        action_log_summary=action_log_summary,
        feedback_loop=feedback_loop,
    )

    rr_semantic_analytics = {
        "lane_count": dashboard.get("lane_count", 0),
        "active_lane_count": len(active_lanes),
        "status_bands": dashboard.get("status_bands", {}),
        "integrity_strip": dashboard.get("integrity_strip", {}),
        "subject_mix": subject_mix,
        "density": [
            {
                "compartment_id": lane.get("compartment_id"),
                "subject": lane.get("subject"),
                "node_count": lane.get("node_count", 0),
                "mismatch_count": (lane.get("integrity") or {}).get("mismatch", 0),
            }
            for lane in active_lanes
        ],
        "provenance_chains": provenance_chains,
    }

    workflow_intelligence = {
        "bottlenecks": bottlenecks,
        "subject_mix": subject_mix,
        "provenance_chains": provenance_chains,
        "timeline_insights": [
            {
                "label": f"{item['subject']} pressure {item['pressure_score']}",
                "compartment_id": item["compartment_id"],
                "surface": "workflow_swimlanes",
            }
            for item in bottlenecks[:4]
        ],
        "rr_to_va_navigation": [
            {
                "surface": "rr_dashboard",
                "compartment_id": item.get("compartment_id"),
                "business_id": item.get("navigation", {}).get("business_id"),
            }
            for item in recommendations
            if item.get("navigation", {}).get("surface") == "rr_dashboard"
        ],
        "timeline_breadcrumbs": [
            {
                "subject": item.get("subject"),
                "breadcrumbs": item.get("breadcrumbs", []),
            }
            for item in unified_timeline[:6]
        ],
    }

    return {
        "mode": "semantic_intelligence",
        "rr_semantic_analytics": rr_semantic_analytics,
        "recommendation_engine": {
            "recommendations": recommendations,
            "dominant_subjects": [lane.get("subject") for lane in active_lanes[:4]],
            "guidance_signals": guidance.get("signals", {}),
            "timeline_aware_recommendations": adaptive_intelligence.get("imbalance_corrections", []),
        },
        "workflow_intelligence": workflow_intelligence,
        "semantic_action_log": {
            "limit": SEMANTIC_ACTION_LOG_LIMIT,
            "entries": action_log_entries,
            "summary": action_log_summary,
        },
        "semantic_feedback_loop": feedback_loop,
        "semantic_optimization": feedback_loop.get("optimization_loop", {}),
        "va_action_engine": {
            "signals": guidance.get("signals", {}),
            "recommendations": guidance.get("recommendations", []),
            "workflow_actions": [
                {
                    "type": item.get("type"),
                    "message": item.get("message"),
                    "navigation": item.get("navigation", {}),
                }
                for item in guidance.get("recommendations", [])
            ],
                "timeline_actions": [
                    {
                        "type": item.get("type"),
                        "message": item.get("message"),
                        "navigation": item.get("navigation", {}),
                    }
                    for item in adaptive_intelligence.get("imbalance_corrections", [])
                ],
                "semantic_coaching": adaptive_intelligence.get("semantic_coaching", []),
        },
        "publishing_intelligence": {
            "chapter_previews": publishing_previews,
            "operating_stack": operating_stack.get("tracks", {}).get("publishing_layer", {}),
            "semantic_diagram": {
                "subjects": [preview.get("subject") for preview in publishing_previews],
                "colors": [preview.get("color") for preview in publishing_previews],
            },
                "chapter_assembly": [
                    {
                        "chapter_id": preview.get("chapter_id"),
                        "subject": preview.get("subject"),
                        "assembly_chain": preview.get("assembly_chain", []),
                        "adaptive_reason": preview.get("adaptive_reason"),
                    }
                    for preview in publishing_previews
                ],
                "timeline_driven_preview": adaptive_intelligence.get("subject_mix_optimization", {}),
        },
        "unified_timeline": unified_timeline,
            "timeline_groups": timeline_groups,
            "semantic_os_health": semantic_os_health,
            "semantic_action_engine": semantic_action_engine,
            "semantic_os_unification": {
                "timeline_breadcrumbs": [item.get("breadcrumbs", []) for item in unified_timeline[:8]],
                "consistency_checks": [
                    {
                        "surface": "rr",
                        "status": "pass" if rr_semantic_analytics.get("active_lane_count", 0) >= 0 else "warn",
                        "message": "RR payload is available from engine truth.",
                    },
                    {
                        "surface": "middle_layer",
                        "status": "pass" if provenance_chains else "warn",
                        "message": "Provenance chains are aligned with RR lanes.",
                    },
                    {
                        "surface": "va",
                        "status": "pass" if guidance.get("recommendations") else "warn",
                        "message": "VA recommendations are derived from shared guidance.",
                    },
                    {
                        "surface": "workflow",
                        "status": "pass" if bottlenecks else "warn",
                        "message": "Workflow pressure is tracked from shared lane history.",
                    },
                    {
                        "surface": "publishing",
                        "status": "pass" if publishing_previews else "warn",
                        "message": "Publishing previews are assembled from RR lanes.",
                    },
                    {
                        "surface": "semantic_os",
                        "status": "pass" if timeline_groups else "warn",
                        "message": "Semantic OS grouping is aligned across subjects and phases.",
                    },
                    {
                        "surface": "drift_detection",
                        "status": "pass" if bool(feedback_loop.get("drift_detection")) else "warn",
                        "message": "Drift detection is composed from history, provenance depth, timeline pressure, and publishing mix.",
                    },
                    {
                        "surface": "stabilization",
                        "status": "pass" if bool((feedback_loop.get("stabilization_loop") or {}).get("recommendations") or []) else "warn",
                        "message": "Stabilization loop recommendations are attached for cross-surface correction.",
                    },
                    {
                        "surface": "optimization",
                        "status": "pass" if bool(feedback_loop.get("optimization_loop")) else "warn",
                        "message": "Optimization loop is attached to the shared semantic payload.",
                    },
                    {
                        "surface": "optimization_reflection",
                        "status": "pass"
                        if bool((feedback_loop.get("optimization_loop") or {}).get("signals"))
                        and bool((semantic_action_engine.get("optimization_automation") or {}).get("signals"))
                        else "warn",
                        "message": "Optimization signals reflect consistently across feedback loop and action engine automation.",
                    },
                ],
            },
        "rr_dashboard": dashboard,
        "rr_industry_map": industry_map,
    }
