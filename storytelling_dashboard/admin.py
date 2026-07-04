from django.contrib import admin
from .models import StorySession


@admin.register(StorySession)
class StorySessionAdmin(admin.ModelAdmin):
    list_display = ('entry_id', 'title', 'status', 'format', 'progress', 'last_edited', 'last_edited_by')
    list_filter = ('status', 'format', 'created', 'last_edited')
    search_fields = ('title', 'entry_id')
    readonly_fields = ('entry_id', 'created', 'last_edited')
    fieldsets = (
        ('Story Info', {
            'fields': ('entry_id', 'title', 'status', 'format')
        }),
        ('Content', {
            'fields': ('talking_points', 'core_concept', 'synopsis'),
            'classes': ('wide',)
        }),
        ('Progress', {
            'fields': ('progress',)
        }),
        ('Metadata', {
            'fields': ('last_edited_by', 'last_edited', 'created'),
            'classes': ('collapse',)
        }),
    )
