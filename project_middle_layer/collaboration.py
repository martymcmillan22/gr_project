from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from project_middle_layer.models import ProjectNode, SemanticEditSession


def acquire_edit_session(*, project: ProjectNode, user, force_takeover: bool = False, lease_minutes: int = 20) -> SemanticEditSession:
    now = timezone.now()
    active = (
        SemanticEditSession.objects.filter(project=project, status="active")
        .order_by("-started_at", "-id")
        .first()
    )

    if active and active.lease_expires_at and active.lease_expires_at <= now:
        active.status = "expired"
        active.save(update_fields=["status"])
        active = None

    if active and active.user_id != getattr(user, "id", None) and not force_takeover:
        raise ValueError("Project is currently being edited by another user.")

    if active and active.user_id != getattr(user, "id", None) and force_takeover:
        active.status = "released"
        active.save(update_fields=["status"])

    if active and active.user_id == getattr(user, "id", None):
        active.lease_expires_at = now + timedelta(minutes=max(1, lease_minutes))
        active.save(update_fields=["lease_expires_at"])
        return active

    return SemanticEditSession.objects.create(
        user=user,
        project=project,
        status="active",
        lease_expires_at=now + timedelta(minutes=max(1, lease_minutes)),
    )


def release_edit_session(*, session: SemanticEditSession) -> SemanticEditSession:
    session.status = "released"
    session.save(update_fields=["status"])
    return session


def heartbeat_edit_session(*, session: SemanticEditSession, user, lease_minutes: int = 20) -> SemanticEditSession:
    if session.user_id != getattr(user, "id", None):
        raise ValueError("Only the session owner can refresh this edit session.")
    session.refresh_lease(minutes=lease_minutes)
    return session
