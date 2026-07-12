from django.db import models


class SemanticPlugin(models.Model):
    slug = models.SlugField(max_length=120, unique=True)
    name = models.CharField(max_length=120)
    plugin_type = models.CharField(max_length=40, default="agent")
    entrypoint = models.CharField(max_length=255)
    capabilities = models.JSONField(default=list, blank=True)
    version = models.CharField(max_length=40, default="0.0.1")
    enabled = models.BooleanField(default=False)
    last_status = models.CharField(max_length=20, default="idle")
    last_error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
