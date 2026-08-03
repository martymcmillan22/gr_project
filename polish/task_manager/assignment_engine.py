from __future__ import annotations

from dataclasses import dataclass

from polish.task_manager.btif_adapter import resolve_phase_compartments, resolve_supported_phases
from polish.task_manager.constants import (
    get_task_archetype_definition,
)


@dataclass(frozen=True)
class AssignmentStep:
    step_index: int
    cycle: int
    phase: str
    compartment: str


def _active_phases_for_assignment(assignment_type: str) -> tuple[str, ...]:
    phases = resolve_supported_phases()
    definition = get_task_archetype_definition(assignment_type)
    allowed = set(phases)
    return tuple(phase for phase in definition.get("phase_scope", ()) if phase in allowed)


def _cycles_for_assignment(assignment_type: str) -> int:
    definition = get_task_archetype_definition(assignment_type)
    return int(definition.get("cycles", 1))


def build_assignment_sequence(assignment_type: str) -> list[AssignmentStep]:
    phase_compartments = resolve_phase_compartments()
    active_phases = _active_phases_for_assignment(assignment_type)
    cycles = _cycles_for_assignment(assignment_type)

    steps: list[AssignmentStep] = []
    cursor = 0
    for cycle in range(1, cycles + 1):
        for phase in active_phases:
            for compartment in phase_compartments.get(phase, ()):
                steps.append(
                    AssignmentStep(
                        step_index=cursor,
                        cycle=cycle,
                        phase=phase,
                        compartment=compartment,
                    )
                )
                cursor += 1
    return steps


def clamp_step_index(assignment_type: str, index: int) -> int:
    sequence = build_assignment_sequence(assignment_type)
    if not sequence:
        return 0
    return max(0, min(index, len(sequence) - 1))


def resolve_step(assignment_type: str, index: int) -> AssignmentStep | None:
    sequence = build_assignment_sequence(assignment_type)
    if not sequence:
        return None
    if index < 0:
        return sequence[0]
    if index >= len(sequence):
        return None
    return sequence[index]
