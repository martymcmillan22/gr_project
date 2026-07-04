from django.contrib import admin
from django.core.files.base import File
from django.utils import timezone
from pathlib import Path

from .models import (
	PolishTask,
	SectorAgenda,
	PolishReminderPreference,
	TaskAssignment,
	TaskAssignmentAttachment,
	TaskAttachmentAuditLog,
	TaskAttachmentQuarantine,
	TaskManagerAnalyticsExportRun,
	TaskObjective,
	TaskWorkflowItem,
)
from .task_manager.models import TaskAttachmentAuditLog
from .task_manager.attachment_security import scan_uploaded_attachment


@admin.register(PolishTask)
class PolishTaskAdmin(admin.ModelAdmin):
	list_display = ("title", "user", "due_date", "is_completed", "updated_at")
	list_filter = ("is_completed",)
	search_fields = ("title", "details", "user__email", "user__username")


@admin.register(SectorAgenda)
class SectorAgendaAdmin(admin.ModelAdmin):
	list_display = ("sector_name", "idea", "user", "created_at")
	search_fields = ("sector_name", "idea", "objective", "user__email", "user__username")


@admin.register(PolishReminderPreference)
class PolishReminderPreferenceAdmin(admin.ModelAdmin):
	list_display = ("user", "enabled", "last_reminded_on")
	list_filter = ("enabled",)
	search_fields = ("user__email", "user__username")


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
	list_display = (
		"title",
		"assignment_type",
		"created_by",
		"assigned_to",
		"current_phase",
		"current_compartment",
		"is_closed",
		"updated_at",
	)
	list_filter = ("assignment_type", "current_phase", "is_closed")
	search_fields = ("title", "created_by__email", "assigned_to__email", "created_by__username", "assigned_to__username")


@admin.register(TaskWorkflowItem)
class TaskWorkflowItemAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"assignment",
		"assignment_type",
		"status",
		"current_phase",
		"current_compartment",
		"updated_at",
	)
	list_filter = ("assignment_type", "status", "current_phase")


@admin.register(TaskObjective)
class TaskObjectiveAdmin(admin.ModelAdmin):
	list_display = ("id", "assignment", "created_by", "is_attached", "created_at")
	list_filter = ("is_attached",)
	search_fields = ("objective_text", "created_by__email", "created_by__username", "assignment__title")


@admin.register(TaskAssignmentAttachment)
class TaskAssignmentAttachmentAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"assignment",
		"label",
		"uploaded_by",
		"scan_status",
		"download_count",
		"created_at",
	)
	list_filter = ("scan_status",)
	search_fields = ("label", "assignment__title", "uploaded_by__email", "uploaded_by__username")


@admin.register(TaskAttachmentQuarantine)
class TaskAttachmentQuarantineAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"assignment",
		"original_filename",
		"uploaded_by",
		"scan_status",
		"review_status",
		"file_size_bytes",
		"created_at",
	)
	list_filter = ("scan_status", "review_status")
	search_fields = ("original_filename", "reason", "uploaded_by__email", "uploaded_by__username")
	actions = ("approve_quarantine_items", "rescan_quarantine_items", "delete_quarantine_items")

	@admin.action(description="Approve selected quarantine items")
	def approve_quarantine_items(self, request, queryset):
		approved_count = 0
		for quarantine in queryset.select_related("assignment", "uploaded_by"):
			if not quarantine.file:
				continue
			attachment = TaskAssignmentAttachment(
				assignment=quarantine.assignment,
				uploaded_by=quarantine.uploaded_by,
				label=quarantine.label,
				file_size_bytes=quarantine.file_size_bytes,
				file_sha256="",
				scan_status=TaskAssignmentAttachment.SCAN_CLEAN,
				scan_notes="Admin approved from quarantine.",
				scanned_at=timezone.now(),
			)
			with quarantine.file.open("rb") as source:
				safe_name = Path(quarantine.original_filename).name or Path(quarantine.file.name).name
				attachment.file.save(safe_name, File(source), save=False)
			attachment.save()
			TaskAttachmentAuditLog.objects.create(
				assignment=quarantine.assignment,
				actor=request.user,
				event_type=TaskAttachmentAuditLog.EVENT_REVIEW_APPROVED,
				filename=quarantine.original_filename,
				content_type=quarantine.content_type,
				file_size_bytes=quarantine.file_size_bytes,
				reason="Admin approved quarantined attachment.",
				metadata={"attachment_id": attachment.id},
			)
			quarantine.review_status = quarantine.REVIEW_APPROVED
			quarantine.review_notes = "Approved and released by admin"
			quarantine.reviewed_by = request.user
			quarantine.reviewed_at = timezone.now()
			quarantine.save(update_fields=["review_status", "review_notes", "reviewed_by", "reviewed_at"])
			if quarantine.file:
				quarantine.file.delete(save=False)
			quarantine.delete()
			approved_count += 1
		self.message_user(request, f"Approved {approved_count} quarantine item(s).")

	@admin.action(description="Re-scan selected quarantine items")
	def rescan_quarantine_items(self, request, queryset):
		rescanned_count = 0
		for quarantine in queryset.select_related("assignment"):
			if not quarantine.file:
				continue
			result = scan_uploaded_attachment(quarantine.file)
			quarantine.scan_status = result.status
			quarantine.reason = result.notes
			quarantine.review_status = quarantine.REVIEW_RESCANNED
			quarantine.review_notes = "Rescanned by admin"
			quarantine.reviewed_by = request.user
			quarantine.reviewed_at = timezone.now()
			quarantine.save(
				update_fields=[
					"scan_status",
					"reason",
					"review_status",
					"review_notes",
					"reviewed_by",
					"reviewed_at",
				]
			)
			TaskAttachmentAuditLog.objects.create(
				assignment=quarantine.assignment,
				actor=request.user,
				event_type=TaskAttachmentAuditLog.EVENT_REVIEW_RESCANNED,
				filename=quarantine.original_filename,
				content_type=quarantine.content_type,
				file_size_bytes=quarantine.file_size_bytes,
				reason=f"Rescan result: {result.status}",
				metadata={"scan_notes": result.notes, "sha256": result.sha256},
			)
			rescanned_count += 1
		self.message_user(request, f"Rescanned {rescanned_count} quarantine item(s).")

	@admin.action(description="Delete selected quarantine items")
	def delete_quarantine_items(self, request, queryset):
		deleted_count = 0
		for quarantine in queryset.select_related("assignment"):
			TaskAttachmentAuditLog.objects.create(
				assignment=quarantine.assignment,
				actor=request.user,
				event_type=TaskAttachmentAuditLog.EVENT_REVIEW_DELETED,
				filename=quarantine.original_filename,
				content_type=quarantine.content_type,
				file_size_bytes=quarantine.file_size_bytes,
				reason="Admin deleted quarantined attachment.",
			)
			if quarantine.file:
				quarantine.file.delete(save=False)
			quarantine.delete()
			deleted_count += 1
		self.message_user(request, f"Deleted {deleted_count} quarantine item(s).")


@admin.register(TaskAttachmentAuditLog)
class TaskAttachmentAuditLogAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"assignment",
		"actor",
		"event_type",
		"filename",
		"file_size_bytes",
		"created_at",
	)
	list_filter = ("event_type",)
	search_fields = ("filename", "reason", "actor__email", "actor__username")


@admin.register(TaskManagerAnalyticsExportRun)
class TaskManagerAnalyticsExportRunAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"trigger_source",
		"export_format",
		"status",
		"requested_by",
		"target_user",
		"created_at",
		"completed_at",
	)
	list_filter = ("trigger_source", "export_format", "status")
	search_fields = ("requested_by__email", "target_user__email", "notes", "artifact_paths", "error_message")
