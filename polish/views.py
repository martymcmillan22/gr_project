from datetime import timedelta
import csv
import io
import mimetypes
from pathlib import Path
from urllib.parse import urlencode

from django.contrib import admin, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.core.files.base import File
from django.views.decorators.http import require_GET
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from center.models import CorporationItem
from seeds.models import Idea, Seed, Business

from .forms import PolishTaskForm, SectorAgendaForm, PolishReminderPreferenceForm
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
from .task_manager.assignment_engine import build_assignment_sequence
from .task_manager.attachment_security import is_clamscan_available, scan_uploaded_attachment
from .task_manager.constants import (
    ASSIGNMENT_CHOICES,
    ASSIGNMENT_DOCUMENT_TITLES,
    ASSIGNMENT_LINEAR,
    BTIF_COMPARTMENTS_BY_PHASE,
)
from .task_manager.permissions import allowed_assignment_types_for_user, user_can_download_attachment
from .task_manager.workflow_tracking import (
    advance_item,
    attach_item,
    complete_item_early,
    create_assignment,
    resume_item,
    skip_item_to_step,
)


def _build_agenda_text(sector_name, idea, objective):
    objective_line = objective if objective else f"Validate and launch {idea} in {sector_name}."
    lines = [
        f"Sector: {sector_name}",
        f"Core Idea: {idea}",
        f"Objective: {objective_line}",
        "",  # spacer
        "Agenda:",
        "1. Market Snapshot: define target customer and demand signals.",
        "2. Offer Design: package the idea into a clear business offer.",
        "3. Revenue Path: define pricing, channels, and first sale plan.",
        "4. Execution Tasks: identify owners, deadlines, and dependencies.",
        "5. Risk Review: list top 3 risks and mitigation actions.",
        "6. Next 7 Days: commit to measurable deliverables.",
    ]
    return "\n".join(lines)


WORKFLOW_SOURCE_MODELS = {
    "idea": Idea,
    "seed": Seed,
    "business": Business,
    "corporation": CorporationItem,
}

ALLOWED_TASK_MANAGER_TABS = {"create", "attach", "assignment", "item", "metrics", "ops-metrics", "quarantine", "activity"}
ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md", ".xlsx", ".csv", ".png", ".jpg", ".jpeg"}
POLISH_ADMIN_GROUP_NAME = "polish_admin"
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "image/png",
    "image/jpeg",
}


def user_is_polish_admin(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return bool(
        user.is_superuser
        or user.is_staff
        or user.groups.filter(name=POLISH_ADMIN_GROUP_NAME).exists()
    )


class PolishAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not user_is_polish_admin(request.user):
            return redirect("center:corporation_admin")
        return super().dispatch(request, *args, **kwargs)


def _format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(max(value, 0))
    unit = units[0]
    for candidate in units:
        unit = candidate
        if size < 1024 or candidate == units[-1]:
            break
        size /= 1024
    if unit == "B":
        return f"{int(size)} {unit}"
    return f"{size:.2f} {unit}"


def _current_objective_text_for_assignment(assignment: TaskAssignment) -> str:
    candidate_item = assignment.workflow_items.exclude(status="completed").order_by("current_step_index", "id").first()
    if candidate_item is None:
        candidate_item = assignment.workflow_items.order_by("current_step_index", "id").first()
    if candidate_item and candidate_item.workflow_object and hasattr(candidate_item.workflow_object, "objective_text"):
        return candidate_item.workflow_object.objective_text
    if candidate_item and candidate_item.workflow_object:
        return str(candidate_item.workflow_object)
    return "No objective attached"


def _record_attachment_audit(
    *,
    assignment: TaskAssignment,
    actor,
    event_type: str,
    filename: str = "",
    content_type: str = "",
    file_size_bytes: int = 0,
    reason: str = "",
    metadata: dict | None = None,
):
    TaskAttachmentAuditLog.objects.create(
        assignment=assignment,
        actor=actor,
        event_type=event_type,
        filename=filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        reason=reason,
        metadata=metadata or {},
    )


def _quarantine_upload(*, assignment: TaskAssignment, actor, uploaded_file, label: str, reason: str, scan_status: str = ""):
    uploaded_file.seek(0)
    TaskAttachmentQuarantine.objects.create(
        assignment=assignment,
        uploaded_by=actor,
        original_filename=uploaded_file.name,
        label=label,
        content_type=(uploaded_file.content_type or "").strip(),
        file_size_bytes=uploaded_file.size,
        file=uploaded_file,
        reason=reason,
        scan_status=scan_status,
    )


def _assignment_accessible_to_user(assignment, user):
    return assignment.created_by_id == user.id or assignment.assigned_to_id == user.id


def _quarantine_accessible_to_user(quarantine, user):
    if user_is_polish_admin(user):
        return True
    return quarantine.uploaded_by_id == user.id


def _quarantine_queryset_for_user(user):
    queryset = TaskAttachmentQuarantine.objects.select_related("assignment", "uploaded_by", "reviewed_by")
    if user_is_polish_admin(user):
        return queryset
    return queryset.filter(uploaded_by=user)


def _promote_quarantine_to_attachment(*, quarantine: TaskAttachmentQuarantine, actor, notes: str = ""):
    attachment = TaskAssignmentAttachment(
        assignment=quarantine.assignment,
        uploaded_by=quarantine.uploaded_by,
        label=quarantine.label,
        file_size_bytes=quarantine.file_size_bytes,
        file_sha256="",
        scan_status=TaskAssignmentAttachment.SCAN_CLEAN,
        scan_notes=notes or "Approved from quarantine.",
        scanned_at=timezone.now(),
    )

    with quarantine.file.open("rb") as source:
        safe_name = Path(quarantine.original_filename).name or Path(quarantine.file.name).name
        attachment.file.save(safe_name, File(source), save=False)
    attachment.save()
    return attachment


def _build_source_options(user):
    options = []
    for idea in Idea.objects.filter(user=user).order_by("-updated_at")[:6]:
        options.append((f"idea:{idea.id}", f"Idea #{idea.id} ({idea.status})"))
    for seed in Seed.objects.filter(idea__user=user).order_by("-updated_at")[:6]:
        options.append((f"seed:{seed.id}", f"Seed #{seed.id} (Idea #{seed.idea_id})"))
    for business in Business.objects.filter(seed__idea__user=user).order_by("-updated_at")[:6]:
        options.append((f"business:{business.id}", f"Business #{business.id} ({business.brand_name})"))
    for item in CorporationItem.objects.filter(owner=user).order_by("-updated_at")[:6]:
        options.append((f"corporation:{item.id}", f"Corporation Item #{item.id} ({item.title})"))
    return options


def _resolve_workflow_object_for_user(user, source_token):
    if ":" not in source_token:
        return None
    model_key, object_id = source_token.split(":", 1)
    model = WORKFLOW_SOURCE_MODELS.get(model_key)
    if model is None:
        return None

    if model is Idea:
        return Idea.objects.filter(pk=object_id, user=user).first()
    if model is Seed:
        return Seed.objects.filter(pk=object_id, idea__user=user).first()
    if model is Business:
        return Business.objects.filter(pk=object_id, seed__idea__user=user).first()
    if model is CorporationItem:
        return CorporationItem.objects.filter(pk=object_id, owner=user).first()
    return None


def _ordered_compartment_codes():
    seen = set()
    ordered = []
    for phase in ("create", "post", "work"):
        for code in BTIF_COMPARTMENTS_BY_PHASE.get(phase, ()):
            if code not in seen:
                ordered.append(code)
                seen.add(code)
    return ordered


def _ordered_compartment_slots():
    alias_map = {
        ("post", "P"): "PU",
        ("work", "P"): "PI",
    }
    slots = []
    for phase in ("create", "post", "work"):
        for code in BTIF_COMPARTMENTS_BY_PHASE.get(phase, ()):
            slot_key = f"{phase}-{code}".lower().replace(" ", "-")
            slots.append(
                {
                    "phase": phase,
                    "raw_code": code,
                    "display_code": alias_map.get((phase, code), code),
                    "slot_key": slot_key,
                }
            )
    return slots


def _build_task_manager_metrics(user):
    assignments_qs = TaskAssignment.objects.filter(created_by=user)
    items_qs = TaskWorkflowItem.objects.filter(assignment__created_by=user)

    phase_counts = {
        "create": items_qs.filter(current_phase="create").count(),
        "post": items_qs.filter(current_phase="post").count(),
        "work": items_qs.filter(current_phase="work").count(),
    }

    compartment_slots = []
    for slot in _ordered_compartment_slots():
        slot_count = items_qs.filter(current_phase=slot["phase"], current_compartment=slot["raw_code"]).count()
        compartment_slots.append(
            {
                "slot_key": slot["slot_key"],
                "code": slot["display_code"],
                "phase": slot["phase"],
                "raw_code": slot["raw_code"],
                "count": slot_count,
            }
        )

    compartment_counts = {slot["code"]: slot["count"] for slot in compartment_slots}

    today = timezone.localdate()
    window_start = today - timedelta(days=6)

    created_rows = {
        row["day"]: row["count"]
        for row in (
            assignments_qs.filter(created_at__date__gte=window_start)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
        )
    }
    completed_rows = {
        row["day"]: row["count"]
        for row in (
            assignments_qs.filter(is_closed=True, updated_at__date__gte=window_start)
            .annotate(day=TruncDate("updated_at"))
            .values("day")
            .annotate(count=Count("id"))
        )
    }

    assignment_timeline = []
    for offset in range(7):
        day = window_start + timedelta(days=offset)
        assignment_timeline.append(
            {
                "day": day.isoformat(),
                "created": created_rows.get(day, 0),
                "completed": completed_rows.get(day, 0),
            }
        )

    statuses = ["received", "working", "completed"]
    phases = ["create", "post", "work"]
    lifecycle_counts = (
        items_qs.values("current_phase", "status")
        .annotate(count=Count("id"))
        .order_by()
    )
    lifecycle_lookup = {
        (row["current_phase"], row["status"]): row["count"] for row in lifecycle_counts
    }
    lifecycle_matrix = [
        [lifecycle_lookup.get((phase, status), 0) for phase in phases] for status in statuses
    ]

    compartment_flow = [
        {
            "code": slot["code"],
            "raw_code": slot["raw_code"],
            "slot_key": slot["slot_key"],
            "count": slot["count"],
            "phase": slot["phase"],
        }
        for slot in compartment_slots
    ]

    now = timezone.now()
    throughput_7d = assignments_qs.filter(is_closed=True, completed_at__date__gte=window_start).count()

    velocity_values = []
    for item in items_qs:
        end_time = item.completed_at or now
        start_time = item.started_at or item.created_at
        duration_days = max((end_time - start_time).total_seconds() / 86400.0, 1 / 24)
        velocity_values.append((item.current_step_index + 1) / duration_days)
    avg_item_velocity = round(sum(velocity_values) / len(velocity_values), 2) if velocity_values else 0

    dwell_rows = {}
    for item in items_qs:
        dwell_hours = max((now - item.updated_at).total_seconds() / 3600.0, 0)
        bucket = dwell_rows.setdefault(item.current_compartment, {"total": 0.0, "count": 0})
        bucket["total"] += dwell_hours
        bucket["count"] += 1
    compartment_dwell_time = {
        code: round(values["total"] / values["count"], 2) for code, values in dwell_rows.items() if values["count"]
    }

    create_to_start_values = []
    start_to_complete_values = []
    for item in items_qs:
        if item.started_at:
            create_to_start_values.append(max((item.started_at - item.created_at).total_seconds() / 3600.0, 0))
        if item.started_at and item.completed_at:
            start_to_complete_values.append(max((item.completed_at - item.started_at).total_seconds() / 3600.0, 0))

    phase_transition_latency = {
        "create_to_start_hours": round(sum(create_to_start_values) / len(create_to_start_values), 2)
        if create_to_start_values
        else 0,
        "start_to_complete_hours": round(sum(start_to_complete_values) / len(start_to_complete_values), 2)
        if start_to_complete_values
        else 0,
    }

    productivity_rows = (
        assignments_qs.values("assigned_to__username", "assigned_to__email")
        .annotate(total=Count("id"), completed=Count("id", filter=Q(is_closed=True)))
        .order_by("-completed", "-total")
    )
    productivity = []
    for row in productivity_rows:
        total = row["total"] or 0
        completed = row["completed"] or 0
        productivity.append(
            {
                "user": row["assigned_to__username"] or row["assigned_to__email"] or "unassigned",
                "total": total,
                "completed": completed,
                "completion_rate": round((completed / total) * 100, 2) if total else 0,
            }
        )

    return {
        "total_assignments": assignments_qs.count(),
        "active_assignments": assignments_qs.filter(is_closed=False).count(),
        "completed_assignments": assignments_qs.filter(is_closed=True).count(),
        "total_items": items_qs.count(),
        "items_in_progress": items_qs.filter(status="working").count(),
        "items_completed": items_qs.filter(status="completed").count(),
        "phase_counts": phase_counts,
        "compartment_counts": compartment_counts,
        "compartment_slots": compartment_slots,
        "assignment_timeline": assignment_timeline,
        "item_lifecycle_heatmap": {
            "phases": phases,
            "statuses": statuses,
            "matrix": lifecycle_matrix,
        },
        "compartment_flow": compartment_flow,
        "operational_metrics": {
            "assignment_throughput_7d": throughput_7d,
            "item_velocity_steps_per_day": avg_item_velocity,
            "compartment_dwell_time_hours": compartment_dwell_time,
            "phase_transition_latency_hours": phase_transition_latency,
            "per_user_productivity": productivity,
        },
    }


def _build_task_manager_activity(user):
    events = []

    assignments = TaskAssignment.objects.filter(created_by=user).order_by("-updated_at")[:20]
    for assignment in assignments:
        state = "completed" if assignment.is_closed else "active"
        events.append(
            {
                "timestamp": assignment.updated_at,
                "message": (
                    f"Assignment #{assignment.id} ({assignment.title}) is {state} at "
                    f"{assignment.current_phase.upper()}:{assignment.current_compartment}."
                ),
            }
        )

    items = TaskWorkflowItem.objects.filter(assignment__created_by=user).order_by("-updated_at")[:20]
    for item in items:
        events.append(
            {
                "timestamp": item.updated_at,
                "message": (
                    f"Item #{item.id} moved to {item.current_phase.upper()}:{item.current_compartment} "
                    f"(step {item.current_step_index}) with status {item.status}."
                ),
            }
        )

    events.sort(key=lambda event: event["timestamp"], reverse=True)
    limited = events[:20]
    return [
        {
            "timestamp": event["timestamp"].isoformat(timespec="seconds"),
            "message": event["message"],
        }
        for event in limited
    ]


def _build_operational_metrics_csv(metrics: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["category", "metric", "value"])

    writer.writerow(["summary", "total_assignments", metrics.get("total_assignments", 0)])
    writer.writerow(["summary", "active_assignments", metrics.get("active_assignments", 0)])
    writer.writerow(["summary", "completed_assignments", metrics.get("completed_assignments", 0)])

    operational = metrics.get("operational_metrics", {})
    writer.writerow(["operational", "assignment_throughput_7d", operational.get("assignment_throughput_7d", 0)])
    writer.writerow(["operational", "item_velocity_steps_per_day", operational.get("item_velocity_steps_per_day", 0)])

    phase_latency = operational.get("phase_transition_latency_hours", {})
    writer.writerow(["operational", "create_to_start_hours", phase_latency.get("create_to_start_hours", 0)])
    writer.writerow(["operational", "start_to_complete_hours", phase_latency.get("start_to_complete_hours", 0)])

    for compartment, value in (operational.get("compartment_dwell_time_hours", {}) or {}).items():
        writer.writerow(["compartment_dwell_hours", compartment, value])

    for row in operational.get("per_user_productivity", []) or []:
        writer.writerow(["user_productivity_total", row.get("user", "unknown"), row.get("total", 0)])
        writer.writerow(["user_productivity_completed", row.get("user", "unknown"), row.get("completed", 0)])
        writer.writerow(["user_productivity_completion_rate", row.get("user", "unknown"), row.get("completion_rate", 0)])

    return output.getvalue()


def _build_operational_metrics_pdf(metrics: dict, *, generated_for: str) -> io.BytesIO:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter, pageCompression=0)
    y = 760

    def write_line(text, bold=False):
        nonlocal y
        if y < 60:
            pdf.showPage()
            y = 760
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 11)
        pdf.drawString(50, y, text[:135])
        y -= 16

    write_line("Task Manager Operational Analytics Report", bold=True)
    write_line(f"Generated for: {generated_for}")
    write_line(f"Generated at: {timezone.now().isoformat(timespec='seconds')}")
    write_line("")

    write_line("Summary", bold=True)
    write_line(f"Total Assignments: {metrics.get('total_assignments', 0)}")
    write_line(f"Active Assignments: {metrics.get('active_assignments', 0)}")
    write_line(f"Completed Assignments: {metrics.get('completed_assignments', 0)}")

    operational = metrics.get("operational_metrics", {})
    write_line("")
    write_line("Operational Metrics", bold=True)
    write_line(f"Assignment Throughput (7d): {operational.get('assignment_throughput_7d', 0)}")
    write_line(f"Item Velocity (steps/day): {operational.get('item_velocity_steps_per_day', 0)}")
    phase_latency = operational.get("phase_transition_latency_hours", {})
    write_line(f"Create to Start (hours): {phase_latency.get('create_to_start_hours', 0)}")
    write_line(f"Start to Complete (hours): {phase_latency.get('start_to_complete_hours', 0)}")

    write_line("")
    write_line("Compartment Dwell Time (hours)", bold=True)
    for compartment, value in (operational.get("compartment_dwell_time_hours", {}) or {}).items():
        write_line(f"{compartment}: {value}")

    write_line("")
    write_line("Per-User Productivity", bold=True)
    for row in operational.get("per_user_productivity", []) or []:
        write_line(
            f"{row.get('user', 'unknown')}: {row.get('completed', 0)}/{row.get('total', 0)} completed ({row.get('completion_rate', 0)}%)"
        )

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer


def _record_analytics_export_run(
    *,
    requested_by,
    target_user,
    trigger_source: str,
    export_format: str,
    status: str,
    output_dir: str = "",
    artifact_paths: str = "",
    notes: str = "",
    error_message: str = "",
):
    TaskManagerAnalyticsExportRun.objects.create(
        requested_by=requested_by,
        target_user=target_user,
        trigger_source=trigger_source,
        export_format=export_format,
        status=status,
        output_dir=output_dir,
        artifact_paths=artifact_paths,
        notes=notes,
        error_message=error_message,
        completed_at=timezone.now(),
    )


def _resolve_active_tab(raw_value, default_tab="create"):
    if raw_value in ALLOWED_TASK_MANAGER_TABS:
        return raw_value
    return default_tab


def _redirect_to_task_manager_admin(request, default_tab="create"):
    active_tab = _resolve_active_tab(request.POST.get("active_tab"), default_tab=default_tab)
    return redirect(f"{reverse('task-manager-admin:index')}?active_tab={active_tab}")


def _build_task_manager_context(user, selected_quarantine_id=None, export_status_filter="all"):
    allowed_assignment_types = sorted(allowed_assignment_types_for_user(user))
    assignments = (
        TaskAssignment.objects.filter(created_by=user)
        .prefetch_related("workflow_items", "objectives", "attachments")
        .order_by("-updated_at")[:8]
    )
    assignment_type_labels = dict(ASSIGNMENT_CHOICES)
    objective_content_type = ContentType.objects.get_for_model(TaskObjective)
    storage_used_bytes = (
        user.get_storage_used_bytes()
    )
    storage_quota_bytes = user.get_storage_quota_bytes()
    tier_upload_cap_bytes = user.get_upload_size_cap_bytes()
    assignment_cards = []
    for assignment in assignments:
        objectives = list(assignment.objectives.all().order_by("created_at", "id"))
        attached_objective_ids = set(
            assignment.workflow_items.filter(
                content_type=objective_content_type,
                object_id__in=[objective.id for objective in objectives],
            ).values_list("object_id", flat=True)
        )
        for objective in objectives:
            objective.is_attached_for_assignment = objective.id in attached_objective_ids

        assignment_cards.append(
            {
                "assignment": assignment,
                "step_total": len(build_assignment_sequence(assignment.assignment_type)),
                "items": list(assignment.workflow_items.all().order_by("current_step_index", "id")),
                "objectives": objectives,
                "attachments": list(assignment.attachments.all().order_by("-created_at", "-id")),
                "quarantine_items": list(
                    assignment.quarantined_attachments.filter(uploaded_by=user).order_by("-created_at", "-id")[:6]
                ),
            }
        )

    quarantine_items_qs = _quarantine_queryset_for_user(user)
    quarantine_items = list(quarantine_items_qs.order_by("-created_at", "-id")[:40])

    selected_quarantine_item = None
    if selected_quarantine_id:
        try:
            selected_quarantine_id = int(selected_quarantine_id)
        except (TypeError, ValueError):
            selected_quarantine_id = None

    if selected_quarantine_id:
        for item in quarantine_items:
            if item.id == selected_quarantine_id:
                selected_quarantine_item = item
                break

    quarantine_history = []
    if selected_quarantine_item:
        quarantine_history = list(
            TaskAttachmentAuditLog.objects.filter(
                assignment=selected_quarantine_item.assignment,
                filename=selected_quarantine_item.original_filename,
            )
            .select_related("actor")
            .order_by("-created_at", "-id")[:20]
        )

    export_history_runs = TaskManagerAnalyticsExportRun.objects.select_related("requested_by", "target_user")
    if not user_is_polish_admin(user):
        export_history_runs = export_history_runs.filter(requested_by=user)
    if export_status_filter == TaskManagerAnalyticsExportRun.STATUS_FAILED:
        export_history_runs = export_history_runs.filter(status=TaskManagerAnalyticsExportRun.STATUS_FAILED)
    export_history_runs = list(export_history_runs.order_by("-created_at", "-id")[:12])

    return {
        "allowed_assignment_types": allowed_assignment_types,
        "assignment_type_options": [
            (value, assignment_type_labels.get(value, value)) for value in allowed_assignment_types
        ],
        "task_assignments": assignments,
        "assignment_cards": assignment_cards,
        "task_workflow_items": TaskWorkflowItem.objects.filter(assignment__created_by=user)[:16],
        "metrics": _build_task_manager_metrics(user),
        "clamscan_available": is_clamscan_available(),
        "storage_used_bytes": storage_used_bytes,
        "storage_quota_bytes": storage_quota_bytes,
        "storage_used_label": _format_bytes(storage_used_bytes),
        "storage_quota_label": _format_bytes(storage_quota_bytes),
        "storage_remaining_label": _format_bytes(max(storage_quota_bytes - storage_used_bytes, 0)),
        "tier_upload_cap_label": _format_bytes(tier_upload_cap_bytes),
        "is_staff_user": user_is_polish_admin(user),
        "is_premium_subscriber": user.is_premium_subscriber(),
        "rejected_attachment_count": TaskAttachmentQuarantine.objects.filter(uploaded_by=user).count(),
        "quarantine_items": quarantine_items,
        "selected_quarantine_item": selected_quarantine_item,
        "quarantine_history": quarantine_history,
        "export_history_runs": export_history_runs,
        "export_status_filter": export_status_filter,
    }


class PolishDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "polish/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if user_is_polish_admin(request.user):
            return super().dispatch(request, *args, **kwargs)
        return redirect("center:corporation_admin")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        preference, _ = PolishReminderPreference.objects.get_or_create(user=self.request.user)
        context["task_form"] = kwargs.get("task_form") or PolishTaskForm()
        context["agenda_form"] = kwargs.get("agenda_form") or SectorAgendaForm()
        context["reminder_form"] = kwargs.get("reminder_form") or PolishReminderPreferenceForm(instance=preference)
        context["reminder_enabled"] = preference.enabled
        context["incomplete_tasks"] = PolishTask.objects.filter(
            user=self.request.user,
            is_completed=False,
        )
        context["completed_tasks"] = PolishTask.objects.filter(
            user=self.request.user,
            is_completed=True,
        )[:8]
        context["recent_agendas"] = SectorAgenda.objects.filter(user=self.request.user)[:8]
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "add_task":
            task_form = PolishTaskForm(request.POST)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.user = request.user
                task.save()
                return redirect("polish:dashboard")
            return self.render_to_response(self.get_context_data(task_form=task_form))

        if action == "complete_task":
            task = get_object_or_404(PolishTask, pk=request.POST.get("task_id"), user=request.user)
            task.is_completed = True
            task.save(update_fields=["is_completed", "updated_at"])
            return redirect("polish:dashboard")

        if action == "create_agenda":
            agenda_form = SectorAgendaForm(request.POST)
            if agenda_form.is_valid():
                agenda = agenda_form.save(commit=False)
                agenda.user = request.user
                agenda.agenda_text = _build_agenda_text(
                    agenda.sector_name,
                    agenda.idea,
                    agenda.objective,
                )
                agenda.save()
                return redirect("polish:dashboard")
            return self.render_to_response(self.get_context_data(agenda_form=agenda_form))

        if action == "update_reminder_preference":
            preference, _ = PolishReminderPreference.objects.get_or_create(user=request.user)
            reminder_form = PolishReminderPreferenceForm(request.POST, instance=preference)
            if reminder_form.is_valid():
                reminder_form.save()
                return redirect("polish:dashboard")
            return self.render_to_response(self.get_context_data(reminder_form=reminder_form))

        return redirect("polish:dashboard")


class TaskManagerAdminView(LoginRequiredMixin, PolishAdminRequiredMixin, TemplateView):
    template_name = "polish/task_manager_admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        export_status_filter = (self.request.GET.get("export_status") or "all").strip().lower()
        if export_status_filter not in {"all", TaskManagerAnalyticsExportRun.STATUS_FAILED}:
            export_status_filter = "all"
        context.update(
            _build_task_manager_context(
                self.request.user,
                selected_quarantine_id=self.request.GET.get("quarantine_id"),
                export_status_filter=export_status_filter,
            )
        )
        context["title"] = "Task Manager Admin"
        context["active_tab"] = _resolve_active_tab(self.request.GET.get("active_tab"), default_tab="create")
        return context


class TaskManagerQuarantineListView(LoginRequiredMixin, PolishAdminRequiredMixin, TemplateView):
    template_name = "polish/task_manager_quarantine.html"
    paginate_by = 20

    SORT_OPTIONS = {
        "newest": ("-created_at", "-id"),
        "oldest": ("created_at", "id"),
        "name_az": ("original_filename", "id"),
        "name_za": ("-original_filename", "-id"),
        "size_high": ("-file_size_bytes", "-id"),
        "size_low": ("file_size_bytes", "id"),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = _quarantine_queryset_for_user(self.request.user)

        scan_status = (self.request.GET.get("scan_status") or "").strip()
        review_status = (self.request.GET.get("review_status") or "").strip()
        search_query = (self.request.GET.get("q") or "").strip()
        sort = (self.request.GET.get("sort") or "newest").strip()
        if sort not in self.SORT_OPTIONS:
            sort = "newest"

        active_params = {}
        if search_query:
            active_params["q"] = search_query
        if scan_status:
            active_params["scan_status"] = scan_status
        if review_status:
            active_params["review_status"] = review_status
        if sort and sort != "newest":
            active_params["sort"] = sort

        def build_filter_url(**overrides):
            merged = dict(active_params)
            for key, value in overrides.items():
                if value in (None, ""):
                    merged.pop(key, None)
                else:
                    merged[key] = value
            if not merged:
                return reverse("polish:task-manager:quarantine-list")
            return f"{reverse('polish:task-manager:quarantine-list')}?{urlencode(merged)}"

        if scan_status:
            queryset = queryset.filter(scan_status=scan_status)
        if review_status:
            queryset = queryset.filter(review_status=review_status)
        if search_query:
            queryset = queryset.filter(
                Q(original_filename__icontains=search_query)
                | Q(reason__icontains=search_query)
                | Q(assignment__title__icontains=search_query)
                | Q(uploaded_by__username__icontains=search_query)
                | Q(uploaded_by__email__icontains=search_query)
            )

        paginator = Paginator(queryset.order_by(*self.SORT_OPTIONS[sort]), self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page") or 1)

        selected_quarantine_id = self.kwargs.get("quarantine_id") or self.request.GET.get("quarantine_id")
        selected_quarantine_item = None
        if selected_quarantine_id:
            try:
                selected_quarantine_item = _quarantine_queryset_for_user(self.request.user).filter(
                    pk=int(selected_quarantine_id)
                ).first()
            except (TypeError, ValueError):
                selected_quarantine_item = None

        quarantine_history = []
        if selected_quarantine_item:
            quarantine_history = list(
                TaskAttachmentAuditLog.objects.filter(
                    assignment=selected_quarantine_item.assignment,
                    filename=selected_quarantine_item.original_filename,
                )
                .select_related("actor")
                .order_by("-created_at", "-id")[:40]
            )

        active_filter_chips = []
        if search_query:
            active_filter_chips.append({"label": f"Search: {search_query}", "remove_url": build_filter_url(q=None)})
        if scan_status:
            active_filter_chips.append({"label": f"Scan: {scan_status}", "remove_url": build_filter_url(scan_status=None)})
        if review_status:
            active_filter_chips.append({"label": f"Review: {review_status}", "remove_url": build_filter_url(review_status=None)})
        if sort and sort != "newest":
            active_filter_chips.append({"label": f"Sort: {sort}", "remove_url": build_filter_url(sort=None)})

        context.update(
            {
                "page_obj": page_obj,
                "quarantine_items": list(page_obj.object_list),
                "selected_quarantine_item": selected_quarantine_item,
                "quarantine_history": quarantine_history,
                "scan_status": scan_status,
                "review_status": review_status,
                "search_query": search_query,
                "sort": sort,
                "scan_status_choices": TaskAssignmentAttachment.SCAN_STATUS_CHOICES,
                "review_status_choices": TaskAttachmentQuarantine.REVIEW_STATUS_CHOICES,
                "sort_choices": [
                    ("newest", "Newest First"),
                    ("oldest", "Oldest First"),
                    ("name_az", "Filename A-Z"),
                    ("name_za", "Filename Z-A"),
                    ("size_high", "Size High-Low"),
                    ("size_low", "Size Low-High"),
                ],
                "active_filter_chips": active_filter_chips,
                "clear_filters_url": reverse("polish:task-manager:quarantine-list"),
                "is_staff_user": user_is_polish_admin(self.request.user),
                "current_full_path": self.request.get_full_path(),
            }
        )
        return context


@require_GET
@login_required
def task_manager_metrics_api(request):
    if not user_is_polish_admin(request.user):
        return JsonResponse({"detail": "Polish admin access required."}, status=403)
    return JsonResponse(_build_task_manager_metrics(request.user))


@require_GET
@login_required
def task_manager_activity_api(request):
    if not user_is_polish_admin(request.user):
        return JsonResponse({"detail": "Polish admin access required."}, status=403)
    return JsonResponse({"events": _build_task_manager_activity(request.user)})


class TaskManagerAssignmentCreateView(LoginRequiredMixin, PolishAdminRequiredMixin, View):
    def post(self, request):
        assignment_type = request.POST.get("assignment_type") or ASSIGNMENT_LINEAR
        title = request.POST.get("title") or "Task Manager Assignment"
        try:
            create_assignment(
                created_by=request.user,
                assignment_type=assignment_type,
                title=title,
                assigned_to=request.user,
            )
            messages.success(request, "Task assignment created.")
        except PermissionDenied:
            if assignment_type == "perpetual":
                messages.error(request, "Perpetual assignments require a premium subscription. Upgrade at /users/subscription/upgrade/.")
            else:
                messages.error(request, "You do not have permission to create this assignment type.")
        return _redirect_to_task_manager_admin(request, default_tab="create")


class TaskManagerAttachItemView(LoginRequiredMixin, PolishAdminRequiredMixin, View):
    def post(self, request, assignment_id):
        assignment = get_object_or_404(TaskAssignment, pk=assignment_id)
        if not _assignment_accessible_to_user(assignment, request.user):
            messages.error(request, "You cannot attach items to this assignment.")
            return _redirect_to_task_manager_admin(request, default_tab="attach")

        action = (request.POST.get("action") or "").strip()
        if action == "remove_attachment":
            attachment_id = request.POST.get("attachment_id")
            attachment = get_object_or_404(TaskAssignmentAttachment, pk=attachment_id, assignment=assignment)
            _record_attachment_audit(
                assignment=assignment,
                actor=request.user,
                event_type=TaskAttachmentAuditLog.EVENT_REMOVED,
                filename=Path(attachment.file.name).name if attachment.file else "",
                content_type="",
                file_size_bytes=attachment.file_size_bytes,
                reason="Attachment removed by user action.",
            )
            if attachment.file:
                attachment.file.delete(save=False)
            attachment.delete()
            messages.success(request, "Attachment removed.")
            return _redirect_to_task_manager_admin(request, default_tab="attach")

        attachment_file = request.FILES.get("attachment_file")
        if attachment_file:
            label = (request.POST.get("attachment_label") or "").strip()
            extension = Path(attachment_file.name).suffix.lower()
            content_type = (attachment_file.content_type or "").strip().lower()
            inferred_mime = mimetypes.guess_type(attachment_file.name)[0]
            admin_override = user_is_polish_admin(request.user) and request.POST.get("admin_override") == "1"

            if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
                reason = "Blocked upload: extension not allowed."
                _quarantine_upload(
                    assignment=assignment,
                    actor=request.user,
                    uploaded_file=attachment_file,
                    label=label,
                    reason=reason,
                )
                _record_attachment_audit(
                    assignment=assignment,
                    actor=request.user,
                    event_type=TaskAttachmentAuditLog.EVENT_BLOCKED,
                    filename=attachment_file.name,
                    content_type=content_type,
                    file_size_bytes=attachment_file.size,
                    reason=reason,
                    metadata={"extension": extension},
                )
                messages.error(
                    request,
                    "Unsupported file type. Allowed: PDF, DOC, DOCX, TXT, MD, XLSX, CSV, PNG, JPG, JPEG.",
                )
                return _redirect_to_task_manager_admin(request, default_tab="attach")

            if content_type and content_type not in ALLOWED_MIME_TYPES:
                reason = "Blocked upload: MIME type not allowed."
                _quarantine_upload(
                    assignment=assignment,
                    actor=request.user,
                    uploaded_file=attachment_file,
                    label=label,
                    reason=reason,
                )
                _record_attachment_audit(
                    assignment=assignment,
                    actor=request.user,
                    event_type=TaskAttachmentAuditLog.EVENT_BLOCKED,
                    filename=attachment_file.name,
                    content_type=content_type,
                    file_size_bytes=attachment_file.size,
                    reason=reason,
                    metadata={"inferred_mime": inferred_mime or ""},
                )
                messages.error(request, "Unsupported MIME type for attachment upload.")
                return _redirect_to_task_manager_admin(request, default_tab="attach")

            tier_upload_cap = request.user.get_upload_size_cap_bytes()
            if attachment_file.size > tier_upload_cap and not admin_override:
                reason = "Blocked upload: tier size cap exceeded."
                _quarantine_upload(
                    assignment=assignment,
                    actor=request.user,
                    uploaded_file=attachment_file,
                    label=label,
                    reason=reason,
                )
                _record_attachment_audit(
                    assignment=assignment,
                    actor=request.user,
                    event_type=TaskAttachmentAuditLog.EVENT_BLOCKED,
                    filename=attachment_file.name,
                    content_type=content_type,
                    file_size_bytes=attachment_file.size,
                    reason=reason,
                    metadata={"tier_cap_bytes": tier_upload_cap},
                )
                messages.error(request, f"File exceeds your tier upload cap ({_format_bytes(tier_upload_cap)}).")
                return _redirect_to_task_manager_admin(request, default_tab="attach")

            current_usage = request.user.get_storage_used_bytes()
            user_quota = request.user.get_storage_quota_bytes()
            projected_usage = current_usage + attachment_file.size
            if projected_usage > user_quota and not admin_override:
                reason = "Blocked upload: user storage quota exceeded."
                _quarantine_upload(
                    assignment=assignment,
                    actor=request.user,
                    uploaded_file=attachment_file,
                    label=label,
                    reason=reason,
                )
                _record_attachment_audit(
                    assignment=assignment,
                    actor=request.user,
                    event_type=TaskAttachmentAuditLog.EVENT_BLOCKED,
                    filename=attachment_file.name,
                    content_type=content_type,
                    file_size_bytes=attachment_file.size,
                    reason=reason,
                    metadata={"projected_usage": projected_usage, "quota": user_quota},
                )
                messages.error(
                    request,
                    "Storage limit reached for your subscription tier. Upgrade at /users/subscription/upgrade/.",
                )
                return _redirect_to_task_manager_admin(request, default_tab="attach")

            scan_result = scan_uploaded_attachment(attachment_file)
            if not scan_result.is_clean:
                reason = f"Blocked upload by security scan: {scan_result.notes}"
                _quarantine_upload(
                    assignment=assignment,
                    actor=request.user,
                    uploaded_file=attachment_file,
                    label=label,
                    reason=reason,
                    scan_status=scan_result.status,
                )
                _record_attachment_audit(
                    assignment=assignment,
                    actor=request.user,
                    event_type=TaskAttachmentAuditLog.EVENT_BLOCKED,
                    filename=attachment_file.name,
                    content_type=content_type,
                    file_size_bytes=attachment_file.size,
                    reason=reason,
                    metadata={"scan_status": scan_result.status, "sha256": scan_result.sha256},
                )
                messages.error(request, f"Attachment blocked by security scan: {scan_result.notes}")
                return _redirect_to_task_manager_admin(request, default_tab="attach")

            TaskAssignmentAttachment.objects.create(
                assignment=assignment,
                uploaded_by=request.user,
                label=label,
                file=attachment_file,
                file_size_bytes=attachment_file.size,
                file_sha256=scan_result.sha256,
                scan_status=scan_result.status,
                scan_notes=scan_result.notes,
                scanned_at=timezone.now(),
            )
            _record_attachment_audit(
                assignment=assignment,
                actor=request.user,
                event_type=TaskAttachmentAuditLog.EVENT_ALLOWED,
                filename=attachment_file.name,
                content_type=content_type,
                file_size_bytes=attachment_file.size,
                reason="Attachment uploaded successfully.",
                metadata={"admin_override": admin_override, "sha256": scan_result.sha256},
            )
            messages.success(request, "File attachment uploaded.")
            return _redirect_to_task_manager_admin(request, default_tab="attach")

        objective_text = (request.POST.get("objective_text") or "").strip()
        objective_id = (request.POST.get("objective_id") or "").strip()

        objective = None
        if objective_text:
            objective = TaskObjective.objects.create(
                assignment=assignment,
                objective_text=objective_text,
                created_by=request.user,
            )
        elif objective_id:
            objective = get_object_or_404(TaskObjective, pk=objective_id, assignment=assignment)
        else:
            messages.error(request, "Provide objective text or select an existing objective.")
            return _redirect_to_task_manager_admin(request, default_tab="attach")

        attach_item(assignment=assignment, workflow_object=objective)
        if not objective.is_attached:
            objective.is_attached = True
            objective.save(update_fields=["is_attached", "updated_at"])

        if objective_text:
            messages.success(request, "Objective created and attached to assignment workflow.")
        else:
            messages.success(request, "Existing objective attached to assignment workflow.")
        return _redirect_to_task_manager_admin(request, default_tab="attach")


class TaskManagerAssignmentActionView(LoginRequiredMixin, PolishAdminRequiredMixin, View):
    def post(self, request, assignment_id):
        assignment = get_object_or_404(TaskAssignment, pk=assignment_id)
        if not _assignment_accessible_to_user(assignment, request.user):
            messages.error(request, "You cannot update this assignment.")
            return _redirect_to_task_manager_admin(request, default_tab="assignment")

        action = request.POST.get("action")
        target_item = assignment.workflow_items.exclude(status="completed").order_by("current_step_index", "id").first()
        if target_item is None:
            target_item = assignment.workflow_items.order_by("current_step_index", "id").first()

        if target_item is None:
            messages.error(request, "Attach at least one workflow item first.")
            return _redirect_to_task_manager_admin(request, default_tab="assignment")

        if action == "advance":
            progress = advance_item(item=target_item, steps=1)
            messages.success(
                request,
                f"Assignment advanced to {progress.phase.upper()}:{progress.compartment} (step {progress.step_index}).",
            )
            assignment.is_closed = progress.completed
            if progress.completed:
                assignment.completed_at = timezone.now()
                assignment.save(update_fields=["is_closed", "completed_at", "updated_at"])
            else:
                assignment.save(update_fields=["is_closed", "updated_at"])
            return _redirect_to_task_manager_admin(request, default_tab="assignment")

        if action == "skip":
            step_index = int(request.POST.get("step_index", "0"))
            progress = skip_item_to_step(item=target_item, step_index=step_index)
            messages.success(
                request,
                f"Assignment skipped to {progress.phase.upper()}:{progress.compartment} (step {progress.step_index}).",
            )
            assignment.is_closed = progress.completed
            if progress.completed:
                assignment.completed_at = timezone.now()
                assignment.save(update_fields=["is_closed", "completed_at", "updated_at"])
            else:
                assignment.save(update_fields=["is_closed", "updated_at"])
            return _redirect_to_task_manager_admin(request, default_tab="assignment")

        if action == "complete":
            completion_notes = (request.POST.get("completion_notes") or "").strip()
            for item in assignment.workflow_items.exclude(status="completed"):
                complete_item_early(item=item)
            assignment.is_closed = True
            assignment.completed_at = timezone.now()
            assignment.completion_notes = completion_notes
            assignment.save(update_fields=["is_closed", "completed_at", "completion_notes", "updated_at"])
            messages.success(request, "Assignment marked completed.")
            return _redirect_to_task_manager_admin(request, default_tab="assignment")

        if action == "resume":
            resumed = False
            for item in assignment.workflow_items.filter(status="completed"):
                resume_item(item=item)
                resumed = True
            if resumed:
                assignment.is_closed = False
                assignment.completed_at = None
                assignment.save(update_fields=["is_closed", "completed_at", "updated_at"])
                messages.success(request, "Assignment resumed.")
            else:
                messages.warning(request, "No completed workflow item to resume.")
            return _redirect_to_task_manager_admin(request, default_tab="assignment")

        messages.error(request, "Invalid assignment action.")
        return _redirect_to_task_manager_admin(request, default_tab="assignment")


class TaskManagerItemActionView(LoginRequiredMixin, PolishAdminRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(TaskWorkflowItem, pk=item_id)
        if not _assignment_accessible_to_user(item.assignment, request.user):
            messages.error(request, "You cannot update this workflow item.")
            return _redirect_to_task_manager_admin(request, default_tab="item")

        action = request.POST.get("action")
        if action == "advance":
            steps = int(request.POST.get("steps", "1"))
            progress = advance_item(item=item, steps=steps)
            messages.success(
                request,
                f"Item moved to {progress.phase.upper()}:{progress.compartment} (step {progress.step_index}).",
            )
            return _redirect_to_task_manager_admin(request, default_tab="item")
        if action == "skip":
            step_index = int(request.POST.get("step_index", "0"))
            progress = skip_item_to_step(item=item, step_index=step_index)
            messages.success(
                request,
                f"Item skipped to {progress.phase.upper()}:{progress.compartment} (step {progress.step_index}).",
            )
            return _redirect_to_task_manager_admin(request, default_tab="item")
        if action == "complete":
            complete_item_early(item=item)
            messages.success(request, "Item marked completed.")
            return _redirect_to_task_manager_admin(request, default_tab="item")
        if action == "resume":
            resume_item(item=item)
            messages.success(request, "Item resumed.")
            return _redirect_to_task_manager_admin(request, default_tab="item")

        messages.error(request, "Invalid item action.")
        return _redirect_to_task_manager_admin(request, default_tab="item")


class TaskManagerQuarantineActionView(LoginRequiredMixin, PolishAdminRequiredMixin, View):
    def post(self, request, quarantine_id):
        quarantine = get_object_or_404(TaskAttachmentQuarantine, pk=quarantine_id)
        return_to = (request.POST.get("return_to") or "").strip()
        if return_to.startswith("/") and "://" not in return_to:
            safe_return_to = return_to
        else:
            safe_return_to = f"{reverse('task-manager-admin:index')}?active_tab=quarantine&quarantine_id={quarantine.id}"

        if not _quarantine_accessible_to_user(quarantine, request.user):
            messages.error(request, "You cannot manage this quarantined attachment.")
            return redirect(safe_return_to)

        action = (request.POST.get("action") or "").strip().lower()
        review_notes = (request.POST.get("review_notes") or "").strip()
        quarantine_redirect = safe_return_to

        if action in {"approve", "rescan", "delete"} and not user_is_polish_admin(request.user):
            messages.error(request, "Only Polish admins can perform quarantine review actions.")
            return redirect(quarantine_redirect)

        if action == "approve":
            promoted = _promote_quarantine_to_attachment(
                quarantine=quarantine,
                actor=request.user,
                notes=review_notes or "Approved and released by staff reviewer.",
            )
            _record_attachment_audit(
                assignment=quarantine.assignment,
                actor=request.user,
                event_type=TaskAttachmentAuditLog.EVENT_REVIEW_APPROVED,
                filename=quarantine.original_filename,
                content_type=quarantine.content_type,
                file_size_bytes=quarantine.file_size_bytes,
                reason=review_notes or "Staff approved quarantined attachment.",
                metadata={"attachment_id": promoted.id},
            )
            quarantine.review_status = quarantine.REVIEW_APPROVED
            quarantine.review_notes = review_notes or "Approved and released"
            quarantine.reviewed_by = request.user
            quarantine.reviewed_at = timezone.now()
            quarantine.save(update_fields=["review_status", "review_notes", "reviewed_by", "reviewed_at"])
            if quarantine.file:
                quarantine.file.delete(save=False)
            quarantine.delete()
            messages.success(request, "Quarantined attachment approved and released.")
            return redirect(quarantine_redirect)

        if action == "rescan":
            scan_result = scan_uploaded_attachment(quarantine.file)
            quarantine.scan_status = scan_result.status
            quarantine.reason = scan_result.notes
            quarantine.review_status = quarantine.REVIEW_RESCANNED
            quarantine.review_notes = review_notes or "Rescanned by staff reviewer"
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
            _record_attachment_audit(
                assignment=quarantine.assignment,
                actor=request.user,
                event_type=TaskAttachmentAuditLog.EVENT_REVIEW_RESCANNED,
                filename=quarantine.original_filename,
                content_type=quarantine.content_type,
                file_size_bytes=quarantine.file_size_bytes,
                reason=review_notes or f"Rescan result: {scan_result.status}",
                metadata={"scan_notes": scan_result.notes, "sha256": scan_result.sha256},
            )
            messages.success(request, f"Quarantine item rescanned ({scan_result.status}).")
            return redirect(quarantine_redirect)

        if action == "delete":
            _record_attachment_audit(
                assignment=quarantine.assignment,
                actor=request.user,
                event_type=TaskAttachmentAuditLog.EVENT_REVIEW_DELETED,
                filename=quarantine.original_filename,
                content_type=quarantine.content_type,
                file_size_bytes=quarantine.file_size_bytes,
                reason=review_notes or "Staff deleted quarantined attachment.",
            )
            quarantine.review_status = quarantine.REVIEW_DELETED
            quarantine.review_notes = review_notes or "Deleted by staff reviewer"
            quarantine.reviewed_by = request.user
            quarantine.reviewed_at = timezone.now()
            quarantine.save(update_fields=["review_status", "review_notes", "reviewed_by", "reviewed_at"])
            if quarantine.file:
                quarantine.file.delete(save=False)
            quarantine.delete()
            messages.success(request, "Quarantined attachment deleted.")
            return redirect(quarantine_redirect)

        messages.error(request, "Invalid quarantine action.")
        return redirect(quarantine_redirect)


class TaskManagerAnalyticsCsvExportView(LoginRequiredMixin, PolishAdminRequiredMixin, View):
    def get(self, request):
        if not user_is_polish_admin(request.user):
            messages.error(request, "Only Polish admins can export analytics reports.")
            return _redirect_to_task_manager_admin(request, default_tab="ops-metrics")

        filename = f"task_manager_operational_metrics_{timezone.now().date().isoformat()}.csv"
        try:
            metrics = _build_task_manager_metrics(request.user)
            csv_content = _build_operational_metrics_csv(metrics)
            _record_analytics_export_run(
                requested_by=request.user,
                target_user=request.user,
                trigger_source=TaskManagerAnalyticsExportRun.SOURCE_UI,
                export_format=TaskManagerAnalyticsExportRun.FORMAT_CSV,
                status=TaskManagerAnalyticsExportRun.STATUS_SUCCESS,
                output_dir="http-download",
                artifact_paths=filename,
                notes="On-demand CSV export from Task Manager UI.",
            )
            response = HttpResponse(csv_content, content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except Exception as exc:
            _record_analytics_export_run(
                requested_by=request.user,
                target_user=request.user,
                trigger_source=TaskManagerAnalyticsExportRun.SOURCE_UI,
                export_format=TaskManagerAnalyticsExportRun.FORMAT_CSV,
                status=TaskManagerAnalyticsExportRun.STATUS_FAILED,
                output_dir="http-download",
                artifact_paths=filename,
                notes="On-demand CSV export failed from Task Manager UI.",
                error_message=str(exc),
            )
            messages.error(request, "CSV export failed. Check Export History for details.")
            return _redirect_to_task_manager_admin(request, default_tab="ops-metrics")


class TaskManagerAnalyticsPdfExportView(LoginRequiredMixin, PolishAdminRequiredMixin, View):
    def get(self, request):
        if not user_is_polish_admin(request.user):
            messages.error(request, "Only Polish admins can export analytics reports.")
            return _redirect_to_task_manager_admin(request, default_tab="ops-metrics")

        filename = f"task_manager_operational_metrics_{timezone.now().date().isoformat()}.pdf"
        try:
            metrics = _build_task_manager_metrics(request.user)
            username = request.user.username or request.user.email or "staff-user"
            buffer = _build_operational_metrics_pdf(metrics, generated_for=username)
            _record_analytics_export_run(
                requested_by=request.user,
                target_user=request.user,
                trigger_source=TaskManagerAnalyticsExportRun.SOURCE_UI,
                export_format=TaskManagerAnalyticsExportRun.FORMAT_PDF,
                status=TaskManagerAnalyticsExportRun.STATUS_SUCCESS,
                output_dir="http-download",
                artifact_paths=filename,
                notes="On-demand PDF export from Task Manager UI.",
            )
            return FileResponse(buffer, as_attachment=True, filename=filename)
        except Exception as exc:
            _record_analytics_export_run(
                requested_by=request.user,
                target_user=request.user,
                trigger_source=TaskManagerAnalyticsExportRun.SOURCE_UI,
                export_format=TaskManagerAnalyticsExportRun.FORMAT_PDF,
                status=TaskManagerAnalyticsExportRun.STATUS_FAILED,
                output_dir="http-download",
                artifact_paths=filename,
                notes="On-demand PDF export failed from Task Manager UI.",
                error_message=str(exc),
            )
            messages.error(request, "PDF export failed. Check Export History for details.")
            return _redirect_to_task_manager_admin(request, default_tab="ops-metrics")


class TaskManagerAttachmentDownloadView(LoginRequiredMixin, PolishAdminRequiredMixin, View):
    def get(self, request, attachment_id):
        attachment = get_object_or_404(TaskAssignmentAttachment, pk=attachment_id)
        if attachment.scan_status != TaskAssignmentAttachment.SCAN_CLEAN:
            messages.error(request, "Attachment is not available because it is not marked clean.")
            return _redirect_to_task_manager_admin(request, default_tab="attach")

        if not user_can_download_attachment(request.user, attachment.assignment, attachment):
            messages.error(request, "You cannot access this attachment.")
            return _redirect_to_task_manager_admin(request, default_tab="attach")

        attachment.download_count += 1
        attachment.save(update_fields=["download_count"])

        file_handle = attachment.file.open("rb")
        filename = Path(attachment.file.name).name
        return FileResponse(file_handle, as_attachment=False, filename=filename)


class TaskManagerAssignmentReportView(LoginRequiredMixin, PolishAdminRequiredMixin, View):
    def get(self, request, assignment_id):
        assignment = get_object_or_404(TaskAssignment, pk=assignment_id)
        if not _assignment_accessible_to_user(assignment, request.user):
            messages.error(request, "You cannot access this assignment report.")
            return _redirect_to_task_manager_admin(request, default_tab="assignment")

        document_title = ASSIGNMENT_DOCUMENT_TITLES.get(assignment.assignment_type, "Assignment Document")
        current_objective = _current_objective_text_for_assignment(assignment)
        state_label = (
            f"Phase {assignment.current_phase.upper()} | "
            f"Compartment {assignment.current_compartment} | "
            f"Step {assignment.current_step_index} | "
            f"Status {'completed' if assignment.is_closed else 'active'}"
        )

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter, pageCompression=0)
        y = 760

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, document_title)
        y -= 30

        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, f"Assignment title: {assignment.title}")
        y -= 20
        pdf.drawString(50, y, f"Current state: {state_label}")
        y -= 20
        pdf.drawString(50, y, "Current objective:")
        y -= 16

        for line in (current_objective or "No objective attached").splitlines() or ["No objective attached"]:
            pdf.drawString(65, y, line[:120])
            y -= 16

        if assignment.is_closed:
            y -= 8
            completed_label = assignment.completed_at.isoformat(timespec="seconds") if assignment.completed_at else "N/A"
            pdf.drawString(50, y, f"Completion date: {completed_label}")
            y -= 20
            pdf.drawString(50, y, "Completion notes:")
            y -= 16
            notes = assignment.completion_notes or "No notes provided."
            for line in notes.splitlines() or [notes]:
                pdf.drawString(65, y, line[:120])
                y -= 16

        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        filename = f"{document_title.replace(' ', '_')}.pdf"
        return FileResponse(buffer, as_attachment=True, filename=filename)