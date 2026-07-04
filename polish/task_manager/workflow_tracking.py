from __future__ import annotations

from dataclasses import dataclass

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from polish.task_manager.assignment_engine import build_assignment_sequence, clamp_step_index, resolve_step
from polish.task_manager.constants import ITEM_STATUS_COMPLETED, ITEM_STATUS_RECEIVED, ITEM_STATUS_WORKING
from polish.task_manager.models import TaskAssignment, TaskWorkflowItem
from polish.task_manager.permissions import user_can_create_assignment


@dataclass(frozen=True)
class StepProgress:
    phase: str
    compartment: str
    step_index: int
    completed: bool


@transaction.atomic
def create_assignment(*, created_by, assignment_type: str, title: str, assigned_to=None) -> TaskAssignment:
    if not user_can_create_assignment(created_by, assignment_type):
        raise PermissionDenied("User cannot create this assignment type.")

    assignment = TaskAssignment.objects.create(
        assignment_type=assignment_type,
        title=title,
        created_by=created_by,
        assigned_to=assigned_to,
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
    return StepProgress(
        phase=item.current_phase,
        compartment=item.current_compartment,
        step_index=item.current_step_index,
        completed=item.status == ITEM_STATUS_COMPLETED,
    )


@transaction.atomic
def skip_item_to_step(*, item: TaskWorkflowItem, step_index: int) -> StepProgress:
    item.current_step_index = clamp_step_index(item.assignment_type, step_index)
    if item.status == ITEM_STATUS_RECEIVED:
        item.status = ITEM_STATUS_WORKING
        if not item.started_at:
            item.started_at = timezone.now()

    item.save()
    return StepProgress(
        phase=item.current_phase,
        compartment=item.current_compartment,
        step_index=item.current_step_index,
        completed=item.status == ITEM_STATUS_COMPLETED,
    )


@transaction.atomic
def complete_item_early(*, item: TaskWorkflowItem) -> TaskWorkflowItem:
    item.status = ITEM_STATUS_COMPLETED
    if not item.completed_at:
        item.completed_at = timezone.now()
    item.save(update_fields=["status", "completed_at", "updated_at"])
    return item


@transaction.atomic
def resume_item(*, item: TaskWorkflowItem) -> TaskWorkflowItem:
    if item.status != ITEM_STATUS_COMPLETED:
        return item
    item.status = ITEM_STATUS_WORKING
    item.completed_at = None
    if not item.started_at:
        item.started_at = timezone.now()
    item.save(update_fields=["status", "completed_at", "started_at", "updated_at"])
    return item


def current_step(item: TaskWorkflowItem):
    return resolve_step(item.assignment_type, item.current_step_index)
