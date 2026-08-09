import json
from pathlib import Path

from django.db import models

from project_middle_layer.models import ProjectEvolutionSnapshot, ProjectNode, SemanticAlert, SemanticLineageRecord
from project_middle_layer.lfo_engine import build_lfo_engine_envelope
from project_middle_layer.pipelines import build_project_creation_payload
from project_middle_layer.semantic import build_semantic_alerts
from project_middle_layer.webhooks import dispatch_semantic_webhook_event
from polish.task_manager.constants import ASSIGNMENT_TWELVE_POINT
from polish.task_manager.routing import build_middle_layer_compartment_drift_detection
from platform_core.models import MLASClassificationRecord
from platform_reference.models import PlatformReferenceGICSReferenceSchema
from platform_reference.models import PlatformReferenceNAICSReferenceSchema
from platform_reference.services.reference_sync import get_gics_source_status
from seeds.rr_visual_system import build_rr_dashboard_payload


CALCULUS_OPERATION_BY_TEMPORAL_ALIGNMENT = {
    "past": {
        "operation": "Integral",
        "middle_layer_semantic_function": "consolidate_context",
        "keywords": ["history", "accumulate", "integrate", "foundation", "context"],
    },
    "present-past": {
        "operation": "Continuity",
        "middle_layer_semantic_function": "preserve_semantic_lineage",
        "keywords": ["continuity", "handoff", "bridge", "sequence", "lineage"],
    },
    "present-future": {
        "operation": "Limit",
        "middle_layer_semantic_function": "evaluate_boundary_conditions",
        "keywords": ["threshold", "constraint", "readiness", "gate", "boundary"],
    },
    "future": {
        "operation": "Derivative",
        "middle_layer_semantic_function": "derive_next_action",
        "keywords": ["next", "delta", "optimize", "forecast", "trajectory"],
    },
}

TEMPORAL_ALIGNMENT_KEYWORDS = {
    "past": ["past", "history", "retrospective", "archive"],
    "present-past": ["present", "handoff", "carry", "continuity"],
    "present-future": ["transition", "plan", "preparation", "readiness"],
    "future": ["future", "forecast", "expand", "growth"],
}

TIMELINE_PHASES = [
    {"id": 1, "name": "Ideas", "slot_start": 1, "slot_end": 4, "family": "idea"},
    {"id": 2, "name": "Seeds", "slot_start": 5, "slot_end": 8, "family": "seed"},
    {"id": 3, "name": "Projects", "slot_start": 9, "slot_end": 12, "family": "project"},
    {"id": 4, "name": "MVP", "slot_start": 13, "slot_end": 16, "family": "mvp"},
]

TEMPORAL_ALIGNMENT_ORDER = ["past", "present-past", "present-future", "future"]


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize_slot_index(value: object) -> int:
    try:
        index = int(value)
    except (TypeError, ValueError):
        return 1
    if index < 1:
        return 1
    if index > 16:
        return 16
    return index


def _normalize_completed_slots(completed_slots: object) -> list[int]:
    normalized: list[int] = []
    values = completed_slots if isinstance(completed_slots, list) else []
    for value in values:
        try:
            index = int(value)
        except (TypeError, ValueError):
            continue
        if index < 1 or index > 16:
            continue
        if index not in normalized:
            normalized.append(index)
    normalized.sort()
    return normalized


def _tokenize(text: object) -> set[str]:
    raw = str(text or "").strip().lower()
    cleaned = raw
    for token in [",", ".", ":", ";", "(", ")", "[", "]", "{", "}", "/", "\\", "-", "_"]:
        cleaned = cleaned.replace(token, " ")
    return {chunk for chunk in cleaned.split() if chunk}


def _keyword_alignment_score(content_tokens: set[str], keywords: list[str]) -> float:
    if not keywords:
        return 0.5
    if not content_tokens:
        return 0.5

    normalized_keywords = {str(item).strip().lower() for item in keywords if str(item).strip()}
    if not normalized_keywords:
        return 0.5

    matched = 0
    for keyword in normalized_keywords:
        keyword_tokens = _tokenize(keyword)
        if keyword_tokens and keyword_tokens.intersection(content_tokens):
            matched += 1
    return _clamp_score(matched / len(normalized_keywords))


def _resolve_phase(slot_index: int) -> dict[str, object]:
    for phase in TIMELINE_PHASES:
        if int(phase["slot_start"]) <= slot_index <= int(phase["slot_end"]):
            return phase
    return TIMELINE_PHASES[0]


def _load_macro_industry_groups() -> list[dict[str, object]]:
    catalog_path = (
        Path(__file__).resolve().parent.parent
        / "platform_semantic"
        / "catalogs"
        / "macro_map.json"
    )

    # Support the current project layout where project_middle_layer and
    # platform_semantic are sibling apps at repo root.
    if not catalog_path.exists():
        catalog_path = Path(__file__).resolve().parent.parent.parent / "platform_semantic" / "catalogs" / "macro_map.json"

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
            subject_name = str(group.get("subject_name") or "")
            industries: list[dict[str, object]] = []
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
                    "group_name": subject_name,
                    "industries": industries,
                }
            )

    flattened.sort(key=lambda item: int(item.get("group_id") or 0))
    return flattened


def _resolve_slot_industry_context(
    *,
    slot_index: int,
    group_metadata: dict[str, object],
    industry_context: dict[str, object],
) -> dict[str, object]:
    industries = group_metadata.get("industries", []) if isinstance(group_metadata, dict) else []
    selected_industry = industries[0] if industries else {"industry_name": "", "sub_industries": []}

    slot_overrides = industry_context.get("slot_overrides", {}) if isinstance(industry_context, dict) else {}
    slot_override = slot_overrides.get(str(slot_index), {}) if isinstance(slot_overrides, dict) else {}

    requested_industry_name = str(
        slot_override.get("industry")
        or industry_context.get("industry")
        or ""
    ).strip()

    if requested_industry_name:
        for industry in industries:
            if str(industry.get("industry_name") or "").strip().lower() == requested_industry_name.lower():
                selected_industry = industry
                break

    requested_sub_industry = str(
        slot_override.get("sub_industry")
        or industry_context.get("sub_industry")
        or ""
    ).strip()

    sub_industries = selected_industry.get("sub_industries", []) if isinstance(selected_industry, dict) else []
    selected_sub_industry = sub_industries[0] if sub_industries else ""
    if requested_sub_industry:
        for sub_industry in sub_industries:
            if str(sub_industry).strip().lower() == requested_sub_industry.lower():
                selected_sub_industry = sub_industry
                break

    return {
        "sector_id": int(group_metadata.get("sector_id") or 0),
        "sector_name": str(group_metadata.get("sector_name") or ""),
        "group_id": int(group_metadata.get("group_id") or slot_index),
        "group_name": str(group_metadata.get("group_name") or ""),
        "industry": str(selected_industry.get("industry_name") or ""),
        "sub_industry": str(selected_sub_industry or ""),
        "available_industries": [str(item.get("industry_name") or "") for item in industries],
    }


def _phase_gate_states(completed_slots: list[int]) -> list[dict[str, object]]:
    phase_one_complete = all(slot in completed_slots for slot in range(1, 5))
    phase_two_complete = all(slot in completed_slots for slot in range(5, 9))
    phase_three_complete = all(slot in completed_slots for slot in range(9, 13))

    return [
        {
            "phase": "Ideas",
            "slot_range": [1, 4],
            "locked": False,
            "unlock_condition": "always_unlocked",
            "condition_met": True,
        },
        {
            "phase": "Seeds",
            "slot_range": [5, 8],
            "locked": not phase_one_complete,
            "unlock_condition": "complete_slots_1_to_4",
            "condition_met": phase_one_complete,
        },
        {
            "phase": "Projects",
            "slot_range": [9, 12],
            "locked": not phase_two_complete,
            "unlock_condition": "complete_slots_5_to_8",
            "condition_met": phase_two_complete,
        },
        {
            "phase": "MVP",
            "slot_range": [13, 16],
            "locked": not phase_three_complete,
            "unlock_condition": "complete_slots_9_to_12",
            "condition_met": phase_three_complete,
        },
    ]


def build_calculus_timeline_runtime_payload(
    *,
    selected_slot: int = 1,
    completed_slots: list[int] | None = None,
    slot_content: dict[str, object] | None = None,
    industry_context: dict[str, object] | None = None,
    prior_slot_states: dict[str, object] | None = None,
) -> dict[str, object]:
    selected_slot = _normalize_slot_index(selected_slot)
    completed_slots = _normalize_completed_slots(completed_slots or [])
    slot_content = slot_content if isinstance(slot_content, dict) else {}
    industry_context = industry_context if isinstance(industry_context, dict) else {}
    prior_slot_states = prior_slot_states if isinstance(prior_slot_states, dict) else {}

    group_catalog = _load_macro_industry_groups()
    group_by_id = {int(item.get("group_id") or 0): item for item in group_catalog}
    phase_gates = _phase_gate_states(completed_slots)
    gate_by_phase_name = {str(item.get("phase") or ""): item for item in phase_gates}

    slots: list[dict[str, object]] = []
    events: list[dict[str, object]] = []

    for slot_index in range(1, 17):
        phase = _resolve_phase(slot_index)
        phase_name = str(phase["name"])
        phase_gate = gate_by_phase_name.get(phase_name, {})
        temporal_alignment = TEMPORAL_ALIGNMENT_ORDER[(slot_index - 1) % 4]
        calculus_rule = CALCULUS_OPERATION_BY_TEMPORAL_ALIGNMENT[temporal_alignment]
        group_metadata = group_by_id.get(slot_index, {
            "sector_id": 0,
            "sector_name": "",
            "group_id": slot_index,
            "group_name": "",
            "industries": [],
        })
        industry_metadata = _resolve_slot_industry_context(
            slot_index=slot_index,
            group_metadata=group_metadata,
            industry_context=industry_context,
        )

        content = slot_content.get(str(slot_index)) or slot_content.get(slot_index) or ""
        tokens = _tokenize(content)
        calculus_alignment = _keyword_alignment_score(tokens, calculus_rule["keywords"])
        temporal_alignment_score = _keyword_alignment_score(tokens, TEMPORAL_ALIGNMENT_KEYWORDS[temporal_alignment])
        industry_keywords = [
            industry_metadata.get("group_name", ""),
            industry_metadata.get("industry", ""),
            industry_metadata.get("sub_industry", ""),
        ]
        industry_alignment = _keyword_alignment_score(tokens, [item for item in industry_keywords if item])

        alignment_score = _clamp_score((calculus_alignment + temporal_alignment_score + industry_alignment) / 3.0)
        drift_score = _clamp_score(1.0 - alignment_score)

        prior_state = prior_slot_states.get(str(slot_index), {})
        prior_drift = prior_state.get("drift_score") if isinstance(prior_state, dict) else None
        try:
            prior_drift_value = float(prior_drift)
            stability_score = _clamp_score(1.0 - abs(drift_score - prior_drift_value))
        except (TypeError, ValueError):
            stability_score = _clamp_score(1.0 - (drift_score * 0.6))

        gate_locked = bool(phase_gate.get("locked", False))
        completed = slot_index in completed_slots
        drift_band = "low"
        if drift_score >= 0.67:
            drift_band = "high"
        elif drift_score >= 0.34:
            drift_band = "medium"

        semantic_tags = [
            f"calculus:{str(calculus_rule['operation']).lower()}",
            f"temporal:{temporal_alignment}",
            f"phase:{str(phase.get('family') or '').lower()}",
            f"group:{str(industry_metadata.get('group_name') or '').lower().replace(' ', '-')}",
            f"industry:{str(industry_metadata.get('industry') or '').lower().replace(' ', '-')}",
        ]

        micro_signals = [
            {"signal": "drift_band", "value": drift_band},
            {"signal": "calculus_alignment", "value": round(calculus_alignment, 3)},
            {"signal": "temporal_alignment", "value": round(temporal_alignment_score, 3)},
            {"signal": "industry_alignment", "value": round(industry_alignment, 3)},
            {"signal": "phase_gate", "value": "locked" if gate_locked else "unlocked"},
        ]

        state = {
            "drift_score": round(drift_score, 3),
            "stability_score": round(stability_score, 3),
            "alignment_score": round(alignment_score, 3),
            "semantic_tags": semantic_tags,
            "micro_signals": micro_signals,
            "va_guidance": (
                "Hold this slot until upstream phase gates are complete."
                if gate_locked
                else "Proceed with semantic refinement and maintain calculus-temporal alignment."
            ),
        }

        slot_payload = {
            "slot_index": slot_index,
            "row_phase": int(phase["id"]),
            "col_slot": ((slot_index - 1) % 4) + 1,
            "phase": phase_name,
            "family": str(phase.get("family") or ""),
            "temporal_alignment": temporal_alignment,
            "calculus_operation": calculus_rule["operation"],
            "middle_layer_semantic_function": calculus_rule["middle_layer_semantic_function"],
            "industry_metadata": industry_metadata,
            "state": state,
            "gate": {
                "locked": gate_locked,
                "reason": "Complete all slots in previous phase first." if gate_locked else "unlocked",
            },
            "completed": completed,
            "event": {
                "event_type": "middle_layer.timeline.slot_state",
                "event_version": "v1",
                "source": "project_middle_layer.calculus_timeline_runtime",
                "slot_index": slot_index,
                "phase": phase_name,
                "temporal_alignment": temporal_alignment,
                "calculus_operation": calculus_rule["operation"],
                "gate_locked": gate_locked,
                "slot_completed": completed,
                "drift_score": round(drift_score, 3),
                "stability_score": round(stability_score, 3),
                "alignment_score": round(alignment_score, 3),
                "industry": industry_metadata.get("industry", ""),
                "industry_metadata": {
                    "group_id": industry_metadata.get("group_id"),
                    "group_name": industry_metadata.get("group_name"),
                    "industry": industry_metadata.get("industry"),
                    "sub_industry": industry_metadata.get("sub_industry"),
                },
                "semantic_state": {
                    "drift_score": round(drift_score, 3),
                    "stability_score": round(stability_score, 3),
                    "alignment_score": round(alignment_score, 3),
                },
                "completed_slots": completed_slots,
            },
        }
        slots.append(slot_payload)

        prior_locked = bool(prior_state.get("gate_locked", False)) if isinstance(prior_state, dict) else False
        prior_completed = bool(prior_state.get("completed", False)) if isinstance(prior_state, dict) else False
        prior_alignment = prior_state.get("alignment_score") if isinstance(prior_state, dict) else None
        changed = False
        if bool(gate_locked) != prior_locked:
            changed = True
        if bool(completed) != prior_completed:
            changed = True
        try:
            if abs(float(prior_alignment) - alignment_score) >= 0.01:
                changed = True
        except (TypeError, ValueError):
            changed = changed or bool(prior_state)

        if changed:
            events.append(
                {
                    "event_type": "middle_layer.timeline.slot_state_changed",
                    "event_version": "v1",
                    "source": "project_middle_layer.calculus_timeline_runtime",
                    "slot_index": slot_index,
                    "phase": phase_name,
                    "temporal_alignment": temporal_alignment,
                    "calculus_operation": calculus_rule["operation"],
                    "gate_locked": gate_locked,
                    "slot_completed": completed,
                    "alignment_score": round(alignment_score, 3),
                    "drift_score": round(drift_score, 3),
                    "stability_score": round(stability_score, 3),
                    "industry_metadata": {
                        "group_id": industry_metadata.get("group_id"),
                        "group_name": industry_metadata.get("group_name"),
                        "industry": industry_metadata.get("industry"),
                        "sub_industry": industry_metadata.get("sub_industry"),
                    },
                    "semantic_state": {
                        "drift_score": round(drift_score, 3),
                        "stability_score": round(stability_score, 3),
                        "alignment_score": round(alignment_score, 3),
                    },
                    "completed_slots": completed_slots,
                }
            )

    selected = next((item for item in slots if int(item["slot_index"]) == selected_slot), slots[0])

    return {
        "mode": "calculus_temporal_timeline_runtime",
        "timeline": {
            "slot_count": 16,
            "phase_count": 4,
            "temporal_alignments": TEMPORAL_ALIGNMENT_ORDER,
            "calculus_operations": ["Integral", "Continuity", "Limit", "Derivative"],
        },
        "deterministic_progression": {
            "rules": [
                "ideas_1_to_4_before_seeds_5_to_8",
                "seeds_5_to_8_before_projects_9_to_12",
                "projects_9_to_12_before_mvp_13_to_16",
            ],
            "completed_slots": completed_slots,
            "phase_gates": phase_gates,
        },
        "selected_slot": selected_slot,
        "selected_slot_state": selected,
        "slots": slots,
        "events": events,
    }


def build_middle_layer_rr_color_context() -> dict[str, object]:
    rr_payload = build_rr_dashboard_payload(limit_per_lane=3)
    active_lanes = [lane for lane in rr_payload.get("lanes", []) if lane.get("node_count", 0) > 0]
    active_lanes.sort(key=lambda lane: int(lane.get("node_count", 0)), reverse=True)
    dominant = [
        {
            "compartment_id": lane.get("compartment_id"),
            "subject": lane.get("subject"),
            "phase": lane.get("phase"),
            "node_count": lane.get("node_count"),
            "integrity": lane.get("integrity", {}),
            "display_anchor_band": lane.get("display_anchor_band", {}),
        }
        for lane in active_lanes[:6]
    ]

    return {
        "lane_count": rr_payload.get("lane_count", 0),
        "status_bands": rr_payload.get("status_bands", {}),
        "integrity_strip": rr_payload.get("integrity_strip", {}),
        "dominant_lanes": dominant,
    }


def dispatch_calculus_timeline_runtime_events(payload: dict[str, object]) -> int:
    if not isinstance(payload, dict):
        return 0

    progression = payload.get("deterministic_progression", {})
    completed_slots = progression.get("completed_slots", []) if isinstance(progression, dict) else []
    phase_gates = progression.get("phase_gates", []) if isinstance(progression, dict) else []

    dispatch_count = 0
    priority_rank = {"critical": 0, "warn": 1, "info": 2}
    event_type_rank = {
        "middle_layer.timeline.drift_threshold": 1,
        "middle_layer.timeline.alignment_shift": 2,
        "middle_layer.timeline.slot_completion": 3,
        "middle_layer.timeline.gate_unlock": 4,
        "middle_layer.timeline.slot_state_changed": 5,
        "middle_layer.timeline.slot_state": 6,
    }

    def _derive_orchestration_events(timeline_event: dict[str, object]) -> list[dict[str, object]]:
        if not isinstance(timeline_event, dict):
            return []

        derived_events: list[dict[str, object]] = []
        event_type = str(timeline_event.get("event_type") or "")
        if event_type not in {"middle_layer.timeline.slot_state", "middle_layer.timeline.slot_state_changed"}:
            return derived_events

        slot_completed = bool(timeline_event.get("slot_completed"))
        gate_locked = bool(timeline_event.get("gate_locked"))

        try:
            slot_index = int(timeline_event.get("slot_index") or 0)
        except (TypeError, ValueError):
            slot_index = 0

        try:
            drift_score = float(
                timeline_event.get("drift_score")
                if timeline_event.get("drift_score") is not None
                else timeline_event.get("semantic_state", {}).get("drift_score", 0)
            )
        except (TypeError, ValueError, AttributeError):
            drift_score = 0.0

        try:
            alignment_score = float(
                timeline_event.get("alignment_score")
                if timeline_event.get("alignment_score") is not None
                else timeline_event.get("semantic_state", {}).get("alignment_score", 0)
            )
        except (TypeError, ValueError, AttributeError):
            alignment_score = 0.0

        if slot_completed:
            derived_events.append(
                {
                    **timeline_event,
                    "event_type": "middle_layer.timeline.slot_completion",
                    "orchestration_reason": "slot_completion_transition",
                }
            )

        if drift_score >= 0.67:
            derived_events.append(
                {
                    **timeline_event,
                    "event_type": "middle_layer.timeline.drift_threshold",
                    "orchestration_reason": "drift_spike_threshold",
                    "drift_threshold": 0.67,
                }
            )

        if alignment_score <= 0.4:
            derived_events.append(
                {
                    **timeline_event,
                    "event_type": "middle_layer.timeline.alignment_shift",
                    "orchestration_reason": "alignment_drop_threshold",
                    "alignment_threshold": 0.4,
                }
            )

        phase_unlock_slots = {4: "Seeds", 8: "Projects", 12: "MVP"}
        unlocked_phase = phase_unlock_slots.get(slot_index)
        if slot_completed and not gate_locked and unlocked_phase:
            gate = next(
                (
                    item
                    for item in phase_gates
                    if isinstance(item, dict) and str(item.get("phase") or "") == unlocked_phase
                ),
                None,
            )
            if gate and not bool(gate.get("locked", True)):
                derived_events.append(
                    {
                        **timeline_event,
                        "event_type": "middle_layer.timeline.gate_unlock",
                        "orchestration_reason": "phase_gate_unlocked",
                        "unlocked_phase": unlocked_phase,
                    }
                )

        return derived_events

    def _resolve_event_priority(timeline_event: dict[str, object]) -> str:
        event_type = str(timeline_event.get("event_type") or "")
        gate_locked = bool(timeline_event.get("gate_locked"))

        try:
            drift_score = float(
                timeline_event.get("drift_score")
                if timeline_event.get("drift_score") is not None
                else timeline_event.get("semantic_state", {}).get("drift_score", 0)
            )
        except (TypeError, ValueError, AttributeError):
            drift_score = 0.0

        try:
            alignment_score = float(
                timeline_event.get("alignment_score")
                if timeline_event.get("alignment_score") is not None
                else timeline_event.get("semantic_state", {}).get("alignment_score", 0)
            )
        except (TypeError, ValueError, AttributeError):
            alignment_score = 1.0

        if event_type in {"middle_layer.timeline.drift_threshold", "middle_layer.timeline.alignment_shift"}:
            if drift_score >= 0.85 or alignment_score <= 0.2:
                return "critical"
            return "warn"

        if event_type in {"middle_layer.timeline.slot_completion", "middle_layer.timeline.gate_unlock"}:
            return "info"

        if gate_locked:
            return "warn"
        if drift_score >= 0.85 or alignment_score <= 0.2:
            return "critical"
        if drift_score >= 0.67 or alignment_score <= 0.4:
            return "warn"
        return "info"

    def _with_priority(timeline_event: dict[str, object]) -> dict[str, object] | None:
        if not isinstance(timeline_event, dict) or not timeline_event.get("event_type"):
            return None

        normalized_event = dict(timeline_event)
        normalized_event["priority"] = _resolve_event_priority(normalized_event)
        return normalized_event

    def _priority_sort_key(timeline_event: dict[str, object]) -> tuple[int, int, int, str]:
        priority = str(timeline_event.get("priority") or "info")
        rank = priority_rank.get(priority, len(priority_rank))

        try:
            slot_index = int(timeline_event.get("slot_index") or 0)
        except (TypeError, ValueError):
            slot_index = 0

        event_type = str(timeline_event.get("event_type") or "")
        event_rank = event_type_rank.get(event_type, len(event_type_rank) + 1)
        return (rank, slot_index, event_rank, event_type)

    def _build_priority_queue(ordered_events: list[dict[str, object]]) -> list[dict[str, object]]:
        queue: list[dict[str, object]] = []
        for index, timeline_event in enumerate(ordered_events):
            queue.append(
                {
                    "queue_index": index,
                    "event_type": str(timeline_event.get("event_type") or ""),
                    "slot_index": int(timeline_event.get("slot_index") or 0),
                    "priority": str(timeline_event.get("priority") or "info"),
                    "orchestration_reason": str(timeline_event.get("orchestration_reason") or ""),
                }
            )
        return queue

    def _build_platform_intelligence_metadata(
        ordered_events: list[dict[str, object]],
        orchestration_priority_queue: list[dict[str, object]],
    ) -> dict[str, object]:
        latest_event = ordered_events[0] if ordered_events else {}

        try:
            latest_drift = float(
                latest_event.get("drift_score")
                if latest_event.get("drift_score") is not None
                else latest_event.get("semantic_state", {}).get("drift_score", 0)
            )
        except (TypeError, ValueError, AttributeError):
            latest_drift = 0.0

        try:
            latest_stability = float(
                latest_event.get("stability_score")
                if latest_event.get("stability_score") is not None
                else latest_event.get("semantic_state", {}).get("stability_score", 0)
            )
        except (TypeError, ValueError, AttributeError):
            latest_stability = 0.0

        try:
            latest_alignment = float(
                latest_event.get("alignment_score")
                if latest_event.get("alignment_score") is not None
                else latest_event.get("semantic_state", {}).get("alignment_score", 0)
            )
        except (TypeError, ValueError, AttributeError):
            latest_alignment = 0.0

        latest_slot_index = 0
        try:
            latest_slot_index = int(latest_event.get("slot_index") or 0)
        except (TypeError, ValueError):
            latest_slot_index = 0

        latest_phase = str(latest_event.get("phase") or "")
        gate_locked = bool(latest_event.get("gate_locked"))

        slot_semantic_scores: dict[int, tuple[float, float]] = {}
        for timeline_event in ordered_events:
            try:
                slot_index = int(timeline_event.get("slot_index") or 0)
            except (TypeError, ValueError):
                continue
            if slot_index <= 0:
                continue
            try:
                drift_score = float(
                    timeline_event.get("drift_score")
                    if timeline_event.get("drift_score") is not None
                    else timeline_event.get("semantic_state", {}).get("drift_score", 0)
                )
            except (TypeError, ValueError, AttributeError):
                drift_score = 0.0
            try:
                alignment_score = float(
                    timeline_event.get("alignment_score")
                    if timeline_event.get("alignment_score") is not None
                    else timeline_event.get("semantic_state", {}).get("alignment_score", 0)
                )
            except (TypeError, ValueError, AttributeError):
                alignment_score = 0.0
            slot_semantic_scores[slot_index] = (_clamp_score(drift_score), _clamp_score(alignment_score))

        sorted_slots = sorted(slot_semantic_scores.keys())
        drift_trend_delta = 0.0
        alignment_trajectory_delta = 0.0
        drift_trend_direction = "stable"
        alignment_trajectory_direction = "stable"
        if len(sorted_slots) >= 2:
            first_drift, first_alignment = slot_semantic_scores[sorted_slots[0]]
            last_drift, last_alignment = slot_semantic_scores[sorted_slots[-1]]
            drift_trend_delta = round(last_drift - first_drift, 3)
            alignment_trajectory_delta = round(last_alignment - first_alignment, 3)
            if drift_trend_delta >= 0.05:
                drift_trend_direction = "rising"
            elif drift_trend_delta <= -0.05:
                drift_trend_direction = "falling"
            if alignment_trajectory_delta >= 0.05:
                alignment_trajectory_direction = "improving"
            elif alignment_trajectory_delta <= -0.05:
                alignment_trajectory_direction = "declining"

        risk_level = "low"
        if latest_drift >= 0.67 or latest_alignment <= 0.4 or gate_locked:
            risk_level = "medium"
        if latest_drift >= 0.85 or latest_alignment <= 0.2:
            risk_level = "high"

        locked_phases = [
            str(item.get("phase") or "")
            for item in phase_gates
            if isinstance(item, dict) and bool(item.get("locked"))
        ]
        unlocked_phases = [
            str(item.get("phase") or "")
            for item in phase_gates
            if isinstance(item, dict) and not bool(item.get("locked"))
        ]

        highest_priority = "info"
        if orchestration_priority_queue:
            highest_priority = str(orchestration_priority_queue[0].get("priority") or "info")

        lfo_envelope = build_lfo_engine_envelope(
            timeline_snapshot={
                "latest_slot_index": latest_slot_index,
                "latest_phase": latest_phase,
                "drift_score": round(_clamp_score(latest_drift), 3),
                "stability_score": round(_clamp_score(latest_stability), 3),
                "alignment_score": round(_clamp_score(latest_alignment), 3),
                "completion_ratio": round(len(completed_slots) / 16.0, 3),
            },
            synthesis_snapshot={
                "risk_level": risk_level,
                "drift_trend": drift_trend_direction,
                "alignment_trajectory": alignment_trajectory_direction,
            },
            trigger_count=len(orchestration_priority_queue),
        )

        return {
            "source": "project_middle_layer.dispatch",
            "orchestration": {
                "priority_order": ["critical", "warn", "info"],
                "trigger_count": len(orchestration_priority_queue),
                "highest_priority": highest_priority,
            },
            "semantic_metadata": {
                "drift_score": round(_clamp_score(latest_drift), 3),
                "stability_score": round(_clamp_score(latest_stability), 3),
                "alignment_score": round(_clamp_score(latest_alignment), 3),
            },
            "phase_gate_state": {
                "locked_phases": locked_phases,
                "unlocked_phases": unlocked_phases,
            },
            "slot_progression": {
                "slot_count": 16,
                "completed_count": len(completed_slots),
                "completion_ratio": round(len(completed_slots) / 16.0, 3),
                "latest_slot_index": latest_slot_index,
                "latest_phase": latest_phase,
            },
            "synthesis": {
                "risk_level": risk_level,
                "drift_trend": {
                    "direction": drift_trend_direction,
                    "delta": drift_trend_delta,
                    "sample_count": len(sorted_slots),
                },
                "alignment_trajectory": {
                    "direction": alignment_trajectory_direction,
                    "delta": alignment_trajectory_delta,
                    "sample_count": len(sorted_slots),
                },
            },
            "lfo_engine": {
                "mode": str(lfo_envelope.get("mode") or "lfo_expansion_v1"),
                "sevm_logical_branch_count": len(lfo_envelope.get("sevm_logical_branches", [])),
                "group_template_count": int(lfo_envelope.get("template_summary", {}).get("group_template_count", 0)),
                "industry_template_count": int(lfo_envelope.get("template_summary", {}).get("industry_template_count", 0)),
                "micro_template_count": int(lfo_envelope.get("micro_template_summary", {}).get("micro_template_count", 0)),
                "feature_pathway_count": len(lfo_envelope.get("feature_probability", [])),
                "surface_modes": {
                    "math": str(lfo_envelope.get("math_surface", {}).get("mode") or ""),
                    "language": str(lfo_envelope.get("language_surface", {}).get("mode") or ""),
                    "arts": str(lfo_envelope.get("arts_surface", {}).get("mode") or ""),
                    "science": str(lfo_envelope.get("science_surface", {}).get("mode") or ""),
                    "micro": str(lfo_envelope.get("micro_surface", {}).get("source") or ""),
                },
                "science_lens_count": len(lfo_envelope.get("science_surface", {}).get("lenses", [])),
                "micro_science_lens_count": len(lfo_envelope.get("micro_templates", [])) * 4,
            },
        }

    def _dispatch_event(
        timeline_event: dict[str, object],
        orchestration_priority_queue: list[dict[str, object]],
        platform_intelligence: dict[str, object],
    ) -> int:
        if not isinstance(timeline_event, dict) or not timeline_event.get("event_type"):
            return 0
        dispatch_semantic_webhook_event(
            event_type=str(timeline_event.get("event_type")),
            payload={
                "mode": payload.get("mode"),
                "timeline_event": timeline_event,
                "completed_slots": completed_slots,
                "phase_gates": phase_gates,
                "priority_order": ["critical", "warn", "info"],
                "orchestration_priority_queue": orchestration_priority_queue,
                "platform_intelligence": platform_intelligence,
            },
        )
        return 1

    dispatch_events: list[dict[str, object]] = []

    selected_slot_state = payload.get("selected_slot_state", {})
    selected_event = selected_slot_state.get("event", {}) if isinstance(selected_slot_state, dict) else {}
    prioritized_selected = _with_priority(selected_event)
    if prioritized_selected is not None:
        dispatch_events.append(prioritized_selected)
        for derived_event in _derive_orchestration_events(prioritized_selected):
            prioritized_derived = _with_priority(derived_event)
            if prioritized_derived is not None:
                dispatch_events.append(prioritized_derived)

    for event in payload.get("events", []):
        prioritized_event = _with_priority(event)
        if prioritized_event is None:
            continue
        dispatch_events.append(prioritized_event)
        for derived_event in _derive_orchestration_events(prioritized_event):
            prioritized_derived = _with_priority(derived_event)
            if prioritized_derived is not None:
                dispatch_events.append(prioritized_derived)

    ordered_dispatch_events = sorted(dispatch_events, key=_priority_sort_key)
    orchestration_priority_queue = _build_priority_queue(ordered_dispatch_events)
    platform_intelligence = _build_platform_intelligence_metadata(
        ordered_dispatch_events,
        orchestration_priority_queue,
    )

    for timeline_event in ordered_dispatch_events:
        dispatch_count += _dispatch_event(
            timeline_event,
            orchestration_priority_queue,
            platform_intelligence,
        )

    return dispatch_count


def get_project_middle_layer_activation_payload() -> dict[str, object]:
    gics_total = PlatformReferenceGICSReferenceSchema.objects.count()
    naics_total = PlatformReferenceNAICSReferenceSchema.objects.count()
    gics_source_status = get_gics_source_status()

    classified_total = MLASClassificationRecord.objects.count()
    classified_with_gics = MLASClassificationRecord.objects.exclude(gics_sub_industry_code="").count()
    classified_with_naics = MLASClassificationRecord.objects.exclude(naics_code_6="").count()

    project_total = ProjectNode.objects.count()
    snapshot_total = ProjectEvolutionSnapshot.objects.count()
    lineage_total = SemanticLineageRecord.objects.count()
    alert_total = SemanticAlert.objects.count()

    reference_ready = gics_total > 0 and naics_total > 0 and gics_source_status != "missing"
    drift_signal_ready = snapshot_total > 0 and lineage_total > 0
    classification_ready = classified_total == 0 or (classified_with_gics > 0 and classified_with_naics > 0)

    capability_flags = {
        "canonical_reference_truth": reference_ready,
        "classification_truth_binding": classification_ready,
        "drift_signal_readiness": drift_signal_ready,
        "compile_export_chain": project_total > 0 or snapshot_total > 0,
        "analytics_alert_surface": alert_total > 0 or snapshot_total > 0,
    }
    rr_color_context = build_middle_layer_rr_color_context()

    recent_snapshots = list(ProjectEvolutionSnapshot.objects.order_by("-created_at", "-id")[:12])
    avg_drift_risk = 0.0
    if recent_snapshots:
        avg_drift_risk = sum(float(item.drift_risk or 0.0) for item in recent_snapshots) / len(recent_snapshots)

    severity_weights = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for row in SemanticAlert.objects.values("severity").annotate(total=models.Count("id")):
        severity = str(row.get("severity", "")).lower()
        if severity in severity_weights:
            severity_weights[severity] = int(row.get("total", 0) or 0)

    compartment_drift_detection = build_middle_layer_compartment_drift_detection(
        assignment_type=ASSIGNMENT_TWELVE_POINT,
        deliverable_name="project middle layer governance",
        drift_risk=avg_drift_risk,
        alert_count=alert_total,
        severity_weights=severity_weights,
    )
    capability_flags["compartment_drift_governance"] = bool(compartment_drift_detection.get("compartments"))

    return {
        "app": "project_middle_layer",
        "boundary": "project-middle-layer",
        "status": "active",
        "reference_truth": {
            "gics_source_status": gics_source_status,
            "gics_total": gics_total,
            "naics_total": naics_total,
        },
        "classification_truth": {
            "total": classified_total,
            "gics_mapped": classified_with_gics,
            "naics_mapped": classified_with_naics,
        },
        "semantic_state": {
            "projects": project_total,
            "snapshots": snapshot_total,
            "lineage_records": lineage_total,
            "alerts": alert_total,
            "drift_baseline": round(avg_drift_risk, 3),
        },
        "rr_color_context": rr_color_context,
        "capability_flags": capability_flags,
        "compartment_drift_detection": compartment_drift_detection,
        "deterministic_ready": all(capability_flags.values()),
    }


def _record_project_evolution_snapshot(*, project: ProjectNode, compiled: dict[str, object]) -> ProjectEvolutionSnapshot:
    identity_payload = compiled.get("identity_payload", {})
    identity = identity_payload.get("identity", {}) if isinstance(identity_payload, dict) else {}
    branch_resolution = identity.get("branch_resolution", {}) if isinstance(identity, dict) else {}
    drift_forecast = compiled.get("drift_forecast", {})
    drift_risk = drift_forecast.get("risk", {}) if isinstance(drift_forecast, dict) else {}
    specialized_path = compiled.get("specialized_path", {})
    semantic_tags = compiled.get("schema", {}).get("semantic_tags", []) if isinstance(compiled.get("schema", {}), dict) else []
    confidence = compiled.get("confidence", {}) if isinstance(compiled.get("confidence", {}), dict) else {}
    lineage_explorer = compiled.get("lineage_explorer", {}) if isinstance(compiled.get("lineage_explorer", {}), dict) else {}
    lineage_tree = lineage_explorer.get("lineage_tree", {}) if isinstance(lineage_explorer, dict) else {}
    semantic_clusters = lineage_explorer.get("semantic_clusters", []) if isinstance(lineage_explorer, dict) else []

    return ProjectEvolutionSnapshot.objects.create(
        project=project,
        identity_payload=identity_payload,
        drift_forecast=drift_forecast,
        branch_resolution=branch_resolution,
        specialized_path=specialized_path,
        semantic_tags=semantic_tags,
        identity_uri=str(identity.get("identity_uri", "")),
        branch_name=str(branch_resolution.get("selected_branch", "")),
        drift_risk=float(drift_risk.get("blended_semantic_drift_risk", 0.0) or 0.0),
        confidence_score=int(confidence.get("confidence_score", 0) or 0),
        confidence_label=str(confidence.get("confidence_label", "Volatile")),
        schema_issue_count=len(compiled.get("schema_validation_errors", []) or []),
        recommendations=compiled.get("recommendations", []),
    )


def _record_semantic_lineage(*, project: ProjectNode, compiled: dict[str, object]) -> SemanticLineageRecord:
    lineage_explorer = compiled.get("lineage_explorer", {}) if isinstance(compiled.get("lineage_explorer", {}), dict) else {}
    lineage_tree = lineage_explorer.get("lineage_tree", {}) if isinstance(lineage_explorer, dict) else {}
    semantic_clusters = lineage_explorer.get("semantic_clusters", []) if isinstance(lineage_explorer, dict) else []

    return SemanticLineageRecord.objects.create(
        project=project,
        lineage_tree=lineage_tree,
        semantic_clusters=semantic_clusters,
        recommendations=compiled.get("recommendations", []),
    )


def _record_semantic_alerts(*, project: ProjectNode, snapshot: ProjectEvolutionSnapshot, compiled: dict[str, object]) -> list[SemanticAlert]:
    prior_snapshots = list(
        ProjectEvolutionSnapshot.objects.filter(project=project)
        .exclude(id=snapshot.id)
        .order_by("-created_at", "-id")[:5]
    )
    recent_schema_issue_count = sum(1 for item in prior_snapshots if (item.schema_issue_count or 0) > 0) + (1 if snapshot.schema_issue_count > 0 else 0)
    prior_drift_values = [float(item.drift_risk or 0.0) for item in prior_snapshots[:3]]

    alerts_payload = build_semantic_alerts(
        compiled.get("schema", {}),
        drift_forecast=compiled.get("drift_forecast", {}),
        confidence=compiled.get("confidence", {}),
        stability_analysis=compiled.get("stability_analysis", {}),
        schema_validation_errors=compiled.get("schema_validation_errors", []),
        recent_schema_issue_count=recent_schema_issue_count,
        prior_drift_values=prior_drift_values,
    )

    alerts: list[SemanticAlert] = []
    for alert_payload in alerts_payload:
        alerts.append(
            SemanticAlert.objects.create(
                project=project,
                source_snapshot=snapshot,
                alert_type=alert_payload["alert_type"],
                severity=alert_payload["severity"],
                message=alert_payload["message"],
                metadata=alert_payload.get("metadata", {}),
            )
        )
    return alerts


def compile_and_store_project_node(payload: dict[str, object]) -> tuple[dict[str, object], ProjectNode]:
    compiled = build_project_creation_payload(
        slug=payload["slug"],
        name=payload["name"],
        semantic_intent=payload["semantic_intent"],
        mlas_tier=payload["mlas_tier"],
        btif_classification=payload["btif_classification"],
        semantic_tags=payload["semantic_tags"],
    )

    metadata = {
        **payload.get("metadata", {}),
        "semantic_tags": payload["semantic_tags"],
        "visibility_tier": payload.get("visibility_tier"),
        "drift_forecast": compiled["drift_forecast"],
        "confidence": compiled.get("confidence", {}),
        "lineage_explorer": compiled.get("lineage_explorer", {}),
        "drift_heatmap_data": compiled.get("drift_heatmap_data", {}),
        "stability_analysis": compiled.get("stability_analysis", {}),
        "recommendations": compiled.get("recommendations", []),
        "identity_payload": compiled["identity_payload"],
        "specialized_path": compiled["specialized_path"],
        "semantic_tree": compiled["semantic_tree"],
    }

    node, _ = ProjectNode.objects.update_or_create(
        slug=payload["slug"],
        defaults={
            "name": payload["name"],
            "semantic_intent": payload["semantic_intent"],
            "mlas_tier": payload["mlas_tier"],
            "btif_classification": payload["btif_classification"],
            "metadata": metadata,
        },
    )
    snapshot = _record_project_evolution_snapshot(project=node, compiled=compiled)
    _record_semantic_lineage(project=node, compiled=compiled)
    alerts = _record_semantic_alerts(project=node, snapshot=snapshot, compiled=compiled)

    compiled["semantic_alerts"] = [
        {
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "metadata": alert.metadata,
        }
        for alert in alerts
    ]

    dispatch_semantic_webhook_event(
        event_type="compile.completed",
        payload={
            "project": {
                "id": node.id,
                "slug": node.slug,
                "name": node.name,
            },
            "snapshot": {
                "id": snapshot.id,
                "identity_uri": snapshot.identity_uri,
                "branch_name": snapshot.branch_name,
                "drift_risk": snapshot.drift_risk,
                "confidence_score": snapshot.confidence_score,
            },
            "alert_count": len(alerts),
        },
    )

    for alert in alerts:
        dispatch_semantic_webhook_event(
            event_type="alert.created",
            payload={
                "project": {
                    "id": node.id,
                    "slug": node.slug,
                },
                "alert": {
                    "id": alert.id,
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                },
            },
        )

    return compiled, node
