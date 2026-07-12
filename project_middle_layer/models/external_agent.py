from django.db import models


class ExternalAgent(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("disabled", "Disabled"),
    ]

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    endpoint = models.URLField(max_length=500)
    capabilities = models.JSONField(default=list, blank=True)
    auth_token = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
