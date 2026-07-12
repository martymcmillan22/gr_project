from django.db import models


class SemanticLineageRecord(models.Model):
    project = models.ForeignKey(
        "project_middle_layer.ProjectNode",
        on_delete=models.CASCADE,
        related_name="lineage_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    lineage_tree = models.JSONField(default=dict)
    semantic_clusters = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.project.slug} lineage @ {self.created_at:%Y-%m-%d %H:%M:%S}"
