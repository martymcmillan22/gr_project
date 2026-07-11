from django.contrib import admin

from .models import ProjectNode


@admin.register(ProjectNode)
class ProjectNodeAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "mlas_tier", "btif_classification", "updated_at")
    search_fields = ("slug", "name", "semantic_intent", "mlas_tier", "btif_classification")
    list_filter = ("mlas_tier", "btif_classification")
