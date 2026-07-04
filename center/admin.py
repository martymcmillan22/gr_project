from django.contrib import admin

from .models import CorporationItem


@admin.register(CorporationItem)
class CorporationItemAdmin(admin.ModelAdmin):
	list_display = ("title", "owner", "item_type", "status", "work_status", "priority", "due_date", "updated_at")
	list_filter = ("status", "work_status", "item_type", "priority")
	search_fields = ("title", "description", "owner__email", "owner__username")
