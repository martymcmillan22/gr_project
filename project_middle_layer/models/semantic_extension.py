from django.db import models


class SemanticExtension(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    schema_patch = models.JSONField(default=dict, blank=True)
    rules_patch = models.JSONField(default=dict, blank=True)
    version = models.CharField(max_length=40, default="0.0.1")
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    rollback_payload = models.JSONField(default=dict, blank=True)
    validation_report = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} v{self.version}"
