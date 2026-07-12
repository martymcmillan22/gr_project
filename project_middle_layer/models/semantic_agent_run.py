from django.db import models


class SemanticAgentRun(models.Model):
    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    agent_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    actions_taken = models.JSONField(default=list, blank=True)
    insights_generated = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.agent_name} run {self.id}"
