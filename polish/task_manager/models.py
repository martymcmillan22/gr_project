from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from polish.task_manager.constants import (
    ASSIGNMENT_CHOICES,
    ASSIGNMENT_LINEAR,
    ITEM_STATUS_CHOICES,
    ITEM_STATUS_RECEIVED,
    PHASE_CREATE,
)
from polish.task_manager.assignment_engine import resolve_step


class TaskAssignment(models.Model):
    assignment_type = models.CharField(max_length=32, choices=ASSIGNMENT_CHOICES, default=ASSIGNMENT_LINEAR)
    title = models.CharField(max_length=200)
    visibility = models.CharField(
        max_length=16,
        choices=[("public", "Public"), ("personal", "Personal")],
        default="public",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_task_assignments",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_assignments",
        null=True,
        blank=True,
    )
    current_step_index = models.PositiveSmallIntegerField(default=0)
    current_phase = models.CharField(max_length=16, default=PHASE_CREATE)
    current_compartment = models.CharField(max_length=8, default="R")
    is_closed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-created_at")

    def __str__(self):
        return f"{self.title} ({self.assignment_type})"

    def sync_position_from_step(self):
        step = resolve_step(self.assignment_type, self.current_step_index)
        if step is None:
            return
        self.current_phase = step.phase
        self.current_compartment = step.compartment


class TaskObjective(models.Model):
    assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name="objectives",
    )
    objective_text = models.TextField()
    visibility = models.CharField(
        max_length=16,
        choices=[("public", "Public"), ("personal", "Personal")],
        default="public",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_objectives",
    )
    is_attached = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at", "id")

    def __str__(self):
        short_text = self.objective_text[:60]
        return f"Objective #{self.id}: {short_text}"


class TaskAssignmentAttachment(models.Model):
    SCAN_PENDING = "pending"
    SCAN_CLEAN = "clean"
    SCAN_FLAGGED = "flagged"
    SCAN_ERROR = "error"
    SCAN_STATUS_CHOICES = (
        (SCAN_PENDING, "Pending"),
        (SCAN_CLEAN, "Clean"),
        (SCAN_FLAGGED, "Flagged"),
        (SCAN_ERROR, "Error"),
    )

    assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_assignment_attachments",
    )
    label = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to="task_manager_attachments/%Y/%m/%d/")
    file_size_bytes = models.BigIntegerField(default=0)
    file_sha256 = models.CharField(max_length=64, blank=True)
    scan_status = models.CharField(max_length=16, choices=SCAN_STATUS_CHOICES, default=SCAN_PENDING)
    scan_notes = models.CharField(max_length=255, blank=True)
    scanned_at = models.DateTimeField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self):
        return self.label or self.file.name


class TaskAttachmentQuarantine(models.Model):
    REVIEW_PENDING = "pending"
    REVIEW_APPROVED = "approved"
    REVIEW_RESCANNED = "rescanned"
    REVIEW_DELETED = "deleted"
    REVIEW_STATUS_CHOICES = (
        (REVIEW_PENDING, "Pending"),
        (REVIEW_APPROVED, "Approved"),
        (REVIEW_RESCANNED, "Rescanned"),
        (REVIEW_DELETED, "Deleted"),
    )

    assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name="quarantined_attachments",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_quarantine_items",
    )
    original_filename = models.CharField(max_length=255)
    label = models.CharField(max_length=200, blank=True)
    content_type = models.CharField(max_length=120, blank=True)
    file_size_bytes = models.BigIntegerField(default=0)
    file = models.FileField(upload_to="task_manager_quarantine/%Y/%m/%d/")
    scan_status = models.CharField(max_length=16, blank=True)
    reason = models.CharField(max_length=255)
    review_status = models.CharField(max_length=16, choices=REVIEW_STATUS_CHOICES, default=REVIEW_PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_task_quarantine_items",
    )
    review_notes = models.CharField(max_length=255, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self):
        return f"Quarantine #{self.id}: {self.original_filename}"


class TaskAttachmentAuditLog(models.Model):
    EVENT_ALLOWED = "allowed"
    EVENT_BLOCKED = "blocked"
    EVENT_REMOVED = "removed"
    EVENT_REVIEW_APPROVED = "review_approved"
    EVENT_REVIEW_RESCANNED = "review_rescanned"
    EVENT_REVIEW_DELETED = "review_deleted"
    EVENT_CHOICES = (
        (EVENT_ALLOWED, "Allowed"),
        (EVENT_BLOCKED, "Blocked"),
        (EVENT_REMOVED, "Removed"),
        (EVENT_REVIEW_APPROVED, "Review Approved"),
        (EVENT_REVIEW_RESCANNED, "Review Rescanned"),
        (EVENT_REVIEW_DELETED, "Review Deleted"),
    )

    assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name="attachment_audit_logs",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_attachment_audit_logs",
    )
    event_type = models.CharField(max_length=16, choices=EVENT_CHOICES)
    filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=120, blank=True)
    file_size_bytes = models.BigIntegerField(default=0)
    reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self):
        return f"{self.event_type} by {self.actor_id} on assignment {self.assignment_id}"


class TaskManagerAnalyticsExportRun(models.Model):
    SOURCE_UI = "ui"
    SOURCE_COMMAND = "command"
    SOURCE_CHOICES = (
        (SOURCE_UI, "UI"),
        (SOURCE_COMMAND, "Command"),
    )

    FORMAT_CSV = "csv"
    FORMAT_PDF = "pdf"
    FORMAT_BOTH = "both"
    FORMAT_CHOICES = (
        (FORMAT_CSV, "CSV"),
        (FORMAT_PDF, "PDF"),
        (FORMAT_BOTH, "Both"),
    )

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_manager_export_runs",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_manager_exports_as_target",
    )
    trigger_source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default=SOURCE_UI)
    export_format = models.CharField(max_length=8, choices=FORMAT_CHOICES, default=FORMAT_CSV)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    output_dir = models.CharField(max_length=255, blank=True)
    artifact_paths = models.TextField(blank=True)
    notes = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self):
        return f"{self.trigger_source}:{self.export_format}:{self.status}"


class TaskWorkflowItem(models.Model):
    assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name="workflow_items",
    )
    assignment_type = models.CharField(max_length=32, choices=ASSIGNMENT_CHOICES, default=ASSIGNMENT_LINEAR)
    status = models.CharField(max_length=16, choices=ITEM_STATUS_CHOICES, default=ITEM_STATUS_RECEIVED)
    current_step_index = models.PositiveSmallIntegerField(default=0)
    current_phase = models.CharField(max_length=16, default=PHASE_CREATE)
    current_compartment = models.CharField(max_length=8, default="R")

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    workflow_object = GenericForeignKey("content_type", "object_id")

    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("assignment", "content_type", "object_id"),
                name="ux_task_workflow_item_assignment_object",
            ),
        ]

    def __str__(self):
        return f"Item {self.id} [{self.assignment_type}] {self.status}"

    def sync_position_from_step(self):
        step = resolve_step(self.assignment_type, self.current_step_index)
        if step is None:
            return
        self.current_phase = step.phase
        self.current_compartment = step.compartment

    def save(self, *args, **kwargs):
        if self.assignment_id:
            self.assignment_type = self.assignment.assignment_type
        self.sync_position_from_step()
        super().save(*args, **kwargs)


class TaskWorkflowDriftSnapshot(models.Model):
    EVENT_ADVANCE = "advance"
    EVENT_SKIP = "skip"
    EVENT_COMPLETE = "complete"
    EVENT_RESUME = "resume"
    EVENT_CHOICES = (
        (EVENT_ADVANCE, "Advance"),
        (EVENT_SKIP, "Skip"),
        (EVENT_COMPLETE, "Complete"),
        (EVENT_RESUME, "Resume"),
    )

    assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name="drift_snapshots",
    )
    item = models.ForeignKey(
        TaskWorkflowItem,
        on_delete=models.CASCADE,
        related_name="drift_snapshots",
    )
    slot_key = models.CharField(max_length=64)
    event_type = models.CharField(max_length=16, choices=EVENT_CHOICES)

    from_step_index = models.PositiveSmallIntegerField(default=0)
    to_step_index = models.PositiveSmallIntegerField(default=0)
    from_phase = models.CharField(max_length=16, default=PHASE_CREATE)
    to_phase = models.CharField(max_length=16, default=PHASE_CREATE)
    from_compartment = models.CharField(max_length=8, default="R")
    to_compartment = models.CharField(max_length=8, default="R")
    status_before = models.CharField(max_length=16, choices=ITEM_STATUS_CHOICES, default=ITEM_STATUS_RECEIVED)
    status_after = models.CharField(max_length=16, choices=ITEM_STATUS_CHOICES, default=ITEM_STATUS_RECEIVED)

    drift_payload = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(fields=("assignment", "created_at"), name="idx_task_drift_assignment_ts"),
            models.Index(fields=("item", "created_at"), name="idx_task_drift_item_ts"),
            models.Index(fields=("assignment", "slot_key", "created_at"), name="idx_task_drift_slot_ts"),
        ]

    def __str__(self):
        return (
            f"assignment={self.assignment_id} item={self.item_id} "
            f"{self.event_type} {self.from_phase}:{self.from_compartment} -> {self.to_phase}:{self.to_compartment}"
        )
