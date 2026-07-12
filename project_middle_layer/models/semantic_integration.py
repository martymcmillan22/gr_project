from django.db import models


class SemanticIntegration(models.Model):
    DIRECTION_CHOICES = [
        ("inbound", "Inbound"),
        ("outbound", "Outbound"),
        ("bidirectional", "Bidirectional"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("disabled", "Disabled"),
    ]

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    target_system = models.CharField(max_length=120)
    endpoint_url = models.URLField(max_length=500, blank=True)
    api_key = models.CharField(max_length=64, unique=True)
    permissions = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
