from __future__ import annotations

from django.conf import settings

from polish.task_manager.constants import BTIF_COMPARTMENTS_BY_PHASE, BTIF_PHASE_ORDER


def resolve_supported_phases() -> tuple[str, ...]:
    """
    Resolve BTIF phases without changing BTIF core resolver code.
    """
    try:
        from platform_core.views import PRESET_ALIAS_CATALOG  # pylint: disable=import-outside-toplevel
    except Exception:
        return BTIF_PHASE_ORDER

    discovered: list[str] = []
    for item in PRESET_ALIAS_CATALOG:
        phase = (item.get("phase") or "").strip().lower()
        if phase and phase not in discovered and phase in BTIF_PHASE_ORDER:
            discovered.append(phase)

    if not discovered:
        return BTIF_PHASE_ORDER
    return tuple(discovered)


def resolve_phase_compartments() -> dict[str, tuple[str, ...]]:
    """
    Return phase -> compartment code mapping.

    Optional settings override supports future expansion/contraction while
    preserving assignment step-index semantics for existing records.
    """
    configured = getattr(settings, "TASK_MANAGER_BTIF_COMPARTMENTS", None)
    if not configured:
        return dict(BTIF_COMPARTMENTS_BY_PHASE)

    resolved: dict[str, tuple[str, ...]] = {}
    for phase in BTIF_PHASE_ORDER:
        values = configured.get(phase) if isinstance(configured, dict) else None
        if values:
            resolved[phase] = tuple(str(value).strip() for value in values if str(value).strip())
        else:
            resolved[phase] = BTIF_COMPARTMENTS_BY_PHASE[phase]
    return resolved
