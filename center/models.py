from django.conf import settings
from django.db import models


class CorporationItem(models.Model):
	TYPE_CAMPAIGN = "campaign"
	TYPE_EVENT = "event"
	TYPE_PARTNERSHIP = "partnership"
	TYPE_GENERAL = "general"
	TYPE_CHOICES = (
		(TYPE_CAMPAIGN, "Campaign"),
		(TYPE_EVENT, "Event"),
		(TYPE_PARTNERSHIP, "Partnership"),
		(TYPE_GENERAL, "General"),
	)

	STATUS_DRAFT = "draft"
	STATUS_REVIEW = "review"
	STATUS_APPROVED = "approved"
	STATUS_POSTED = "posted"
	STATUS_CHOICES = (
		(STATUS_DRAFT, "Draft"),
		(STATUS_REVIEW, "Review"),
		(STATUS_APPROVED, "Approved"),
		(STATUS_POSTED, "Posted"),
	)

	WORK_STATUS_TODO = "todo"
	WORK_STATUS_IN_PROGRESS = "in_progress"
	WORK_STATUS_DONE = "done"
	WORK_STATUS_CHOICES = (
		(WORK_STATUS_TODO, "To Do"),
		(WORK_STATUS_IN_PROGRESS, "In Progress"),
		(WORK_STATUS_DONE, "Done"),
	)

	PRIORITY_LOW = "low"
	PRIORITY_MEDIUM = "medium"
	PRIORITY_HIGH = "high"
	PRIORITY_CHOICES = (
		(PRIORITY_LOW, "Low"),
		(PRIORITY_MEDIUM, "Medium"),
		(PRIORITY_HIGH, "High"),
	)

	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="corporation_items",
	)
	reviewer = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="reviewed_corporation_items",
	)
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	item_type = models.CharField(max_length=24, choices=TYPE_CHOICES, default=TYPE_GENERAL)
	status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
	priority = models.CharField(max_length=12, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
	due_date = models.DateField(null=True, blank=True)
	approved_at = models.DateTimeField(null=True, blank=True)
	work_status = models.CharField(max_length=20, choices=WORK_STATUS_CHOICES, null=True, blank=True)
	work_started_at = models.DateTimeField(null=True, blank=True)
	work_completed_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-updated_at", "-created_at")

	def __str__(self):
		return f"{self.title} ({self.get_status_display()})"

	def can_transition_to(self, next_status):
		transitions = {
			self.STATUS_DRAFT: {self.STATUS_REVIEW},
			self.STATUS_REVIEW: {self.STATUS_APPROVED, self.STATUS_DRAFT},
			self.STATUS_APPROVED: {self.STATUS_POSTED, self.STATUS_REVIEW},
			self.STATUS_POSTED: set(),
		}
		return next_status in transitions.get(self.status, set())

	def can_transition_work_to(self, next_work_status):
		if self.status != self.STATUS_POSTED:
			return False

		current = self.work_status or self.WORK_STATUS_TODO
		transitions = {
			self.WORK_STATUS_TODO: {self.WORK_STATUS_IN_PROGRESS},
			self.WORK_STATUS_IN_PROGRESS: {self.WORK_STATUS_DONE},
			self.WORK_STATUS_DONE: set(),
		}
		return next_work_status in transitions.get(current, set())
