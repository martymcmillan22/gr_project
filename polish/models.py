from django.conf import settings
from django.db import models


class PolishTask(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="polish_tasks",
	)
	title = models.CharField(max_length=200)
	details = models.TextField(blank=True)
	due_date = models.DateField(null=True, blank=True)
	is_completed = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("is_completed", "due_date", "-created_at")

	def __str__(self):
		return self.title


class SectorAgenda(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="sector_agendas",
	)
	sector_name = models.CharField(max_length=120)
	idea = models.CharField(max_length=240)
	objective = models.CharField(max_length=240, blank=True)
	agenda_text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("-created_at",)

	def __str__(self):
		return f"{self.sector_name} - {self.idea}"


class PolishReminderPreference(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="polish_reminder_preference",
	)
	enabled = models.BooleanField(default=False)
	last_reminded_on = models.DateField(null=True, blank=True)

	def __str__(self):
		state = "On" if self.enabled else "Off"
		return f"Polish reminder ({state}) for {self.user}"


from .task_manager.models import (  # noqa: E402,F401
	TaskAssignment,
	TaskAssignmentAttachment,
	TaskAttachmentAuditLog,
	TaskAttachmentQuarantine,
	TaskManagerAnalyticsExportRun,
	TaskObjective,
	TaskWorkflowDriftSnapshot,
	TaskWorkflowItem,
)
