from django.contrib import admin

from .models import HomepageAction, HomepageBackendItem, HomepageFlow, HomepagePreference, HomepageTask


@admin.register(HomepageBackendItem)
class HomepageBackendItemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "summary", "owner__username", "owner__email")


@admin.register(HomepageTask)
class HomepageTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "owner", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "description", "owner__username", "owner__email")


@admin.register(HomepageFlow)
class HomepageFlowAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "progress", "owner", "updated_at")
    list_filter = ("status",)
    search_fields = ("name", "message", "owner__username", "owner__email")


@admin.register(HomepagePreference)
class HomepagePreferenceAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "notifications", "dark_mode", "updated_at")
    list_filter = ("notifications", "dark_mode")
    search_fields = ("owner__username", "owner__email")


@admin.register(HomepageAction)
class HomepageActionAdmin(admin.ModelAdmin):
    list_display = ("id", "label", "owner", "created_at")
    search_fields = ("label", "owner__username", "owner__email")
