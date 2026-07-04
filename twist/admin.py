from django.contrib import admin
from . import models

@admin.register(models.CreativeIdea)
class CreativeIdeaAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'status', 'content_preview', 'tags', 'created_at')
	list_filter = ('status', 'created_at')
	search_fields = ('content', 'tags', 'user__email', 'user__username')
	ordering = ('-created_at',)

	def content_preview(self, obj):
		text = (obj.content or '').strip()
		if len(text) > 60:
			return f"{text[:57]}..."
		return text or '-'

	content_preview.short_description = 'Content'

