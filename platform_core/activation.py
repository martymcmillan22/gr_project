from django.http import JsonResponse
from django.utils import timezone

from platform_quadrant.services.activation import get_quadrant_activation_payload
from platform_semantic.services.activation import get_semantic_activation_payload
from project_middle_layer.services import get_project_middle_layer_activation_payload


def _as_bool(raw: str | None) -> bool:
    value = str(raw or "").strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def _normalize_mode(raw: str | None) -> str:
    mode = str(raw or "").strip().lower()
    if mode in {"strict", "assistive"}:
        return mode
    return "default"


def _build_va_readiness(
    *,
    semantic_ready: bool,
    quadrant_ready: bool,
    middle_layer_ready: bool,
    middle_layer_payload: dict[str, object],
) -> dict[str, object]:
    capability_flags = middle_layer_payload.get("capability_flags", {})
    if not isinstance(capability_flags, dict):
        capability_flags = {}

    orchestration_available = semantic_ready and quadrant_ready and middle_layer_ready
    semantic_bridge_ready = semantic_ready and bool(capability_flags.get("canonical_reference_truth", False))
    narrative_engine_ready = bool(capability_flags.get("analytics_alert_surface", False))
    personality_load_state = "ready" if orchestration_available else "pending"

    return {
        "personality_load_state": personality_load_state,
        "orchestration_available": orchestration_available,
        "semantic_bridge_ready": semantic_bridge_ready,
        "narrative_engine_ready": narrative_engine_ready,
        "deterministic_ready": orchestration_available and semantic_bridge_ready and narrative_engine_ready,
    }


def build_phase4_activation_payload(*, include_va: bool = False, mode: str = "default") -> dict[str, object]:
    policy_mode = _normalize_mode(mode)
    semantic_payload = get_semantic_activation_payload()
    quadrant_payload = get_quadrant_activation_payload()
    middle_layer_payload = get_project_middle_layer_activation_payload()

    semantic_ready = bool(semantic_payload.get("deterministic_ready", False))
    quadrant_ready = bool(quadrant_payload.get("deterministic_ready", False))
    middle_layer_ready = bool(middle_layer_payload.get("deterministic_ready", False))

    quadrant_capabilities = quadrant_payload.get("capability_flags", {})
    if not isinstance(quadrant_capabilities, dict):
        quadrant_capabilities = {}

    middle_layer_capabilities = middle_layer_payload.get("capability_flags", {})
    if not isinstance(middle_layer_capabilities, dict):
        middle_layer_capabilities = {}

    matrix = quadrant_payload.get("resolver_catalog", {}).get("matrix", []) if isinstance(quadrant_payload.get("resolver_catalog", {}), dict) else []

    payload: dict[str, object] = {
        "app": "platform_activation",
        "boundary": "phase4-orchestration",
        "contract": "semantic-spine-heartbeat",
        "contract_version": "1.0.0",
        "status": "active",
        "generated_at": timezone.now().isoformat(),
        "request_context": {
            "mode": policy_mode,
            "include_va": include_va,
            "policy_applied": False,
            "policy_note": "Activation endpoint remains descriptive; mode is echo-only for orchestration correlation.",
        },
        "semantic_readiness": {
            "semantic_assets": semantic_payload.get("semantic_assets", {}),
            "reference_truth": semantic_payload.get("reference_truth", {}),
            "classification_truth": semantic_payload.get("classification_truth", {}),
            "semantic_catalogs": semantic_payload.get("semantic_catalogs", {}),
            "deterministic_ready": semantic_ready,
        },
        "quadrant_readiness": {
            "routing_table_counts": {
                "am_domains": len(quadrant_payload.get("resolver_catalog", {}).get("am_domains", {})) if isinstance(quadrant_payload.get("resolver_catalog", {}), dict) else 0,
                "pm_domains": len(quadrant_payload.get("resolver_catalog", {}).get("pm_domains", {})) if isinstance(quadrant_payload.get("resolver_catalog", {}), dict) else 0,
                "resolver_matrix": len(matrix) if isinstance(matrix, list) else 0,
            },
            "reference_truth": quadrant_payload.get("reference_truth", {}),
            "semantic_truth": quadrant_payload.get("semantic_truth", {}),
            "classification_truth": quadrant_payload.get("classification_truth", {}),
            "overlay_readiness": bool(quadrant_capabilities.get("semantic_bundle_routing", False)),
            "heatmap_readiness": bool(quadrant_capabilities.get("deterministic_quadrant_routing", False)),
            "canonical_truth_binding": bool(quadrant_capabilities.get("reference_truth_binding", False)),
            "semantic_dependency_binding": bool(quadrant_capabilities.get("semantic_bundle_routing", False)),
            "deterministic_ready": quadrant_ready,
        },
        "project_middle_layer_readiness": {
            "reference_truth": middle_layer_payload.get("reference_truth", {}),
            "classification_truth": middle_layer_payload.get("classification_truth", {}),
            "semantic_state": middle_layer_payload.get("semantic_state", {}),
            "drift_detection_readiness": bool(middle_layer_capabilities.get("drift_signal_readiness", False)),
            "compilation_readiness": bool(middle_layer_capabilities.get("compile_export_chain", False)),
            "deterministic_ready": middle_layer_ready,
        },
        "phase_flags": {
            "platform_semantic": semantic_ready,
            "platform_quadrant": quadrant_ready,
            "project_middle_layer": middle_layer_ready,
        },
    }

    overall_ready = semantic_ready and quadrant_ready and middle_layer_ready

    if include_va:
        va_readiness = _build_va_readiness(
            semantic_ready=semantic_ready,
            quadrant_ready=quadrant_ready,
            middle_layer_ready=middle_layer_ready,
            middle_layer_payload=middle_layer_payload,
        )
        payload["va_readiness"] = va_readiness
        overall_ready = overall_ready and bool(va_readiness.get("deterministic_ready", False))

    payload["deterministic_ready"] = overall_ready
    return payload


def _make_gate(
    *,
    gate_id: str,
    label: str,
    owner: str,
    severity: str,
    is_met: bool,
    dependency_hint: str,
) -> dict[str, object]:
    return {
        "id": gate_id,
        "label": label,
        "owner": owner,
        "severity": severity,
        "met": is_met,
        "status": "ready" if is_met else "blocked",
        "dependency_hint": dependency_hint,
    }


def _gate_to_blocker(gate: dict[str, object]) -> dict[str, str]:
    return {
        "capability": str(gate.get("id", "unknown_capability")),
        "owner": str(gate.get("owner", "unknown_owner")),
        "severity": str(gate.get("severity", "critical")),
        "reason": str(gate.get("dependency_hint", "missing_dependency")),
    }


def _build_missing_dependencies(activation_payload: dict[str, object]) -> list[str]:
    missing: list[str] = []

    semantic = activation_payload.get("semantic_readiness", {})
    if not isinstance(semantic, dict):
        semantic = {}
    semantic_ref = semantic.get("reference_truth", {})
    if not isinstance(semantic_ref, dict):
        semantic_ref = {}

    if int(semantic_ref.get("gics_total", 0) or 0) <= 0:
        missing.append("gics_reference_rows")
    if int(semantic_ref.get("naics_total", 0) or 0) <= 0:
        missing.append("naics_reference_rows")

    quadrant = activation_payload.get("quadrant_readiness", {})
    if not isinstance(quadrant, dict):
        quadrant = {}
    routing_counts = quadrant.get("routing_table_counts", {})
    if not isinstance(routing_counts, dict):
        routing_counts = {}
    if int(routing_counts.get("resolver_matrix", 0) or 0) <= 0:
        missing.append("quadrant_resolver_matrix")

    middle_layer = activation_payload.get("project_middle_layer_readiness", {})
    if not isinstance(middle_layer, dict):
        middle_layer = {}
    semantic_state = middle_layer.get("semantic_state", {})
    if not isinstance(semantic_state, dict):
        semantic_state = {}
    if int(semantic_state.get("projects", 0) or 0) <= 0:
        missing.append("project_middle_layer_projects")
    if int(semantic_state.get("snapshots", 0) or 0) <= 0:
        missing.append("project_middle_layer_snapshots")

    return missing


def _build_recommended_actions(blockers: list[dict[str, str]]) -> list[str]:
    if not blockers:
        return [
            "Proceed with full VA + UI orchestration rollout",
            "Lock semantic-spine heartbeat at contract_version 1.0.0",
            "Start phase-4 continuous readiness monitoring",
        ]

    actions: list[str] = []
    for blocker in blockers:
        capability = blocker.get("capability", "unknown_capability")
        reason = blocker.get("reason", "missing_dependency")
        actions.append(f"Resolve {capability}: {reason}")

    actions.append("Re-run /platform/activation/ and /platform/orchestration/ after fixes")
    return actions


def _build_assistive_actions(
    *,
    hard_blockers: list[dict[str, str]],
    soft_blockers: list[dict[str, str]],
    missing_dependencies: list[str],
    go: bool,
) -> list[str]:
    if go:
        actions = [
            "Proceed through UI guided activation sequence",
            "Enable VA narration to coach remaining optional setup",
        ]
        if soft_blockers:
            actions.append("Resolve soft blockers after launch stabilization window")
        return actions

    actions: list[str] = []
    for blocker in hard_blockers:
        capability = blocker.get("capability", "unknown_capability")
        actions.append(f"Unblock critical gate: {capability}")

    if missing_dependencies:
        actions.append("Restore missing dependencies required by blocked critical gates")

    actions.append("Re-run orchestration in assistive mode after remediation")
    return actions


def build_phase4_orchestration_payload(*, include_va: bool = False, mode: str = "default") -> dict[str, object]:
    policy_mode = _normalize_mode(mode)
    activation_payload = build_phase4_activation_payload(include_va=include_va, mode=policy_mode)

    phase_flags = activation_payload.get("phase_flags", {})
    if not isinstance(phase_flags, dict):
        phase_flags = {}

    semantic_ready = bool(phase_flags.get("platform_semantic", False))
    quadrant_ready = bool(phase_flags.get("platform_quadrant", False))
    middle_layer_ready = bool(phase_flags.get("project_middle_layer", False))

    readiness_gates: list[dict[str, object]] = []

    readiness_gates.append(
        _make_gate(
            gate_id="platform_semantic_ready",
            label="Platform Semantic Readiness",
            owner="platform_semantic",
            severity="critical",
            is_met=semantic_ready,
            dependency_hint="semantic assets, catalogs, and reference truth must be deterministic",
        )
    )
    readiness_gates.append(
        _make_gate(
            gate_id="platform_quadrant_ready",
            label="Platform Quadrant Readiness",
            owner="platform_quadrant",
            severity="critical",
            is_met=quadrant_ready,
            dependency_hint="quadrant resolver, bindings, and routing readiness must be deterministic",
        )
    )
    readiness_gates.append(
        _make_gate(
            gate_id="project_middle_layer_ready",
            label="Project Middle Layer Readiness",
            owner="project_middle_layer",
            severity="critical",
            is_met=middle_layer_ready,
            dependency_hint="drift detection and compile/export chain readiness are required",
        )
    )

    va_readiness = activation_payload.get("va_readiness", {}) if include_va else {}
    if include_va:
        if not isinstance(va_readiness, dict):
            va_readiness = {}
        va_ready = bool(va_readiness.get("deterministic_ready", False))
        readiness_gates.append(
            _make_gate(
                gate_id="va_orchestration_ready",
                label="VA Orchestration Readiness",
                owner="va",
                severity="soft",
                is_met=va_ready,
                dependency_hint="VA personality load, bridge, and narrative engine must be ready",
            )
        )

    if policy_mode == "assistive":
        semantic_catalogs = activation_payload.get("semantic_readiness", {}).get("semantic_catalogs", {}) if isinstance(activation_payload.get("semantic_readiness", {}), dict) else {}
        if not isinstance(semantic_catalogs, dict):
            semantic_catalogs = {}
        phase_catalog = semantic_catalogs.get("phase", {})
        phase_count = len(phase_catalog) if isinstance(phase_catalog, dict) else 0
        ui_guidance_ready = phase_count >= 2
        readiness_gates.append(
            _make_gate(
                gate_id="ui_guidance_depth_ready",
                label="UI Guidance Depth Readiness",
                owner="ui",
                severity="soft",
                is_met=ui_guidance_ready,
                dependency_hint="assistive mode expects at least two semantic phases for richer user guidance",
            )
        )

    hard_blockers = [_gate_to_blocker(gate) for gate in readiness_gates if not bool(gate.get("met", False)) and gate.get("severity") == "critical"]
    soft_blockers = [_gate_to_blocker(gate) for gate in readiness_gates if not bool(gate.get("met", False)) and gate.get("severity") == "soft"]
    blockers = hard_blockers + soft_blockers

    if policy_mode == "assistive":
        go = len(hard_blockers) == 0
    else:
        go = len(blockers) == 0

    missing_dependencies = _build_missing_dependencies(activation_payload)

    activation_sequence = [
        {
            "step": 1,
            "surface": "platform_semantic",
            "status": "ready" if semantic_ready else "blocked",
        },
        {
            "step": 2,
            "surface": "platform_quadrant",
            "status": "ready" if quadrant_ready else "blocked",
        },
        {
            "step": 3,
            "surface": "project_middle_layer",
            "status": "ready" if middle_layer_ready else "blocked",
        },
    ]

    if include_va:
        activation_sequence.append(
            {
                "step": 4,
                "surface": "va",
                "status": "ready" if bool(va_readiness.get("deterministic_ready", False)) else "blocked",
            }
        )

    ready_gate_count = sum(1 for gate in readiness_gates if bool(gate.get("met", False)))
    total_gate_count = len(readiness_gates)
    readiness_percent = int((ready_gate_count / total_gate_count) * 100) if total_gate_count else 0

    ui_mode = "full_activation" if go else "safe_read_only"
    if policy_mode == "assistive":
        ui_mode = "guided_activation" if go else "guided_recovery"
    va_mode = "active" if bool(va_readiness.get("orchestration_available", False)) else "standby"
    if policy_mode == "strict":
        va_mode = "raw" if include_va else "disabled"

    if go and policy_mode == "assistive" and soft_blockers:
        activation_state = "active_with_soft_blockers"
    elif go:
        activation_state = "active"
    else:
        activation_state = "blocked"

    if policy_mode == "strict":
        recommended_actions: list[str] = []
    elif policy_mode == "assistive":
        recommended_actions = _build_assistive_actions(
            hard_blockers=hard_blockers,
            soft_blockers=soft_blockers,
            missing_dependencies=missing_dependencies,
            go=go,
        )
    else:
        recommended_actions = _build_recommended_actions(blockers)

    payload: dict[str, object] = {
        "app": "platform_activation",
        "boundary": "phase4-orchestration",
        "contract": "semantic-spine-orchestration",
        "contract_version": "1.0.0",
        "phase": 4,
        "decision_surface": True,
        "status": "active",
        "generated_at": timezone.now().isoformat(),
        "source_activation_contract": {
            "contract": activation_payload.get("contract", "semantic-spine-heartbeat"),
            "contract_version": activation_payload.get("contract_version", "1.0.0"),
        },
        "decision": {
            "go": go,
            "state": "go" if go else "no-go",
            "platform_wide_activation_state": activation_state,
        },
        "policy": {
            "mode": policy_mode,
            "strict_no_soft_pass": policy_mode == "strict",
            "assistive_soft_blockers_allowed": policy_mode == "assistive",
        },
        "blocking_capabilities": hard_blockers if policy_mode == "assistive" else blockers,
        "soft_blocking_capabilities": soft_blockers,
        "missing_dependencies": missing_dependencies,
        "readiness_gates": readiness_gates,
        "activation_sequence": activation_sequence,
        "recommended_next_actions": recommended_actions,
        "orchestration_hints": {
            "va": {
                "mode": va_mode,
                "include_va": include_va,
                "ready": bool(va_readiness.get("deterministic_ready", False)) if include_va else False,
            },
            "ui": {
                "mode": ui_mode,
                "allow_full_navigation": go,
                "fallback_banner": "Phase-4 orchestration blocked" if not go else "",
            },
        },
        "semantic_spine_health_summary": {
            "ready_gates": ready_gate_count,
            "total_gates": total_gate_count,
            "readiness_percent": readiness_percent,
            "heartbeat_ready": bool(activation_payload.get("deterministic_ready", False)),
        },
        "activation_payload": activation_payload,
        "deterministic_ready": go,
    }

    if include_va:
        payload["va_readiness"] = va_readiness

    return payload


def phase4_activation_view(request):
    include_va = _as_bool(request.GET.get("include_va"))
    mode = request.GET.get("mode")
    return JsonResponse(build_phase4_activation_payload(include_va=include_va, mode=str(mode or "")))


def phase4_orchestration_view(request):
    include_va = _as_bool(request.GET.get("include_va"))
    mode = request.GET.get("mode")
    return JsonResponse(build_phase4_orchestration_payload(include_va=include_va, mode=str(mode or "")))
