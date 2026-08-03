from django.contrib import admin

from platform_reference.models import PlatformReferenceGICSReferenceSchema
from platform_reference.models import PlatformReferenceNAICSReferenceSchema


@admin.register(PlatformReferenceNAICSReferenceSchema)
class NAICSReferenceAdmin(admin.ModelAdmin):
	list_display = ("code", "title", "sector_code", "source_version", "is_active", "updated_at")
	list_filter = ("is_active", "source_version")
	search_fields = ("code", "title", "sector_code")
	ordering = ("code",)


@admin.register(PlatformReferenceGICSReferenceSchema)
class GICSReferenceAdmin(admin.ModelAdmin):
	list_display = ("code", "name", "level", "parent_code", "source_version", "is_active", "updated_at")
	list_filter = ("level", "is_active", "source_version")
	search_fields = ("code", "name", "parent_code")
	ordering = ("level", "code")
