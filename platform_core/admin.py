from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import (
    CustomerTenantMembership,
    ContractBillingAccessLink,
    ContractBillingJob,
    ContractBillingNotification,
    ContractBillingSnapshot,
    ClientContractProfile,
    ContractUsageEvent,
    InsightsDailySnapshot,
    InsightsNarrativeSnapshot,
    GICSReference,
    MLASClassificationRecord,
    NAICSReference,
    QuadrantUsageEvent,
    SemanticPreset,
    Slide,
)


class ClassificationValidationBandFilter(admin.SimpleListFilter):
    title = "validation band"
    parameter_name = "validation_band"

    def lookups(self, request, model_admin):
        return (
            ("green", "Green (>= 0.90)"),
            ("yellow", "Yellow (0.75-0.89)"),
            ("red", "Red (< 0.75)"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "green":
            return queryset.filter(confidence_overall__gte=0.90)
        if value == "yellow":
            return queryset.filter(confidence_overall__gte=0.75, confidence_overall__lt=0.90)
        if value == "red":
            return queryset.filter(confidence_overall__lt=0.75)
        return queryset


class ClassificationExternalAlignmentFilter(admin.SimpleListFilter):
    title = "external alignment"
    parameter_name = "external_alignment"

    def lookups(self, request, model_admin):
        return (
            ("linked", "Has external link"),
            ("missing", "Missing external link"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "linked":
            return queryset.exclude(dewey_code="", gics_sub_industry_code="", naics_code_6="")
        if value == "missing":
            return queryset.filter(dewey_code="", gics_sub_industry_code="", naics_code_6="")
        return queryset


class ClassificationSemanticConflictFilter(admin.SimpleListFilter):
    title = "semantic conflict"
    parameter_name = "semantic_conflict"

    def lookups(self, request, model_admin):
        return (
            ("duplicate_term", "Duplicate approved term code"),
            ("duplicate_label", "Duplicate approved Basetrue label"),
            ("approved_missing_external", "Approved missing external alignment"),
            ("term_with_meta", "Term row has MetaTerm code"),
            ("meta_missing_meta", "Meta row missing MetaTerm code"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "duplicate_term":
            duplicate_term_codes = list(
                queryset.filter(review_status="approved", target_layer="term")
                .exclude(mlas_term_code="")
                .values("mlas_term_code")
                .annotate(total=Count("id"))
                .filter(total__gt=1)
                .values_list("mlas_term_code", flat=True)
            )
            return queryset.filter(review_status="approved", target_layer="term", mlas_term_code__in=duplicate_term_codes)
        if value == "duplicate_label":
            duplicate_labels = list(
                queryset.filter(review_status="approved", target_layer="term")
                .exclude(basetrue_label="")
                .values("basetrue_label")
                .annotate(total=Count("id"))
                .filter(total__gt=1)
                .values_list("basetrue_label", flat=True)
            )
            return queryset.filter(review_status="approved", target_layer="term", basetrue_label__in=duplicate_labels)
        if value == "approved_missing_external":
            return queryset.filter(review_status="approved", dewey_code="", gics_sub_industry_code="", naics_code_6="")
        if value == "term_with_meta":
            return queryset.filter(target_layer="term").exclude(mlas_meta_term_code="")
        if value == "meta_missing_meta":
            return queryset.filter(target_layer="meta", mlas_meta_term_code="")
        return queryset


@admin.register(InsightsDailySnapshot)
class InsightsDailySnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "snapshot_date",
        "pressure_index",
        "average_health_score",
        "risk_flag_count",
        "activity_count",
        "user_growth_count",
    )
    search_fields = ("snapshot_date",)
    ordering = ("-snapshot_date",)


@admin.register(InsightsNarrativeSnapshot)
class InsightsNarrativeSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "snapshot_date",
        "state_label",
        "pressure_index",
        "weighted_priority_score",
        "growth_direction",
        "quadrant_priority",
        "pipeline_bottleneck",
    )
    search_fields = ("snapshot_date", "state_label", "pipeline_bottleneck")
    ordering = ("-snapshot_date",)


@admin.register(ClientContractProfile)
class ClientContractProfileAdmin(admin.ModelAdmin):
    list_display = (
        "tenant_key",
        "client_key",
        "display_name",
        "billing_contact_email",
        "billing_plan",
        "monthly_event_allowance",
        "default_schema_version",
        "strict_negotiation",
        "strict_payload_shape",
        "is_active",
    )
    list_filter = ("strict_negotiation", "strict_payload_shape", "is_active")
    search_fields = ("tenant_key", "client_key", "display_name")
    ordering = ("tenant_key", "client_key")


@admin.register(ContractUsageEvent)
class ContractUsageEventAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "tenant_key",
        "endpoint",
        "client_key",
        "billable_units",
        "billable_amount",
        "requested_schema_version",
        "selected_schema_version",
        "negotiation_source",
        "status_code",
    )
    list_filter = (
        "endpoint",
        "status_code",
        "strict_negotiation",
        "strict_payload_shape",
    )
    search_fields = (
        "tenant_key",
        "client_key",
        "requested_schema_version",
        "selected_schema_version",
    )
    ordering = ("-created_at",)


@admin.register(QuadrantUsageEvent)
class QuadrantUsageEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "hour", "is_pm", "slug")
    list_filter = ("is_pm", "hour")
    search_fields = ("slug",)
    ordering = ("-created_at",)


@admin.register(ContractBillingSnapshot)
class ContractBillingSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "tenant_key",
        "client_key",
        "window_days",
        "period_start",
        "period_end",
    )
    search_fields = ("tenant_key", "client_key")
    ordering = ("-created_at",)


@admin.register(ContractBillingJob)
class ContractBillingJobAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "tenant_key",
        "client_key",
        "job_type",
        "status",
        "requested_by",
    )
    list_filter = ("job_type", "status")
    search_fields = ("tenant_key", "client_key")
    ordering = ("-created_at",)


@admin.register(ContractBillingNotification)
class ContractBillingNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "tenant_key",
        "client_key",
        "channel",
        "recipient",
        "status",
        "retry_count",
        "last_attempt_at",
        "sent_at",
    )
    list_filter = ("channel", "status")
    search_fields = ("tenant_key", "client_key", "recipient", "subject")
    ordering = ("-created_at",)


@admin.register(ContractBillingAccessLink)
class ContractBillingAccessLinkAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "tenant_key",
        "client_key",
        "window_days",
        "label",
        "recipient_email",
        "is_active",
        "expires_at",
        "revoked_at",
        "use_count",
    )
    list_filter = ("is_active",)
    search_fields = ("tenant_key", "client_key", "label", "recipient_email", "link_key")
    ordering = ("-created_at",)


@admin.register(CustomerTenantMembership)
class CustomerTenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant_key", "client_key", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("user__email", "user__username", "tenant_key", "client_key")
    ordering = ("tenant_key", "client_key")


@admin.register(SemanticPreset)
class SemanticPresetAdmin(admin.ModelAdmin):
    list_display = ("name", "phase", "color_primary", "metaphor", "dewey_code", "ui_category")
    list_filter = ("phase", "color_primary", "metaphor", "ui_category")
    search_fields = ("name", "mlas_subject", "mlas_branch", "industry_super_sector")
    ordering = ("name",)


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "phase",
        "phase_resolved",
        "color_primary",
        "metaphor",
        "ui_category_resolved",
        "layout_archetype",
        "component_pack",
        "applied_preset",
    )
    list_filter = ("phase", "phase_resolved", "color_primary", "layout_archetype", "component_pack")
    search_fields = ("title", "mlas_subject", "mlas_branch", "mlas_term", "industry_super_sector")
    ordering = ("-updated_at",)


@admin.register(MLASClassificationRecord)
class MLASClassificationRecordAdmin(admin.ModelAdmin):
    actions = (
        "promote_to_candidate",
        "mark_rejected",
        "recompute_consensus_and_reason",
    )

    list_display = (
        "record_id",
        "review_status",
        "target_layer",
        "validation_state",
        "confidence_overall",
        "algorithm_consensus_score",
        "mlas_subject_code",
        "mlas_branch_code",
        "mlas_term_code",
        "basetrue_label",
        "updated_at",
    )
    list_filter = (
        "review_status",
        "target_layer",
        "mlas_subject_code",
        ClassificationValidationBandFilter,
        ClassificationExternalAlignmentFilter,
        ClassificationSemanticConflictFilter,
    )
    search_fields = (
        "record_id",
        "source_name_raw",
        "basetrue_label",
        "mlas_subject_code",
        "mlas_branch_code",
        "mlas_term_code",
        "dewey_code",
        "gics_sub_industry_code",
        "naics_code_6",
    )
    ordering = ("review_status", "-confidence_overall", "record_id")

    @admin.action(description="Promote selected rows to candidate")
    def promote_to_candidate(self, request, queryset):
        queryset.update(review_status=MLASClassificationRecord.REVIEW_CANDIDATE)

    @admin.action(description="Mark selected rows as rejected")
    def mark_rejected(self, request, queryset):
        queryset.update(review_status=MLASClassificationRecord.REVIEW_REJECTED)

    @admin.action(description="Recompute consensus and confidence reason template")
    def recompute_consensus_and_reason(self, request, queryset):
        for record in queryset:
            scores = [
                float(record.algorithm_1_score or 0.0),
                float(record.algorithm_2_score or 0.0),
                float(record.algorithm_3_score or 0.0),
                float(record.algorithm_4_score or 0.0),
            ]
            consensus = round(sum(scores) / 4.0, 6)
            record.algorithm_consensus_score = consensus

            if record.confidence_overall >= 0.90 and consensus >= 0.85:
                band = "high"
                guidance = "strong alignment"
            elif record.confidence_overall >= 0.75 and consensus >= 0.70:
                band = "medium"
                guidance = "good alignment with minor ambiguity"
            else:
                band = "low"
                guidance = "needs reviewer attention"

            record.confidence_reason = (
                f"Auto template: {band} confidence with {guidance}; "
                f"algorithm_consensus={consensus:.2f}."
            )
            record.save(update_fields=["algorithm_consensus_score", "confidence_reason", "updated_at"])

    @admin.display(description="Validation")
    def validation_state(self, obj: MLASClassificationRecord):
        confidence = float(obj.confidence_overall or 0.0)
        if confidence >= 0.90:
            return format_html('<span style="color:#0a7f39;font-weight:600;">Green</span>')
        if confidence >= 0.75:
            return format_html('<span style="color:#a16a00;font-weight:600;">Yellow</span>')
        return format_html('<span style="color:#b00020;font-weight:600;">Red</span>')


@admin.register(NAICSReference)
class NAICSReferenceAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "sector_code", "source_version", "is_active", "updated_at")
    list_filter = ("is_active", "source_version")
    search_fields = ("code", "title", "sector_code")
    ordering = ("code",)


@admin.register(GICSReference)
class GICSReferenceAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "level", "parent_code", "source_version", "is_active", "updated_at")
    list_filter = ("level", "is_active", "source_version")
    search_fields = ("code", "name", "parent_code")
    ordering = ("level", "code")
