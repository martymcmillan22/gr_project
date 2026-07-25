from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from peringram.models import Recycle3Profile
from peringram.pip_state import PIPState, PIPWorkflowService
from peringram.srl import SRLService

from .forms import CorporationItemForm
from .models import CorporationItem
from polish.forms import PolishReminderPreferenceForm, PolishTaskForm
from polish.models import PolishReminderPreference, PolishTask


CENTER_CELLS = {
    "bos": {
        "label": "BOS",
        "color": "#d72638",
        "color_tint": "#f8d7db",
        "color_name": "Red",
        "subject": "Math",
        "time": "1 am",
        "srl": "4",
    },
    "bol": {
        "label": "BOL",
        "color": "#1f6feb",
        "color_tint": "#d6e6ff",
        "color_name": "Blue",
        "subject": "Language",
        "time": "2 am",
        "srl": "16",
    },
    "boe": {
        "label": "BOE",
        "color": "#f2c94c",
        "color_tint": "#fff3cd",
        "color_name": "Yellow",
        "subject": "Arts",
        "time": "3 am",
        "srl": "64",
    },
    "bop": {
        "label": "BOP",
        "color": "#2e7d32",
        "color_tint": "#d7f2d8",
        "color_name": "Green",
        "subject": "Science",
        "time": "4 am",
        "srl": "256",
    },
    "library": {
        "label": "Library",
        "color": "#7a3db8",
        "color_tint": "#eadbfa",
        "color_name": "Purple",
        "subject": "General Information",
        "time": "5 am",
        "srl": "1024",
    },
    "duseum": {
        "label": "Duseum",
        "color": "#0f766e",
        "color_tint": "#d5f6f2",
        "color_name": "Teal",
        "subject": "Literature",
        "time": "6 am",
        "srl": "4096",
    },
    "nuseum": {
        "label": "Nuseum",
        "color": "#f97316",
        "color_tint": "#ffe4d1",
        "color_name": "Orange",
        "subject": "Crafts",
        "time": "7 am",
        "srl": "16384",
    },
    "monuments": {
        "label": "Monuments",
        "color": "#84cc16",
        "color_tint": "#effccb",
        "color_name": "Lime",
        "subject": "Technology",
        "time": "8 am",
        "srl": "65,536",
    },
    "grassroots": {
        "label": "GrassRoots",
        "color": "#ec4899",
        "color_tint": "#ffd8eb",
        "color_name": "Pink",
        "subject": "History",
        "time": "9 am",
        "srl": "262,144",
    },
    "pjs": {
        "label": "Pj's",
        "color": "#06b6d4",
        "color_tint": "#d8f8ff",
        "color_name": "Cyan",
        "subject": "Geology",
        "time": "10 am",
        "srl": "1,048,576",
    },
    "agendatime": {
        "label": "AgendaTime",
        "color": "#f59e0b",
        "color_tint": "#fff0cf",
        "color_name": "Amber",
        "subject": "N/A",
        "time": "11 am",
        "srl": "4,194,304",
    },
    "harvestcrops": {
        "label": "HarvestCrops",
        "color": "#65a30d",
        "color_tint": "#ecfbc9",
        "color_name": "Green-Lime",
        "subject": "N/A",
        "time": "12 pm",
        "srl": "16,777,216",
    },
}

CENTER_CELL_ALIASES = {
    "bridge": {**CENTER_CELLS["bol"], "label": "Bridge"},
    "openfields": {**CENTER_CELLS["boe"], "label": "OpenFields"},
    "seedlings": {**CENTER_CELLS["bop"], "label": "Seedlings"},
    "roots": {**CENTER_CELLS["library"], "label": "Roots"},
    "growth": {**CENTER_CELLS["duseum"], "label": "Growth"},
    "sunrise": {**CENTER_CELLS["nuseum"], "label": "Sunrise"},
    "pathways": {**CENTER_CELLS["monuments"], "label": "Pathways"},
    "community": {**CENTER_CELLS["grassroots"], "label": "Community"},
    "exchange": {**CENTER_CELLS["pjs"], "label": "Exchange"},
    "harvestprep": {**CENTER_CELLS["agendatime"], "label": "HarvestPrep"},
}

CENTER_CELLS.update(CENTER_CELL_ALIASES)


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "center/index.html"


class CellDetailView(LoginRequiredMixin, TemplateView):
    template_name = "center/cell_detail.html"

    def get(self, request, *args, **kwargs):
        slug = kwargs.get("slug", "").lower()
        if slug in ("bos", "bol", "boe", "bop"):
            recycle, _ = Recycle3Profile.objects.get_or_create(user=request.user)
            territory = SRLService.assign_compartment(request.user)
            pip_state = PIPState.from_recycle3(recycle, territory=territory)
            if not PIPWorkflowService.can_access_bureau(slug, pip_state):
                return redirect("center:insufficient_tier")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug", "").lower()
        cell = CENTER_CELLS.get(slug)
        if not cell:
            raise Http404("Center cell not found")
        context["cell"] = cell
        return context


class InsufficientTierView(LoginRequiredMixin, TemplateView):
    template_name = "center/insufficient_tier.html"


class CorporationAdminView(LoginRequiredMixin, TemplateView):
    template_name = "center/corporation_admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reminder_preference, _ = PolishReminderPreference.objects.get_or_create(user=self.request.user)
        context["create_form"] = kwargs.get("create_form") or CorporationItemForm()
        context["polish_task_form"] = kwargs.get("polish_task_form") or PolishTaskForm()
        context["polish_reminder_form"] = (
            kwargs.get("polish_reminder_form") or PolishReminderPreferenceForm(instance=reminder_preference)
        )
        context["polish_reminder_enabled"] = reminder_preference.enabled
        context["polish_incomplete_tasks"] = PolishTask.objects.filter(
            user=self.request.user,
            is_completed=False,
        )
        context["polish_completed_tasks"] = PolishTask.objects.filter(
            user=self.request.user,
            is_completed=True,
        )[:8]
        context["items"] = CorporationItem.objects.filter(owner=self.request.user)
        context["status_draft"] = CorporationItem.STATUS_DRAFT
        context["status_review"] = CorporationItem.STATUS_REVIEW
        context["status_approved"] = CorporationItem.STATUS_APPROVED
        context["status_posted"] = CorporationItem.STATUS_POSTED
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "add_polish_task":
            task_form = PolishTaskForm(request.POST)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.user = request.user
                task.save()
                return redirect("center:corporation_admin")
            return self.render_to_response(self.get_context_data(polish_task_form=task_form))

        if action == "complete_polish_task":
            task = get_object_or_404(PolishTask, pk=request.POST.get("task_id"), user=request.user)
            task.is_completed = True
            task.save(update_fields=["is_completed", "updated_at"])
            return redirect("center:corporation_admin")

        if action == "update_polish_reminder_preference":
            preference, _ = PolishReminderPreference.objects.get_or_create(user=request.user)
            reminder_form = PolishReminderPreferenceForm(request.POST, instance=preference)
            if reminder_form.is_valid():
                reminder_form.save()
                return redirect("center:corporation_admin")
            return self.render_to_response(self.get_context_data(polish_reminder_form=reminder_form))

        if action == "create":
            form = CorporationItemForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.owner = request.user
                item.save()
                return redirect("center:corporation_admin")
            return self.render_to_response(self.get_context_data(create_form=form))

        if action == "transition":
            item_id = request.POST.get("item_id")
            next_status = request.POST.get("next_status")
            item = get_object_or_404(CorporationItem, pk=item_id, owner=request.user)

            if item.can_transition_to(next_status):
                item.status = next_status
                if next_status == CorporationItem.STATUS_APPROVED:
                    item.approved_at = timezone.now()
                item.save(update_fields=["status", "approved_at", "updated_at"])

        return redirect("center:corporation_admin")


class MuseumSocialView(LoginRequiredMixin, TemplateView):
    template_name = "center/museum_social.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ready_to_post_items"] = CorporationItem.objects.filter(
            owner=self.request.user,
            status=CorporationItem.STATUS_APPROVED,
        )
        context["posted_items"] = CorporationItem.objects.filter(
            owner=self.request.user,
            status=CorporationItem.STATUS_POSTED,
        )
        return context

    def post(self, request, *args, **kwargs):
        item_id = request.POST.get("item_id")
        item = get_object_or_404(
            CorporationItem,
            pk=item_id,
            owner=request.user,
            status=CorporationItem.STATUS_APPROVED,
        )
        item.status = CorporationItem.STATUS_POSTED
        item.work_status = CorporationItem.WORK_STATUS_TODO
        item.save(update_fields=["status", "work_status", "updated_at"])
        return redirect("center:museum_social")


class GardenBoardView(LoginRequiredMixin, TemplateView):
    template_name = "center/garden_board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posted_items = CorporationItem.objects.filter(
            owner=self.request.user,
            status=CorporationItem.STATUS_POSTED,
        )

        context["todo_items"] = posted_items.filter(
            Q(work_status=CorporationItem.WORK_STATUS_TODO) | Q(work_status__isnull=True)
        )
        context["in_progress_items"] = posted_items.filter(
            work_status=CorporationItem.WORK_STATUS_IN_PROGRESS
        )
        context["done_items"] = posted_items.filter(work_status=CorporationItem.WORK_STATUS_DONE)
        context["work_todo"] = CorporationItem.WORK_STATUS_TODO
        context["work_in_progress"] = CorporationItem.WORK_STATUS_IN_PROGRESS
        context["work_done"] = CorporationItem.WORK_STATUS_DONE
        return context

    def post(self, request, *args, **kwargs):
        item_id = request.POST.get("item_id")
        next_work_status = request.POST.get("next_work_status")
        item = get_object_or_404(
            CorporationItem,
            pk=item_id,
            owner=request.user,
            status=CorporationItem.STATUS_POSTED,
        )

        if item.can_transition_work_to(next_work_status):
            item.work_status = next_work_status
            update_fields = ["work_status", "updated_at"]
            if next_work_status == CorporationItem.WORK_STATUS_IN_PROGRESS and not item.work_started_at:
                item.work_started_at = timezone.now()
                update_fields.append("work_started_at")
            if next_work_status == CorporationItem.WORK_STATUS_DONE:
                item.work_completed_at = timezone.now()
                update_fields.append("work_completed_at")
            item.save(update_fields=update_fields)

        return redirect("center:garden_board")
