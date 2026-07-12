from django.db import models


class SemanticSchedule(models.Model):
    ACTION_CHOICES = [
        ("pipeline-run", "Pipeline Run"),
        ("export", "Export"),
        ("alert-check", "Alert Check"),
    ]

    STATUS_CHOICES = [
        ("idle", "Idle"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("paused", "Paused"),
    ]

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    cron_expression = models.CharField(max_length=64, default="0 0 * * *")
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    pipeline = models.ForeignKey(
        "project_middle_layer.SemanticPipeline",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schedules",
    )
    payload = models.JSONField(default=dict, blank=True)
    is_paused = models.BooleanField(default=False)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="idle")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SemanticScheduleRun(models.Model):
    STATUS_CHOICES = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    schedule = models.ForeignKey(
        "project_middle_layer.SemanticSchedule",
        on_delete=models.CASCADE,
        related_name="runs",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    triggered_by = models.CharField(max_length=120, default="manual")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at", "-id"]

    def __str__(self):
        return f"{self.schedule.slug} run {self.id}"
