import datetime
import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone


class Issue(models.Model):
	publication_name = models.CharField(max_length=120, default="BaseTrue Monthly")
	masthead_title = models.CharField(max_length=180, default="The BaseTrue Bulletin")
	month = models.PositiveSmallIntegerField()
	year = models.PositiveSmallIntegerField()
	tagline = models.CharField(max_length=220, blank=True)

	class Meta:
		ordering = ["-year", "-month"]
		constraints = [
			models.UniqueConstraint(fields=["year", "month"], name="unique_issue_month_year"),
		]

	def __str__(self):
		return f"{self.masthead_title} - {self.month_name} {self.year}"

	@property
	def month_name(self):
		return datetime.date(1900, self.month, 1).strftime("%B")

	@property
	def issue_date(self):
		return datetime.date(self.year, self.month, 1)


class StoryQuerySet(models.QuerySet):
	def published(self):
		now = timezone.now()
		return self.filter(status=Story.Status.PUBLISHED, publish_at__lte=now)


class Story(models.Model):
	class Feature(models.TextChoices):
		PIP = "pip", "Perpetual Infrastructure Program"
		BASE_TRUE = "base_true", "Base True Information Format"

	class Status(models.TextChoices):
		DRAFT = "draft", "Draft"
		SCHEDULED = "scheduled", "Scheduled"
		PUBLISHED = "published", "Published"

	issue = models.ForeignKey(Issue, related_name="stories", on_delete=models.CASCADE)
	feature = models.CharField(max_length=20, choices=Feature.choices)
	headline = models.CharField(max_length=220)
	byline = models.CharField(max_length=120)
	dek = models.CharField(max_length=280, blank=True)
	body = models.TextField()
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
	publish_at = models.DateTimeField(help_text="Set a future date to stage stories ahead of release.")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	objects = StoryQuerySet.as_manager()

	class Meta:
		ordering = ["feature", "publish_at", "id"]

	def __str__(self):
		return self.headline

	@property
	def is_live(self):
		return self.status == self.Status.PUBLISHED and self.publish_at <= timezone.now()


class NewsletterSubscriber(models.Model):
	email = models.EmailField(unique=True)
	is_active = models.BooleanField(default=True)
	unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	joined_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-joined_at"]

	def __str__(self):
		return self.email

	def get_unsubscribe_path(self):
		return reverse("baseTrue_news:unsubscribe", kwargs={"token": self.unsubscribe_token})

# Create your models here.
