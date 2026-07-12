from django.conf import settings
from django.db import models


class SemanticAuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="semantic_audit_logs")
    action = models.CharField(max_length=120)
    project = models.ForeignKey("project_middle_layer.ProjectNode", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    payload = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=50, default="system")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action} ({self.source})"
