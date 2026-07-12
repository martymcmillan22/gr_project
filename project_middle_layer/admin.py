from django.contrib import admin

from .models import (
    ProjectNode,
    SemanticAuditLog,
    SemanticChangeRequest,
    SemanticEditSession,
    SemanticPermission,
    SemanticRole,
    SemanticUserProfile,
    SemanticVersion,
)


@admin.register(ProjectNode)
class ProjectNodeAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "mlas_tier", "btif_classification", "updated_at")
    search_fields = ("slug", "name", "semantic_intent", "mlas_tier", "btif_classification")
    list_filter = ("mlas_tier", "btif_classification")


@admin.register(SemanticRole)
class SemanticRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "updated_at")
    search_fields = ("name", "slug")


@admin.register(SemanticPermission)
class SemanticPermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "project", "tier", "branch", "is_active", "created_at")
    search_fields = ("user__username", "role__slug", "project__slug", "tier", "branch")
    list_filter = ("is_active", "tier", "branch")


@admin.register(SemanticUserProfile)
class SemanticUserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "default_role", "updated_at")
    search_fields = ("user__username", "default_role__slug")


@admin.register(SemanticEditSession)
class SemanticEditSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "user", "status", "lease_expires_at", "started_at")
    search_fields = ("project__slug", "user__username", "status")
    list_filter = ("status",)


@admin.register(SemanticChangeRequest)
class SemanticChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "author", "status", "reviewer", "created_at", "reviewed_at")
    search_fields = ("project__slug", "author__username", "reviewer__username", "status")
    list_filter = ("status",)


@admin.register(SemanticAuditLog)
class SemanticAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "source", "action", "project", "actor")
    search_fields = ("source", "action", "project__slug", "actor__username")
    list_filter = ("source", "action")


@admin.register(SemanticVersion)
class SemanticVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "version_number", "author", "created_at")
    search_fields = ("project__slug", "author__username", "message")
    list_filter = ("project",)
