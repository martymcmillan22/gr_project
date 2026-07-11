from django.db import models
from django.conf import settings




class CreativeIdea(models.Model):
    STATUS_RAW = 'RAW'
    STATUS_SEED = 'SEED'
    STATUS_PROJECT = 'PROJECT'
    STATUS_BUSINESS = 'BUSINESS'
    STATUS_CHOICES = [
        (STATUS_RAW, 'Raw'),
        (STATUS_SEED, 'Seed'),
        (STATUS_PROJECT, 'Project'),
        (STATUS_BUSINESS, 'Business (Legacy)'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(blank=True)# For typed text or transcriptions
    tags = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RAW)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def __str__(self):
        preview = (self.content or '').strip()
        if len(preview) > 40:
            preview = f"{preview[:37]}..."
        return f"{self.user} - {preview or 'No content'}"

    class Meta:
        ordering = ['-created_at'] # Shows newest idea first

