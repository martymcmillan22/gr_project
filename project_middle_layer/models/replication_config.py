from django.db import models


class ReplicationConfig(models.Model):
    MODE_CHOICES = [
        ("full", "Full Replication"),
        ("branch_only", "Branch Only"),
        ("tier_only", "Tier Only"),
        ("snapshot_only", "Snapshot Only"),
    ]

    DIRECTION_CHOICES = [
        ("push", "Push"),
        ("pull", "Pull"),
        ("bidirectional", "Bidirectional"),
    ]

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    remote_node_url = models.URLField(max_length=500)
    api_key = models.CharField(max_length=128)
    mode = models.CharField(max_length=32, choices=MODE_CHOICES, default="full")
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default="bidirectional")
    is_active = models.BooleanField(default=True)
    last_synced_version = models.PositiveIntegerField(default=0)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, default="idle")
    last_error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
