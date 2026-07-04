from django.db import models
from django.conf import settings

class CareerPath(models.Model):
    subject = models.CharField(max_length=255, db_index=True)
    degree_level_code = models.IntegerField(db_index=True)
    degree_name = models.CharField(max_length=100)
    career_title = models.CharField(max_length=255)
    salary_metric = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Career Path Assignment"
        verbose_name_plural = "Career Path Assignments"

    def __str__(self):
        return f"[{self.subject}] {self.career_title} (${self.salary_metric})"


class CareerFilterPreset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='career_filter_presets')
    name = models.CharField(max_length=120)
    degree_query = models.CharField(max_length=10, blank=True, default='')
    sort_by = models.CharField(max_length=30, default='salary_desc')
    selected_subjects = models.JSONField(default=list)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('user', 'name')
        verbose_name = 'Career Filter Preset'
        verbose_name_plural = 'Career Filter Presets'

    def __str__(self):
        return f"{self.user.username}::{self.name}"

