from django.conf import settings
from django.db import models

PATTERN_CHOICES = [
    ("billing", "Billing / Pricing"),
    ("ui", "UI / Navigation"),
    ("feature", "Feature Request"),
    ("bug", "Bug / Error"),
    ("performance", "Performance"),
    ("other", "Other"),
    ("", "Unclassified"),
]


class FAQ(models.Model):
    NORMAL = 0
    ELEVATED = 1
    HIGH = 2
    CRITICAL = 3

    PRIORITY_CHOICES = [
        (NORMAL, "Normal"),
        (ELEVATED, "Elevated"),
        (HIGH, "High"),
        (CRITICAL, "Critical"),
    ]

    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    priority = models.SmallIntegerField(
        choices=PRIORITY_CHOICES,
        default=NORMAL,
        help_text="Higher priority FAQs surface first in suggestions.",
    )
    positive_hits = models.PositiveIntegerField(
        default=0,
        help_text="Times this FAQ was viewed as a suggestion.",
    )
    negative_hits = models.PositiveIntegerField(
        default=0,
        help_text="Times negative feedback was submitted (proxy for unresolved issues).",
    )
    is_active = models.BooleanField(default=True)
    pattern_tag = models.CharField(
        max_length=20,
        choices=PATTERN_CHOICES,
        blank=True,
        default="",
        help_text="Links this FAQ to a negative feedback pattern for auto-suggestion.",
    )

    class Meta:
        ordering = ["-priority", "order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class Feedback(models.Model):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    SENTIMENT_CHOICES = [
        (POSITIVE, "Positive 👍"),
        (NEGATIVE, "Negative 👎"),
    ]

    PATTERN_CHOICES = PATTERN_CHOICES  # re-exported for backwards compat (admin, services)

    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES)
    text = models.TextField(blank=True, default="")
    pattern_tag = models.CharField(
        max_length=20,
        choices=PATTERN_CHOICES,
        blank=True,
        default="",
        help_text="Admin-assigned pattern for clustering negative feedback.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feedback_items",
    )
    page_url = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"

    def __str__(self):
        user_label = self.user.username if self.user else "anonymous"
        return f"{self.get_sentiment_display()} — {user_label} @ {self.created_at:%Y-%m-%d %H:%M}"
