from django.db import models


class DistributedAgentRun(models.Model):
    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    agent_name = models.CharField(max_length=120)
    node_count = models.PositiveIntegerField(default=0)
    shard_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    metrics = models.JSONField(default=dict, blank=True)
    insights = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.agent_name} distributed run {self.id}"
