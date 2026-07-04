from __future__ import annotations

from dataclasses import dataclass

from polish.task_manager.btif_adapter import resolve_phase_compartments, resolve_supported_phases
from polish.task_manager.constants import (
    ASSIGNMENT_DOUBLE_LINEAR,
    ASSIGNMENT_LINEAR,
    ASSIGNMENT_PERPETUAL,
    ASSIGNMENT_TWELVE_POINT,
)


@dataclass(frozen=True)
class AssignmentStep:
    step_index: int
    cycle: int
    phase: str
    compartment: str


def _active_phases_for_assignment(assignment_type: str) -> tuple[str, ...]:
    phases = resolve_supported_phases()
    if assignment_type == ASSIGNMENT_LINEAR:
        return (phases[0],)
    if assignment_type == ASSIGNMENT_DOUBLE_LINEAR:
        return phases[:2]
    if assignment_type in {ASSIGNMENT_TWELVE_POINT, ASSIGNMENT_PERPETUAL}:
        return phases
    raise ValueError(f"Unsupported assignment type: {assignment_type}")


def _cycles_for_assignment(assignment_type: str) -> int:
    if assignment_type == ASSIGNMENT_PERPETUAL:
        return 2
    return 1


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
