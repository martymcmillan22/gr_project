from django.db import models


class SemanticAlert(models.Model):
    ALERT_TYPE_CHOICES = [
        ("high_drift", "High Drift"),
        ("low_confidence", "Low Confidence"),
        ("unstable_stability", "Unstable Stability"),
        ("schema_failure", "Schema Failure"),
        ("repeated_schema_failure", "Repeated Schema Failure"),
        ("timeline_drift_trend", "Timeline Drift Trend"),
    ]

    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    project = models.ForeignKey(
        "project_middle_layer.ProjectNode",
        on_delete=models.CASCADE,
        related_name="semantic_alerts",
    )
    source_snapshot = models.ForeignKey(
        "project_middle_layer.ProjectEvolutionSnapshot",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="semantic_alerts",
    )
    alert_type = models.CharField(max_length=64, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    message = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.get_alert_type_display()} for {self.project.slug}"
