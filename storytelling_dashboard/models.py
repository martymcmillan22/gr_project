from django.db import models
from django.conf import settings


class StorySession(models.Model):
    """Track user editing sessions for stories."""
    
    STATUS_CHOICES = [
        ('complete', 'Complete'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
    ]
    
    FORMAT_CHOICES = [
        ('short_series', 'Short Series (Sitcom)'),
        ('one_hour_series', '1-Hour Long Series Episode'),
        ('movie', 'Movie (90–120 minutes)'),
        ('epic_movie', 'Epic Movie (3+ hours)'),
    ]
    
    entry_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='movie')
    
    # Content snapshots (for draft management)
    talking_points = models.TextField(blank=True)
    core_concept = models.TextField(blank=True)
    synopsis = models.TextField(blank=True)
    
    # Metadata
    progress = models.IntegerField(default=0)  # 0-100
    last_edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    last_edited = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['entry_id']
        verbose_name = 'Story Entry'
        verbose_name_plural = 'Story Entries'
    
    def __str__(self):
        return f"{self.entry_id}. {self.title} ({self.get_status_display()})"
