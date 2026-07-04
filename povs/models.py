from django.conf import settings
from django.db import models


class ExpoFact(models.Model):
    """Red stage — a set of news facts posted by staff to anchor POV responses."""
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expo_facts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Expository Fact Set'
        verbose_name_plural = 'Expository Fact Sets'

    def __str__(self):
        return self.title


class POVResponse(models.Model):
    """A user's progressive POV response to one ExpoFact.

    Stage gate rules (enforced by properties and views):
        Blue       first_person      — always available
        Green      prediction        — requires first_person completed
        Yellow     narrative         — requires prediction completed
        Green-Lime probable_outcome  — requires narrative completed
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pov_responses',
    )
    expo_fact = models.ForeignKey(
        ExpoFact,
        on_delete=models.CASCADE,
        related_name='responses',
    )

    # Blue
    first_person = models.TextField(blank=True)
    first_person_at = models.DateTimeField(null=True, blank=True)

    # Green
    prediction = models.TextField(blank=True)
    prediction_at = models.DateTimeField(null=True, blank=True)

    # Yellow
    narrative = models.TextField(blank=True)
    narrative_at = models.DateTimeField(null=True, blank=True)

    # Green-Lime
    probable_outcome = models.TextField(blank=True)
    probable_outcome_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'expo_fact')]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user} → {self.expo_fact}"

    @property
    def can_predict(self):
        return bool(self.first_person.strip())

    @property
    def can_narrate(self):
        return bool(self.prediction.strip())

    @property
    def can_add_outcome(self):
        return bool(self.narrative.strip())
