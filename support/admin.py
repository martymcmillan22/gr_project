from urllib.parse import urlencode

from django.contrib import admin
from django.db.models import F
from django.urls import reverse
from django.utils.html import format_html

from .models import FAQ, Feedback
from .services import (
    apply_priority_adjustments,
    faq_draft_for_pattern,
    faq_effectiveness_score,
    get_priority_adjustments_needed,
    high_importance_patterns,
    negative_pattern_clusters,
)


class LowEffectivenessFilter(admin.SimpleListFilter):
    """Filter for FAQs where negative_hits >= positive_hits."""

    title = "Effectiveness"
    parameter_name = "low_effectiveness"

    def lookups(self, request, model_admin):
        return [
            ("needs_improvement", "Needs improvement (negative ≥ positive)"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "needs_improvement":
            return queryset.filter(negative_hits__gte=F("positive_hits"))
        return queryset


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "pattern_tag", "priority", "effectiveness_badge", "hit_counts", "order", "is_active")
    list_editable = ("pattern_tag", "priority", "order", "is_active")
    list_filter = ("pattern_tag", "priority", "is_active", LowEffectivenessFilter)
    search_fields = ("question", "answer")
    readonly_fields = ("positive_hits", "negative_hits")
    ordering = ("-priority", "order")
    actions = ["auto_adjust_priorities"]

    def auto_adjust_priorities(self, request, queryset):
        """
        Admin action: Auto-adjust FAQ priorities based on effectiveness.

        Analyzes all active FAQs and:
        - Bumps priority if effectiveness >= 80%
        - Lowers priority if effectiveness <= 30%
        - Only adjusts if 5+ total hits (sufficient data)

        Requires staffstatus (already enforced by Django admin).
        """
        result = apply_priority_adjustments()

        if result["total"] == 0:
            self.message_user(
                request,
                "No FAQs met the adjustment criteria (need 80%+ or 30%- effectiveness with 5+ hits).",
                level="info",
            )
        else:
            msg = (
                f"Auto-adjusted {result['total']} FAQ priorities: "
                f"{result['bumped']} bumped up, {result['lowered']} lowered. "
                f"See change list for new rankings."
            )
            self.message_user(request, msg, level="success")

    auto_adjust_priorities.short_description = (
        "Auto-adjust priorities based on effectiveness (80%+ bump, 30%- lower)"
    )

    def effectiveness_badge(self, obj):
        """Visual indicator of FAQ effectiveness."""
        if obj.positive_hits == 0 and obj.negative_hits == 0:
            return "—"
        total = obj.positive_hits + obj.negative_hits
        ratio = obj.positive_hits / total
        if ratio >= 0.8:
            return format_html('<span class="tag is-success is-light">✓ Good</span>')
        elif ratio >= 0.5:
            return format_html('<span class="tag is-info is-light">→ Fair</span>')
        else:
            return format_html('<span class="tag is-warning is-light">⚠ Needs improvement</span>')
    effectiveness_badge.short_description = "Effectiveness"

    def hit_counts(self, obj):
        """Display positive and negative hit counts."""
        return format_html(
            '<strong style="color:green;">↑{}</strong> / <strong style="color:red;">↓{}</strong>',
            obj.positive_hits,
            obj.negative_hits,
        )
    hit_counts.short_description = "Hits"

    def get_changeform_initial_data(self, request):
        """
        Pre-fill the FAQ add form when called with GET params.

        Supported params:
            ?pattern_tag=billing
            ?question=...      (optional override)
            ?answer=...        (optional override)

        The admin user can edit everything before saving.
        """
        initial = super().get_changeform_initial_data(request)
        pattern_tag = request.GET.get("pattern_tag", "").strip()
        if pattern_tag:
            draft_q, draft_a = faq_draft_for_pattern(pattern_tag)
            initial.setdefault("pattern_tag", pattern_tag)
            initial.setdefault("question", request.GET.get("question", draft_q))
            initial.setdefault("answer", request.GET.get("answer", draft_a))
        return initial


class HighFrequencyFilter(admin.SimpleListFilter):
    """Surfaces pattern tags that appear 3+ times in negative feedback."""
    title = "High-frequency patterns"
    parameter_name = "high_frequency"

    def lookups(self, request, model_admin):
        return [
            (p["pattern_tag"], f'{p["label"]} ({p["count"]})')
            for p in high_importance_patterns()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(pattern_tag=self.value())
        return queryset


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("sentiment", "pattern_tag", "user", "short_text", "create_faq_link", "page_url", "created_at")
    list_filter = ("sentiment", "pattern_tag", HighFrequencyFilter, "created_at")
    list_editable = ("pattern_tag",)
    search_fields = ("text", "user__username", "page_url")
    readonly_fields = ("sentiment", "text", "user", "page_url", "created_at")
    ordering = ("-created_at",)

    def short_text(self, obj):
        return obj.text[:80] + "…" if len(obj.text) > 80 else obj.text
    short_text.short_description = "Text"

    def create_faq_link(self, obj):
        """
        Renders a one-click "Add FAQ" link for negative feedback that has a
        pattern_tag assigned.  The link pre-fills the FAQ add form via GET params.
        """
        if obj.sentiment != Feedback.NEGATIVE or not obj.pattern_tag:
            return "—"
        add_url = reverse("admin:support_faq_add")
        params = urlencode({"pattern_tag": obj.pattern_tag})
        return format_html(
            '<a href="{}?{}" target="_blank" class="button" '
            'style="font-size:0.75rem;padding:2px 8px;">'
            '＋ Add FAQ</a>',
            add_url,
            params,
        )
    create_faq_link.short_description = "Quick FAQ"
    create_faq_link.allow_tags = True

    def has_add_permission(self, request):
        return False

    def changelist_view(self, request, extra_context=None):
        """Inject high-importance pattern summary into the changelist."""
        extra_context = extra_context or {}
        extra_context["high_importance_patterns"] = high_importance_patterns()
        extra_context["all_patterns"] = negative_pattern_clusters()
        return super().changelist_view(request, extra_context=extra_context)
