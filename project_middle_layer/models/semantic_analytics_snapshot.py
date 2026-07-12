from django.db import models


class SemanticAnalyticsSnapshot(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    metrics = models.JSONField(default=dict)
    branch_filter = models.CharField(max_length=120, blank=True)
    tier_filter = models.CharField(max_length=120, blank=True)
    project_count = models.PositiveIntegerField(default=0)

    drift_mean = models.FloatField(default=0.0)
    drift_std = models.FloatField(default=0.0)
    confidence_mean = models.FloatField(default=0.0)
    confidence_std = models.FloatField(default=0.0)
    stability_mean = models.FloatField(default=0.0)
    stability_std = models.FloatField(default=0.0)

    lineage_cluster_map = models.JSONField(default=dict)
    tag_frequency_map = models.JSONField(default=dict)
    chart_series = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Semantic analytics snapshot {self.id} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
