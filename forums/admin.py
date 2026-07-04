from django.contrib import admin

from .models import ForumPost


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
	list_display = ("title", "forum_type", "author", "created_at")
	list_filter = ("forum_type", "created_at")
	search_fields = ("title", "body", "author__username", "author__email")
