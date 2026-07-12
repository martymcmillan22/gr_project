from django.conf import settings
from django.db import models


class MarketplaceItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ("plugin", "Plugin"),
        ("schema", "Schema"),
        ("agent", "Agent"),
        ("extension", "Extension"),
    ]

    slug = models.SlugField(max_length=120, unique=True)
    name = models.CharField(max_length=120)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    current_version = models.CharField(max_length=40, default="0.0.1")
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.item_type})"


class MarketplaceVersion(models.Model):
    item = models.ForeignKey(
        "project_middle_layer.MarketplaceItem",
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version = models.CharField(max_length=40)
    changelog = models.TextField(blank=True)
    compatibility = models.JSONField(default=dict, blank=True)
    dependency_slugs = models.JSONField(default=list, blank=True)
    download_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        unique_together = [("item", "version")]

    def __str__(self):
        return f"{self.item.slug}@{self.version}"


class MarketplaceInstall(models.Model):
    STATUS_CHOICES = [
        ("installed", "Installed"),
        ("updating", "Updating"),
        ("failed", "Failed"),
        ("removed", "Removed"),
    ]

    item = models.ForeignKey(
        "project_middle_layer.MarketplaceItem",
        on_delete=models.CASCADE,
        related_name="installs",
    )
    installed_version = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="installed")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marketplace_installs",
    )
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]

    def __str__(self):
        return f"{self.item.slug}:{self.installed_version} ({self.status})"
