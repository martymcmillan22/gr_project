from __future__ import annotations

from polish.task_manager.constants import (
    ASSIGNMENT_DOUBLE_LINEAR,
    ASSIGNMENT_LINEAR,
    ASSIGNMENT_PERPETUAL,
    ASSIGNMENT_TWELVE_POINT,
    get_task_archetype_definition,
)

PHASE_IDEA = "idea"
PHASE_SEED = "seed"
PHASE_PROJECT = "project"

PHASE_TASK_MANAGER_POLICIES = {
    PHASE_IDEA: {
        "va": {
            "enabled": False,
            "mode": "disabled",
            "narration": "none",
            "drift_detection": "none",
            "deliverable_coaching": False,
            "compartment_narration": False,
            "editorial_tone_guidance": False,
        },
        "polish": {
            "enabled": False,
            "mode": "disabled",
            "identity_refinement": False,
            "deliverable_refinement": False,
            "compartment_refinement": False,
        },
        "task_manager": {
            "enabled": False,
            "allow_assignments": False,
            "allow_compartment_routing": False,
            "allow_deliverable_binding": False,
        },
    },
    PHASE_SEED: {
        "va": {
            "enabled": True,
            "mode": "read_only",
            "narration": "identity_only",
            "drift_detection": "none",
            "deliverable_coaching": False,
            "compartment_narration": False,
            "editorial_tone_guidance": False,
        },
        "polish": {
            "enabled": True,
            "mode": "identity_refinement",
            "identity_refinement": True,
            "deliverable_refinement": False,
            "compartment_refinement": False,
        },
        "task_manager": {
            "enabled": False,
            "allow_assignments": False,
            "allow_compartment_routing": False,
            "allow_deliverable_binding": False,
        },
    },
    PHASE_PROJECT: {
        "va": {
            "enabled": True,
            "mode": "full",
            "narration": "compartment_and_deliverable",
            "drift_detection": "full",
            "deliverable_coaching": True,
            "compartment_narration": True,
            "editorial_tone_guidance": True,
        },
        "polish": {
            "enabled": True,
            "mode": "full_refinement",
            "identity_refinement": True,
            "deliverable_refinement": True,
            "compartment_refinement": True,
        },
        "task_manager": {
            "enabled": True,
            "allow_assignments": True,
            "allow_compartment_routing": True,
            "allow_deliverable_binding": True,
        },
    },
}

PROGRESSION_MODELS = {
    ASSIGNMENT_LINEAR: "sequential",
    ASSIGNMENT_DOUBLE_LINEAR: "parallel",
    ASSIGNMENT_TWELVE_POINT: "structured",
    ASSIGNMENT_PERPETUAL: "rolling",
}

DELIVERABLE_ASSIGNMENT_RULES = (
    (("issue", "sidebar"), ASSIGNMENT_DOUBLE_LINEAR),
    (("monthly", "issue"), ASSIGNMENT_LINEAR),
    (("annual", "summary"), ASSIGNMENT_TWELVE_POINT),
    (("annual", "plan"), ASSIGNMENT_PERPETUAL),
    (("editorial", "calendar"), ASSIGNMENT_PERPETUAL),
    (("theme", "tracker"), ASSIGNMENT_PERPETUAL),
)


def normalize_operating_phase(phase: str | None) -> str:
    value = str(phase or "").strip().lower()
    if value in PHASE_TASK_MANAGER_POLICIES:
        return value
    return PHASE_PROJECT


def get_phase_policy(phase: str | None) -> dict[str, object]:
    normalized = normalize_operating_phase(phase)
    return {
        "phase": normalized,
        **PHASE_TASK_MANAGER_POLICIES[normalized],
    }


def task_manager_enabled_for_phase(phase: str | None) -> bool:
    policy = get_phase_policy(phase)
    task_manager_policy = policy.get("task_manager", {})
    return bool(task_manager_policy.get("enabled", False))


def resolve_assignment_type_for_deliverable(deliverable_name: str) -> str:
    text = str(deliverable_name or "").strip().lower()
    if not text:
        return ASSIGNMENT_LINEAR

    for terms, assignment_type in DELIVERABLE_ASSIGNMENT_RULES:
        if all(term in text for term in terms):
            return assignment_type
    return ASSIGNMENT_LINEAR


def bind_deliverable_to_compartments(*, assignment_type: str, deliverable_name: str) -> dict[str, object]:
    archetype = get_task_archetype_definition(assignment_type)
    canonical_compartments = archetype.get("canonical_compartments", {})

    bindings: list[dict[str, str]] = []
    for track, slots in canonical_compartments.items():
        for slot in slots:
            bindings.append(
                {
                    "track": track,
                    "slot": str(slot.get("slot", "")),
                    "compartment": str(slot.get("compartment", "")),
                    "label": str(slot.get("label", "")),
                }
            )

    return {
        "deliverable": str(deliverable_name or "").strip(),
        "assignment_type": assignment_type,
        "archetype_label": archetype.get("label", assignment_type),
        "progression_model": PROGRESSION_MODELS.get(assignment_type, "sequential"),
        "binding_count": len(bindings),
        "compartment_bindings": bindings,
    }


def _tone_for_compartment(code: str) -> str:
    if code in {"R", "P"}:
        return "exploratory"
    if code in {"B", "T", "I", "N"}:
        return "constructive"
    if code in {"Y", "O", "V", "S"}:
        return "precision"
    return "delivery"


def _next_step_for_compartment(code: str) -> str:
    if code in {"R", "P"}:
        return "Confirm intent and constraints before expanding scope."
    if code in {"B", "T", "I", "N"}:
        return "Advance structure and lock deterministic sequence boundaries."
    if code in {"Y", "O", "V", "S"}:
        return "Refine narrative clarity and remove semantic ambiguities."
    return "Finalize output and verify governance alignment signatures."


def _status_from_score(score: float) -> str:
    if score >= 0.7:
        return "at_risk"
    if score >= 0.35:
        return "watch"
    return "stable"


def _alignment_from_score(score: float) -> str:
    if score >= 0.7:
        return "recalibrate"
    if score >= 0.35:
        return "monitor"
    return "aligned"


def build_middle_layer_compartment_drift_detection(
    *,
    assignment_type: str,
    deliverable_name: str,
    drift_risk: float = 0.0,
    alert_count: int = 0,
    severity_weights: dict[str, int] | None = None,
) -> dict[str, object]:
    routing = bind_deliverable_to_compartments(
        assignment_type=assignment_type,
        deliverable_name=deliverable_name,
    )
    bindings = routing.get("compartment_bindings", [])
    binding_count = max(int(routing.get("binding_count", 0)), 1)

    safe_risk = max(0.0, min(float(drift_risk or 0.0), 1.0))
    severity_weights = severity_weights or {}
    weighted_alerts = (
        int(severity_weights.get("low", 0))
        + int(severity_weights.get("medium", 0)) * 2
        + int(severity_weights.get("high", 0)) * 3
        + int(severity_weights.get("critical", 0)) * 4
    )
    if weighted_alerts == 0:
        weighted_alerts = int(alert_count or 0)
    alert_delta = min(weighted_alerts * 0.02, 0.2)

    rows: list[dict[str, object]] = []
    for index, binding in enumerate(bindings):
        position_bias = (index / binding_count) * 0.1
        base_score = max(0.0, min(safe_risk + alert_delta + position_bias, 1.0))

        semantic_score = base_score
        narrative_score = max(0.0, min(base_score * 0.92, 1.0))
        identity_score = max(0.0, min(base_score * 0.88, 1.0))
        deliverable_score = max(0.0, min(base_score * 0.95, 1.0))

        blended_score = round(
            (semantic_score + narrative_score + identity_score + deliverable_score) / 4,
            3,
        )
        rows.append(
            {
                "track": binding.get("track", ""),
                "slot": binding.get("slot", ""),
                "compartment": binding.get("compartment", ""),
                "drift": {
                    "semantic": round(semantic_score, 3),
                    "narrative": round(narrative_score, 3),
                    "identity": round(identity_score, 3),
                    "deliverable": round(deliverable_score, 3),
                    "blended": blended_score,
                },
                "status": _status_from_score(blended_score),
                "alignment": _alignment_from_score(blended_score),
            }
        )

    return {
        "assignment_type": assignment_type,
        "deliverable": str(deliverable_name or "").strip(),
        "alert_count": int(alert_count or 0),
        "severity_weights": severity_weights,
        "compartments": rows,
    }


def build_va_compartment_narration(
    *,
    assignment_type: str,
    deliverable_name: str,
    drift_detection: dict[str, object] | None = None,
) -> dict[str, object]:
    routing = bind_deliverable_to_compartments(
        assignment_type=assignment_type,
        deliverable_name=deliverable_name,
    )
    if drift_detection is None:
        drift_detection = build_middle_layer_compartment_drift_detection(
            assignment_type=assignment_type,
            deliverable_name=deliverable_name,
            drift_risk=0.0,
            alert_count=0,
        )
    drift_rows = drift_detection.get("compartments", []) if isinstance(drift_detection, dict) else []
    drift_lookup = {
        (str(row.get("track", "")), str(row.get("slot", ""))): row
        for row in drift_rows
        if isinstance(row, dict)
    }

    narration_rows: list[dict[str, object]] = []
    for binding in routing.get("compartment_bindings", []):
        track = str(binding.get("track", ""))
        slot = str(binding.get("slot", ""))
        compartment = str(binding.get("compartment", ""))
        drift_row = drift_lookup.get((track, slot), {})
        drift = drift_row.get("drift", {}) if isinstance(drift_row, dict) else {}
        blended = float(drift.get("blended", 0.0) or 0.0)
        status = str(drift_row.get("status", _status_from_score(blended)))
        alignment = str(drift_row.get("alignment", _alignment_from_score(blended)))

        narration_rows.append(
            {
                "track": track,
                "slot": slot,
                "compartment": compartment,
                "status": status,
                "drift": {
                    "semantic": float(drift.get("semantic", 0.0) or 0.0),
                    "narrative": float(drift.get("narrative", 0.0) or 0.0),
                    "identity": float(drift.get("identity", 0.0) or 0.0),
                    "deliverable": float(drift.get("deliverable", 0.0) or 0.0),
                    "blended": blended,
                },
                "tone": _tone_for_compartment(compartment),
                "alignment": alignment,
                "next_step": _next_step_for_compartment(compartment),
                "narration": (
                    f"Compartment {compartment} is {status}. "
                    f"Use {_tone_for_compartment(compartment)} tone and focus on {_next_step_for_compartment(compartment).lower()}"
                ),
            }
        )

    return {
        "assignment_type": assignment_type,
        "deliverable": str(deliverable_name or "").strip(),
        "compartments": narration_rows,
    }


def build_polish_compartment_refinement(
    *,
    assignment_type: str,
    deliverable_name: str,
) -> dict[str, object]:
    routing = bind_deliverable_to_compartments(
        assignment_type=assignment_type,
        deliverable_name=deliverable_name,
    )

    rows: list[dict[str, object]] = []
    for binding in routing.get("compartment_bindings", []):
        compartment = str(binding.get("compartment", ""))
        tone = _tone_for_compartment(compartment)
        rows.append(
            {
                "track": str(binding.get("track", "")),
                "slot": str(binding.get("slot", "")),
                "compartment": compartment,
                "refinement": {
                    "narrative": "tighten storyline coherence and signal-to-noise",
                    "structure": "enforce deterministic section ordering",
                    "tone": tone,
                    "clarity": "remove ambiguity and collapse duplicate intents",
                    "alignment": "verify quadrant and archetype contract alignment",
                },
            }
        )

    return {
        "assignment_type": assignment_type,
        "deliverable": str(deliverable_name or "").strip(),
        "compartments": rows,
    }
