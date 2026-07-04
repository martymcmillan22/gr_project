from django.contrib import admin
from django.core.cache import cache
from .models import CareerPath, CareerFilterPreset

@admin.register(CareerPath)
class CareerPathAdmin(admin.ModelAdmin):
    # Customize columns shown inside the admin dashboard table view
    list_display = ('subject', 'degree_level_code', 'degree_name', 'career_title', 'salary_metric')
    list_filter = ('subject', 'degree_level_code')
    search_fields = ('subject', 'career_title')

    def save_model(self, request, obj, form, change):
        """Wipes the cache whenever a record is added or modified via Admin."""
        super().save_model(request, obj, form, change)
        cache.clear()

    def delete_model(self, request, obj):
        """Wipes the cache whenever a record is deleted via Admin."""
        super().delete_model(request, obj)
        cache.clear()


@admin.register(CareerFilterPreset)
class CareerFilterPresetAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'degree_query', 'sort_by', 'updated')
    list_filter = ('sort_by', 'updated')
    search_fields = ('user__username', 'name')
