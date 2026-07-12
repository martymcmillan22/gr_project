from django.db import models


class SemanticCrossSyncLog(models.Model):
    SYNC_TYPE_CHOICES = [
        ("full", "Full Sync"),
        ("delta", "Delta Sync"),
        ("version", "Version Sync"),
        ("lineage", "Lineage Sync"),
        ("analytics", "Analytics Sync"),
        ("insight", "Insight Sync"),
    ]

    STATUS_CHOICES = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    source_platform = models.CharField(max_length=120, default="local")
    target_platform = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    summary = models.JSONField(default=dict, blank=True)
    conflict_report = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at", "-id"]

    def __str__(self):
        return f"{self.sync_type} -> {self.target_platform} ({self.status})"
