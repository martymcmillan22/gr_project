from django.conf import settings
from django.db import models


class ForumPost(models.Model):
	FORUM_CITY = "city"
	FORUM_STATE = "state"
	FORUM_NATIONAL = "national"
	FORUM_GLOBAL = "global"

	FORUM_CHOICES = [
		(FORUM_CITY, "City Forum"),
		(FORUM_STATE, "State Forum"),
		(FORUM_NATIONAL, "National Forum"),
		(FORUM_GLOBAL, "Global Forum"),
	]

	VISIBILITY_PUBLIC = "public"
	VISIBILITY_PERSONAL = "personal"
	VISIBILITY_CHOICES = [
		(VISIBILITY_PUBLIC, "Public"),
		(VISIBILITY_PERSONAL, "Personal"),
	]

	forum_type = models.CharField(max_length=20, choices=FORUM_CHOICES)
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts")
	title = models.CharField(max_length=160)
	body = models.TextField()
	visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default=VISIBILITY_PUBLIC)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.get_forum_type_display()}: {self.title}"
