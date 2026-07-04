from __future__ import annotations

from polish.task_manager.constants import (
    ASSIGNMENT_DOUBLE_LINEAR,
    ASSIGNMENT_LINEAR,
    ASSIGNMENT_PERPETUAL,
    ASSIGNMENT_TWELVE_POINT,
)


ROLE_TO_ALLOWED_ASSIGNMENTS = {
    "botanists": {ASSIGNMENT_LINEAR},
    "engineers": {ASSIGNMENT_LINEAR, ASSIGNMENT_DOUBLE_LINEAR, ASSIGNMENT_TWELVE_POINT},
    "architects": {ASSIGNMENT_TWELVE_POINT, ASSIGNMENT_PERPETUAL},
}

ALLOWED_ATTACHMENT_DOWNLOAD_ROLES = {"botanists", "engineers", "architects"}


def allowed_assignment_types_for_user(user) -> set[str]:
    if not user or not user.is_authenticated:
        return set()
    if user.is_superuser:
        return {
            ASSIGNMENT_LINEAR,
            ASSIGNMENT_DOUBLE_LINEAR,
            ASSIGNMENT_TWELVE_POINT,
            ASSIGNMENT_PERPETUAL,
        }

    group_names = {name.lower() for name in user.groups.values_list("name", flat=True)}
    allowed: set[str] = set()
    for role_name, role_allowed in ROLE_TO_ALLOWED_ASSIGNMENTS.items():
        if role_name in group_names:
            allowed |= role_allowed
    return allowed


def user_can_create_assignment(user, assignment_type: str) -> bool:
    if assignment_type == ASSIGNMENT_PERPETUAL and not (user and user.is_authenticated and user.is_premium_subscriber()):
        return False
    return assignment_type in allowed_assignment_types_for_user(user)


def user_can_download_attachment(user, assignment, attachment) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True

    group_names = {name.lower() for name in user.groups.values_list("name", flat=True)}
    if not (group_names & ALLOWED_ATTACHMENT_DOWNLOAD_ROLES):
        return False

    return (
        assignment.created_by_id == user.id
        or assignment.assigned_to_id == user.id
        or attachment.uploaded_by_id == user.id
    )
