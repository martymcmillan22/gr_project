from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class SemanticEditSession(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("released", "Released"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="semantic_edit_sessions")
    project = models.ForeignKey("project_middle_layer.ProjectNode", on_delete=models.CASCADE, related_name="edit_sessions")
    started_at = models.DateTimeField(auto_now_add=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        ordering = ["-started_at", "-id"]

    def __str__(self):
        return f"Edit session {self.id} for {self.project.slug}"

    def refresh_lease(self, *, minutes: int = 20):
        self.lease_expires_at = timezone.now() + timedelta(minutes=max(1, minutes))
        self.status = "active"
        self.save(update_fields=["lease_expires_at", "status"])
