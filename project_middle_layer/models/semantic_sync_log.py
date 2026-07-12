from django.db import models


class SemanticSyncLog(models.Model):
    SYNC_TYPE_CHOICES = [
        ("version", "Version Sync"),
        ("snapshot", "Snapshot Sync"),
        ("lineage", "Lineage Sync"),
        ("tag", "Tag Sync"),
        ("alert", "Alert/Recommendation Sync"),
    ]

    STATUS_CHOICES = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    source_node = models.CharField(max_length=255, blank=True)
    target_node = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at", "-id"]

    def __str__(self):
        return f"{self.sync_type} sync {self.id}"
