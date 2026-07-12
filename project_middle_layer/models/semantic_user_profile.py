from django.conf import settings
from django.db import models


class SemanticUserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="semantic_profile")
    default_role = models.ForeignKey("project_middle_layer.SemanticRole", on_delete=models.SET_NULL, null=True, blank=True, related_name="default_for_profiles")
    preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self):
        return f"Semantic profile for user {self.user_id}"
