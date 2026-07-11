from __future__ import annotations

from django.contrib.auth import get_user_model
from django.conf import settings

from project_middle_layer.models import ProjectNode, SemanticPermission, SemanticUserProfile


def _project_tier(project: ProjectNode | None) -> str:
    if not project:
        return ""
    return str((project.metadata or {}).get("visibility_tier", "")).strip().lower()


def has_semantic_capability(
    user,
    capability: str,
    *,
    project: ProjectNode | None = None,
    tier: str | None = None,
    branch: str | None = None,
) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    try:
        profile = SemanticUserProfile.objects.select_related("default_role").get(user=user)
    except SemanticUserProfile.DoesNotExist:
        strict_mode = bool(getattr(settings, "PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS", False))
        if strict_mode:
            return False
        # Compatibility mode: allow authenticated users until explicit role mappings are configured.
        return True

    normalized_capability = (capability or "").strip().lower()
    requested_tier = (tier or _project_tier(project)).strip().lower()
    requested_branch = (branch or "").strip().lower()

    if profile.default_role and normalized_capability in [str(item).strip().lower() for item in (profile.default_role.capabilities or [])]:
        return True

    query = SemanticPermission.objects.filter(user=user, is_active=True).select_related("role")

    if project:
        query = query.filter(project=project)
    elif requested_tier:
        query = query.filter(tier=requested_tier)
    else:
        query = query.filter(project__isnull=True)

    if requested_branch:
        query = query.filter(branch__in=["", requested_branch])

    for permission in query:
        role_caps = [str(item).strip().lower() for item in (permission.role.capabilities or [])]
        if normalized_capability in role_caps:
            return True

    return False


def resolve_actor_by_username(username: str | None):
    name = (username or "").strip()
    if not name:
        return None
    user_model = get_user_model()
    return user_model.objects.filter(username=name).first()
