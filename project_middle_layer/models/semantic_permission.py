from django.conf import settings
from django.db import models


class SemanticPermission(models.Model):
    role = models.ForeignKey("project_middle_layer.SemanticRole", on_delete=models.CASCADE, related_name="permissions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="semantic_permissions")
    project = models.ForeignKey("project_middle_layer.ProjectNode", on_delete=models.CASCADE, related_name="semantic_permissions", null=True, blank=True)
    tier = models.CharField(max_length=120, blank=True)
    branch = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.user_id}:{self.role.slug}"
