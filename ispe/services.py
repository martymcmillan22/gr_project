from platform_core.activation import build_phase4_activation_payload
from platform_core.activation import build_phase4_orchestration_payload
from polish.task_manager.constants import ASSIGNMENT_LINEAR
from polish.task_manager.routing import (
    build_middle_layer_compartment_drift_detection,
    build_polish_compartment_refinement,
    build_va_compartment_narration,
    get_phase_policy,
)

ISPE_PHASES = ("idea", "seed", "project")
ISPE_LOCAL_CONFIG_READY = True


def _normalize_mode(raw: str | None) -> str:
    value = str(raw or "").strip().lower()
    if value in {"strict", "assistive", "default"}:
        return value
    return "assistive"


def _normalize_phase(raw: str | None) -> str:
    value = str(raw or "").strip().lower()
    if value in ISPE_PHASES:
        return value
    return "idea"


def _setup_steps_from_payload(orchestration_payload: dict[str, object]) -> list[str]:
    steps: list[str] = []
    blocking_capabilities = orchestration_payload.get("blocking_capabilities", [])
    soft_blocking_capabilities = orchestration_payload.get("soft_blocking_capabilities", [])
    missing_dependencies = orchestration_payload.get("missing_dependencies", [])

    if isinstance(blocking_capabilities, list):
        for blocker in blocking_capabilities:
            if not isinstance(blocker, dict):
                continue
            capability = str(blocker.get("capability", "unknown_capability"))
            reason = str(blocker.get("reason", "missing_dependency"))
            steps.append(f"Resolve {capability}: {reason}")

    if isinstance(soft_blocking_capabilities, list):
        for blocker in soft_blocking_capabilities:
            if not isinstance(blocker, dict):
                continue
            capability = str(blocker.get("capability", "unknown_capability"))
            reason = str(blocker.get("reason", "optional_dependency"))
            steps.append(f"Optional follow-up: {capability} - {reason}")

    if isinstance(missing_dependencies, list):
        for dependency in missing_dependencies:
            steps.append(f"Add missing dependency: {dependency}")

    return steps


def _idea_guidance(orchestration_payload: dict[str, object], *, go: bool) -> dict[str, object]:
    if go:
        return {
            "phase": "idea",
            "state": "ready",
            "headline": "Create a new Idea",
            "subheadline": "The platform is ready for a fresh Idea submission.",
            "cta_label": "Create Idea",
            "next_suggested_fields": [
                "idea_title",
                "audience",
                "annual_plan",
                "industry_mapping",
                "btif_base",
                "objective",
            ],
            "primary_unlocks": [
                "idea_creation",
                "suggested_fields",
                "assistant_guidance",
            ],
        }

    return {
        "phase": "idea",
        "state": "blocked",
        "headline": "Prepare the Idea workspace",
        "subheadline": "Resolve setup blockers before creating the next Idea.",
        "cta_label": "Fix setup blockers",
        "setup_steps": _setup_steps_from_payload(orchestration_payload),
        "next_suggested_fields": [
            "idea_title",
            "audience",
            "objective",
        ],
        "primary_unlocks": [
            "idea_creation",
            "assistant_guidance",
        ],
    }


def _seed_guidance(orchestration_payload: dict[str, object], *, go: bool) -> dict[str, object]:
    if go:
        return {
            "phase": "seed",
            "state": "ready",
            "headline": "Promote the Idea to Seed",
            "subheadline": "The platform can now shape the Idea into a structured Seed.",
            "cta_label": "Promote to Seed",
            "next_suggested_fields": [
                "seed_name",
                "structure",
                "btif_identity",
                "distribution_channels",
                "release_cadence",
            ],
            "primary_unlocks": [
                "seed_promotion",
                "btif_identity_hints",
                "structure_guidance",
            ],
        }

    return {
        "phase": "seed",
        "state": "blocked",
        "headline": "Seed promotion needs a few more inputs",
        "subheadline": "Complete the blocking requirements before promoting this Idea.",
        "cta_label": "Review required inputs",
        "setup_steps": _setup_steps_from_payload(orchestration_payload),
        "next_suggested_fields": [
            "seed_name",
            "structure",
            "btif_identity",
        ],
        "primary_unlocks": [
            "seed_promotion",
            "assistant_guidance",
        ],
    }


def _project_guidance(orchestration_payload: dict[str, object], *, go: bool, include_va: bool) -> dict[str, object]:
    if go:
        return {
            "phase": "project",
            "state": "ready",
            "headline": "Unlock Project operations",
            "subheadline": "PIP, Polish, Task Manager, and VA can be opened from this state.",
            "cta_label": "Open Project tools",
            "next_suggested_fields": [
                "project_name",
                "delivery_scope",
                "pip_access",
                "polish_scope",
                "task_manager_scope",
                "va_orchestration",
            ],
            "primary_unlocks": [
                "pip",
                "polish",
                "task_manager",
                "va" if include_va else "va_ready",
            ],
        }

    return {
        "phase": "project",
        "state": "blocked",
        "headline": "Project workspace is not ready yet",
        "subheadline": "Resolve the critical platform blockers before unlocking project tools.",
        "cta_label": "Review project blockers",
        "setup_steps": _setup_steps_from_payload(orchestration_payload),
        "next_suggested_fields": [
            "project_name",
            "delivery_scope",
            "pip_access",
        ],
        "primary_unlocks": [
            "pip",
            "polish",
            "task_manager",
            "va" if include_va else "va_ready",
        ],
    }


def build_ispe_activation_payload(*, mode: str = "assistive", include_va: bool = True, phase: str = "idea") -> dict[str, object]:
    normalized_mode = _normalize_mode(mode)
    normalized_phase = _normalize_phase(phase)

    activation_payload = build_phase4_activation_payload(include_va=include_va, mode=normalized_mode)
    orchestration_payload = build_phase4_orchestration_payload(include_va=include_va, mode=normalized_mode)

    semantic_ready = bool(activation_payload.get("semantic_readiness", {}).get("deterministic_ready", False)) if isinstance(activation_payload.get("semantic_readiness", {}), dict) else False
    quadrant_ready = bool(activation_payload.get("quadrant_readiness", {}).get("deterministic_ready", False)) if isinstance(activation_payload.get("quadrant_readiness", {}), dict) else False
    middle_layer_ready = bool(activation_payload.get("project_middle_layer_readiness", {}).get("deterministic_ready", False)) if isinstance(activation_payload.get("project_middle_layer_readiness", {}), dict) else False
    orchestration_go = bool(orchestration_payload.get("decision", {}).get("go", False)) if isinstance(orchestration_payload.get("decision", {}), dict) else False

    if normalized_phase == "idea":
        phase_guidance = _idea_guidance(orchestration_payload, go=orchestration_go)
    elif normalized_phase == "seed":
        phase_guidance = _seed_guidance(orchestration_payload, go=orchestration_go)
    else:
        phase_guidance = _project_guidance(orchestration_payload, go=orchestration_go, include_va=include_va)

    phase_policy = get_phase_policy(normalized_phase)
    drift_baseline = 0.0
    if isinstance(activation_payload.get("project_middle_layer_readiness"), dict):
        drift_baseline = float(
            activation_payload.get("project_middle_layer_readiness", {}).get("drift_baseline", 0.0) or 0.0
        )

    compartment_drift = build_middle_layer_compartment_drift_detection(
        assignment_type=ASSIGNMENT_LINEAR,
        deliverable_name=f"{normalized_phase} governance",
        drift_risk=drift_baseline,
        alert_count=0,
    )
    va_narration = build_va_compartment_narration(
        assignment_type=ASSIGNMENT_LINEAR,
        deliverable_name=f"{normalized_phase} governance",
        drift_detection=compartment_drift,
    )
    polish_refinement = build_polish_compartment_refinement(
        assignment_type=ASSIGNMENT_LINEAR,
        deliverable_name=f"{normalized_phase} governance",
    )

    ispe_ready = ISPE_LOCAL_CONFIG_READY and semantic_ready and quadrant_ready and middle_layer_ready and orchestration_go

    return {
        "app": "ispe",
        "boundary": "ispe-activation",
        "contract": "ispe-orchestration-heartbeat",
        "contract_version": "1.0.0",
        "status": "active",
        "phase": normalized_phase,
        "mode": normalized_mode,
        "activation_contract": activation_payload,
        "orchestration_contract": orchestration_payload,
        "semantic_ready": semantic_ready,
        "quadrant_ready": quadrant_ready,
        "middle_layer_ready": middle_layer_ready,
        "ispe_config_ready": ISPE_LOCAL_CONFIG_READY,
        "phase_guidance": phase_guidance,
        "phase_policy": phase_policy,
        "va_compartment_narration": va_narration,
        "polish_compartment_refinement": polish_refinement,
        "middle_layer_compartment_drift": compartment_drift,
        "ispe_ready": ispe_ready,
    }
