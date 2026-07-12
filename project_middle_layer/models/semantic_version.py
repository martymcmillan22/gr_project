from django.conf import settings
from django.db import models


class SemanticVersion(models.Model):
    project = models.ForeignKey("project_middle_layer.ProjectNode", on_delete=models.CASCADE, related_name="semantic_versions")
    version_number = models.PositiveIntegerField()
    snapshot = models.ForeignKey("project_middle_layer.ProjectEvolutionSnapshot", on_delete=models.SET_NULL, null=True, blank=True, related_name="semantic_versions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="semantic_versions")
    message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        unique_together = [("project", "version_number")]

    def __str__(self):
        return f"{self.project.slug} v{self.version_number}"
