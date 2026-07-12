from django.db import models


class ProjectEvolutionSnapshot(models.Model):
    project = models.ForeignKey(
        "project_middle_layer.ProjectNode",
        on_delete=models.CASCADE,
        related_name="evolution_snapshots",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    identity_payload = models.JSONField(default=dict)
    drift_forecast = models.JSONField(default=dict)
    branch_resolution = models.JSONField(default=dict)
    specialized_path = models.JSONField(default=dict)
    semantic_tags = models.JSONField(default=list)
    identity_uri = models.CharField(max_length=255)
    branch_name = models.CharField(max_length=120, blank=True)
    drift_risk = models.FloatField(default=0.0)
    confidence_score = models.PositiveSmallIntegerField(default=0)
    confidence_label = models.CharField(max_length=20, default="Volatile")
    schema_issue_count = models.PositiveSmallIntegerField(default=0)
    recommendations = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.project.slug} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
