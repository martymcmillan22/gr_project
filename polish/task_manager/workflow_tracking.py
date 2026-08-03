from __future__ import annotations

from dataclasses import dataclass

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from polish.task_manager.assignment_engine import build_assignment_sequence, clamp_step_index, resolve_step
from polish.task_manager.constants import ITEM_STATUS_COMPLETED, ITEM_STATUS_RECEIVED, ITEM_STATUS_WORKING
from polish.task_manager.constants import get_task_archetype_definition
from polish.task_manager.models import TaskAssignment, TaskWorkflowItem
from polish.task_manager.models import TaskWorkflowDriftSnapshot
from polish.task_manager.permissions import user_can_create_assignment
from polish.task_manager.routing import (
    build_middle_layer_compartment_drift_detection,
    build_polish_compartment_refinement,
    build_va_compartment_narration,
    bind_deliverable_to_compartments,
    get_phase_policy,
    resolve_assignment_type_for_deliverable,
    task_manager_enabled_for_phase,
)


@dataclass(frozen=True)
class StepProgress:
    phase: str
    compartment: str
    step_index: int
    completed: bool


def _slot_key_for_item(*, phase: str, compartment: str, step_index: int) -> str:
    return f"{phase}:{compartment}:s{step_index + 1}"


def _record_drift_snapshot(*, item: TaskWorkflowItem, event_type: str, before: dict[str, object], after: dict[str, object], metadata: dict[str, object] | None = None):
    assignment = item.assignment
    deliverable_name = ""
    if isinstance(assignment.metadata, dict):
        deliverable_name = str(assignment.metadata.get("deliverable_routing", {}).get("deliverable", "") or "")

    drift_detection = build_middle_layer_compartment_drift_detection(
        assignment_type=assignment.assignment_type,
        deliverable_name=deliverable_name or assignment.title,
        drift_risk=0.0,
        alert_count=0,
    )
    match_row = None
    for row in drift_detection.get("compartments", []):
        if str(row.get("compartment", "")) == str(after.get("compartment", "")):
            match_row = row
            break

    payload = {
        "assignment_type": assignment.assignment_type,
        "deliverable": deliverable_name or assignment.title,
        "slot_drift": match_row or {},
    }

    TaskWorkflowDriftSnapshot.objects.create(
        assignment=assignment,
        item=item,
        slot_key=_slot_key_for_item(
            phase=str(after.get("phase", "")),
            compartment=str(after.get("compartment", "")),
            step_index=int(after.get("step_index", 0)),
        ),
        event_type=event_type,
        from_step_index=int(before.get("step_index", 0)),
        to_step_index=int(after.get("step_index", 0)),
        from_phase=str(before.get("phase", "")),
        to_phase=str(after.get("phase", "")),
        from_compartment=str(before.get("compartment", "")),
        to_compartment=str(after.get("compartment", "")),
        status_before=str(before.get("status", ITEM_STATUS_RECEIVED)),
        status_after=str(after.get("status", ITEM_STATUS_RECEIVED)),
        drift_payload=payload,
        metadata=metadata or {},
    )


@transaction.atomic
def create_assignment(
    *,
    created_by,
    assignment_type: str,
    title: str,
    assigned_to=None,
    operating_phase: str = "project",
    deliverable_name: str = "",
) -> TaskAssignment:
    normalized_assignment_type = str(assignment_type or "").strip().lower()
    if normalized_assignment_type in {"", "auto"}:
        normalized_assignment_type = resolve_assignment_type_for_deliverable(deliverable_name or title)

    if not user_can_create_assignment(created_by, normalized_assignment_type):
        raise PermissionDenied("User cannot create this assignment type.")

    if not task_manager_enabled_for_phase(operating_phase):
        raise PermissionDenied("Task Manager assignments are only allowed in the Project phase.")

    archetype = get_task_archetype_definition(normalized_assignment_type)
    phase_policy = get_phase_policy(operating_phase)
    routing = bind_deliverable_to_compartments(
        assignment_type=normalized_assignment_type,
        deliverable_name=deliverable_name or title,
    )
    drift_detection = build_middle_layer_compartment_drift_detection(
        assignment_type=normalized_assignment_type,
        deliverable_name=deliverable_name or title,
        drift_risk=0.0,
        alert_count=0,
    )
    va_narration = build_va_compartment_narration(
        assignment_type=normalized_assignment_type,
        deliverable_name=deliverable_name or title,
        drift_detection=drift_detection,
    )
    polish_refinement = build_polish_compartment_refinement(
        assignment_type=normalized_assignment_type,
        deliverable_name=deliverable_name or title,
    )

    assignment = TaskAssignment.objects.create(
        assignment_type=normalized_assignment_type,
        title=title,
        created_by=created_by,
        assigned_to=assigned_to,
        metadata={
            "task_archetype": {
                "key": archetype["key"],
                "label": archetype["label"],
                "compartment_count": archetype["compartment_count"],
                "tracks": archetype["tracks"],
                "cycles": archetype["cycles"],
                "phase_scope": list(archetype["phase_scope"]),
                "governance": archetype["governance"],
                "canonical_compartments": archetype.get("canonical_compartments", {}),
                "use_cases": list(archetype.get("use_cases", ())),
                "progression_model": routing.get("progression_model", "sequential"),
            },
            "phase_policy": phase_policy,
            "deliverable_routing": routing,
            "compartment_governance": {
                "va_narration": va_narration,
                "polish_refinement": polish_refinement,
                "middle_layer_drift_detection": drift_detection,
            },
        },
    )
    assignment.sync_position_from_step()
    assignment.save(update_fields=["current_phase", "current_compartment", "updated_at"])
    return assignment


@transaction.atomic
def attach_item(*, assignment: TaskAssignment, workflow_object, status: str = ITEM_STATUS_RECEIVED) -> TaskWorkflowItem:
    content_type = ContentType.objects.get_for_model(workflow_object.__class__)
    item, _ = TaskWorkflowItem.objects.get_or_create(
        assignment=assignment,
        content_type=content_type,
        object_id=workflow_object.pk,
        defaults={"status": status},
    )
    return item


@transaction.atomic
def advance_item(*, item: TaskWorkflowItem, steps: int = 1) -> StepProgress:
    sequence = build_assignment_sequence(item.assignment_type)
    if not sequence:
        raise ValueError("No sequence available for assignment type.")

    if item.status == ITEM_STATUS_COMPLETED:
        return StepProgress(
            phase=item.current_phase,
            compartment=item.current_compartment,
            step_index=item.current_step_index,
            completed=True,
        )

    before = {
        "phase": item.current_phase,
        "compartment": item.current_compartment,
        "step_index": item.current_step_index,
        "status": item.status,
    }

    next_index = clamp_step_index(item.assignment_type, item.current_step_index + max(1, steps))
    item.current_step_index = next_index
    item.status = ITEM_STATUS_WORKING
    if not item.started_at:
        item.started_at = timezone.now()

    at_end = next_index >= len(sequence) - 1
    if at_end:
        item.status = ITEM_STATUS_COMPLETED
        if not item.completed_at:
            item.completed_at = timezone.now()

    item.save()
    after = {
        "phase": item.current_phase,
        "compartment": item.current_compartment,
        "step_index": item.current_step_index,
        "status": item.status,
    }
    _record_drift_snapshot(item=item, event_type=TaskWorkflowDriftSnapshot.EVENT_ADVANCE, before=before, after=after, metadata={"steps": max(1, steps)})
    return StepProgress(
        phase=item.current_phase,
        compartment=item.current_compartment,
        step_index=item.current_step_index,
        completed=item.status == ITEM_STATUS_COMPLETED,
    )


@transaction.atomic
def skip_item_to_step(*, item: TaskWorkflowItem, step_index: int) -> StepProgress:
    before = {
        "phase": item.current_phase,
        "compartment": item.current_compartment,
        "step_index": item.current_step_index,
        "status": item.status,
    }

    item.current_step_index = clamp_step_index(item.assignment_type, step_index)
    if item.status == ITEM_STATUS_RECEIVED:
        item.status = ITEM_STATUS_WORKING
        if not item.started_at:
            item.started_at = timezone.now()

    item.save()
    after = {
        "phase": item.current_phase,
        "compartment": item.current_compartment,
        "step_index": item.current_step_index,
        "status": item.status,
    }
    _record_drift_snapshot(item=item, event_type=TaskWorkflowDriftSnapshot.EVENT_SKIP, before=before, after=after, metadata={"requested_step_index": step_index})
    return StepProgress(
        phase=item.current_phase,
        compartment=item.current_compartment,
        step_index=item.current_step_index,
        completed=item.status == ITEM_STATUS_COMPLETED,
    )


@transaction.atomic
def complete_item_early(*, item: TaskWorkflowItem) -> TaskWorkflowItem:
    before = {
        "phase": item.current_phase,
        "compartment": item.current_compartment,
        "step_index": item.current_step_index,
        "status": item.status,
    }
    item.status = ITEM_STATUS_COMPLETED
    if not item.completed_at:
        item.completed_at = timezone.now()
    item.save(update_fields=["status", "completed_at", "updated_at"])
    after = {
        "phase": item.current_phase,
        "compartment": item.current_compartment,
        "step_index": item.current_step_index,
        "status": item.status,
    }
    _record_drift_snapshot(item=item, event_type=TaskWorkflowDriftSnapshot.EVENT_COMPLETE, before=before, after=after)
    return item


@transaction.atomic
def resume_item(*, item: TaskWorkflowItem) -> TaskWorkflowItem:
    if item.status != ITEM_STATUS_COMPLETED:
        return item
    before = {
        "phase": item.current_phase,
        "compartment": item.current_compartment,
        "step_index": item.current_step_index,
        "status": item.status,
    }
    item.status = ITEM_STATUS_WORKING
    item.completed_at = None
    if not item.started_at:
        item.started_at = timezone.now()
    item.save(update_fields=["status", "completed_at", "started_at", "updated_at"])
    after = {
        "phase": item.current_phase,
        "compartment": item.current_compartment,
        "step_index": item.current_step_index,
        "status": item.status,
    }
    _record_drift_snapshot(item=item, event_type=TaskWorkflowDriftSnapshot.EVENT_RESUME, before=before, after=after)
    return item


def current_step(item: TaskWorkflowItem):
    return resolve_step(item.assignment_type, item.current_step_index)
