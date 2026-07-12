from django.db import models


class SemanticShard(models.Model):
    STRATEGY_CHOICES = [
        ("branch", "By Branch"),
        ("tier", "By Tier"),
        ("slug_prefix", "By Project Slug Prefix"),
        ("cluster", "By Semantic Cluster"),
    ]

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    node_url = models.URLField(max_length=500, blank=True)
    strategy = models.CharField(max_length=32, choices=STRATEGY_CHOICES, default="branch")
    route_value = models.CharField(max_length=120, blank=True)
    project_slug_prefix = models.CharField(max_length=20, blank=True)
    cluster_label = models.CharField(max_length=120, blank=True)
    branch = models.CharField(max_length=120, blank=True)
    tier = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    health_score = models.PositiveSmallIntegerField(default=100)
    status = models.CharField(max_length=20, default="healthy")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
