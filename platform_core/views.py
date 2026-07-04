import json
import logging
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from platform_core.resolvers.quadrant import get_current_hour, is_pm, resolve_domain, resolve_url
from platform_core.resolvers.quadrant import AM_DOMAINS, PM_DOMAINS
from platform_core.resolvers.quadrant_inversion import HINGE_HOUR, build_inversion_payload

from .models import (
    GICSReference,
    MLASClassificationRecord,
    NAICSReference,
    SemanticBundle,
    SemanticBundleRevision,
    SemanticBundleRevisionTag,
    SemanticBundleShare,
    SemanticPreset,
    QuadrantUsageEvent,
    Slide,
)
from .routing import apply_resolved_route
from .reference_sync import get_gics_source_status

from .unified_admin import (
    _billing_access_link_anomalies_payload,
    _billing_access_link_risk_payload,
    _billing_access_link_risk_trend_payload,
    _billing_access_link_from_token,
    _billing_access_link_analytics_payload,
    _billing_access_links_payload,
    _billing_access_link_payload,
    _billing_access_token,
    _billing_health_explainer_payload,
    _billing_health_score_change_payload,
    _billing_health_score_payload,
    _billing_invoice_email_diagnostics_payload,
    _billing_micro_trends_payload,
    _billing_snapshot_history_payload,
    _contract_billing_summary_payload,
    _customer_billing_forecast_payload,
    _customer_link_usage_insights_payload,
    _customer_invoice_event_feed_payload,
    _customer_invoice_timeline_payload,
    _customer_billing_notifications_payload,
    _customer_membership_payload,
    _render_invoice_pdf_response,
    _verify_billing_access_token,
)


logger = logging.getLogger(__name__)


PRESET_ALIAS_CATALOG = [
    {"name": "create.foundation", "phase": "create", "kind": "bundle"},
    {"name": "post.storyline", "phase": "post", "kind": "bundle"},
    {"name": "work.execution", "phase": "work", "kind": "bundle"},
    {"name": "executive.summary", "phase": "create", "kind": "executive"},
    {"name": "executive.overview", "phase": "post", "kind": "executive"},
    {"name": "executive.pipeline", "phase": "work", "kind": "executive"},
]

PRESET_ALIAS_TO_PHASE = {item["name"]: item["phase"] for item in PRESET_ALIAS_CATALOG}
EXECUTIVE_ALIAS_NAMES = {item["name"] for item in PRESET_ALIAS_CATALOG if item["kind"] == "executive"}

PRESET_BUNDLE_CATALOG = [
    {
        "name": "bundle.foundation.triad",
        "label": "Foundation Triad",
        "family": "foundation.core",
        "description": "Canonical create/post/work progression for foundational slide generation.",
        "sequence": ["create.foundation", "post.storyline", "work.execution"],
    },
    {
        "name": "bundle.executive.inversion",
        "label": "Executive Inversion",
        "family": "executive.overview",
        "description": "Executive semantic inversion across create, post, and work views.",
        "sequence": ["executive.summary", "executive.overview", "executive.pipeline"],
    },
]

PRESET_BUNDLE_BY_NAME = {item["name"]: item for item in PRESET_BUNDLE_CATALOG}

PHASE_TO_EXECUTIVE_ALIAS = {
    "create": "executive.summary",
    "post": "executive.overview",
    "work": "executive.pipeline",
}


def _resolve_preset_with_alias(preset_name: str):
    preset = SemanticPreset.objects.filter(name=preset_name).first()
    if preset:
        return preset, None

    alias_phase = PRESET_ALIAS_TO_PHASE.get(preset_name)
    if not alias_phase:
        return None, None

    phase_preset = SemanticPreset.objects.filter(phase=alias_phase).order_by("name").first()
    if not phase_preset:
        return None, None

    forced_ui_category = "executive" if preset_name in EXECUTIVE_ALIAS_NAMES else None
    return phase_preset, forced_ui_category


def _phase_for_preset_name(preset_name: str) -> str | None:
    preset = SemanticPreset.objects.filter(name=preset_name).only("phase").first()
    if preset:
        return preset.phase
    return PRESET_ALIAS_TO_PHASE.get(preset_name)


def _layout_for_phase(phase: str | None) -> str:
    mapping = {
        "create": "matrix",
        "post": "journey",
        "work": "pipeline",
    }
    return mapping.get((phase or "").lower(), "matrix")


def _bundle_metadata(bundle: dict) -> dict:
    sequence = list(bundle.get("sequence") or [])
    phase_distribution: dict[str, int] = {}
    layout_distribution: dict[str, int] = {}

    for preset_name in sequence:
        phase = _phase_for_preset_name(preset_name) or "unknown"
        layout = _layout_for_phase(phase)
        phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
        layout_distribution[layout] = layout_distribution.get(layout, 0) + 1

    return {
        "name": bundle.get("name"),
        "label": bundle.get("label") or bundle.get("name"),
        "family": bundle.get("family") or "custom",
        "description": bundle.get("description") or "",
        "sequence": sequence,
        "slide_count": len(sequence),
        "phase_distribution": phase_distribution,
        "layout_distribution": layout_distribution,
        "supports_inversion": True,
        "kind": bundle.get("kind") or "bundle",
        "owner": (
            {
                "id": bundle.get("created_by"),
                "username": bundle.get("created_by_username"),
            }
            if bundle.get("created_by")
            else None
        ),
        "current_revision": bundle.get("current_revision"),
        "revision_count": bundle.get("revision_count"),
        "access_role": bundle.get("access_role"),
        "tags": bundle.get("tags") or [],
    }


def _bundle_revision_payload(revision: SemanticBundleRevision) -> dict:
    return {
        "revision_number": revision.revision_number,
        "label": revision.label,
        "family": revision.family,
        "description": revision.description,
        "sequence": list(revision.sequence or []),
        "created_at": revision.created_at.isoformat(),
        "created_by": {
            "id": revision.created_by_id,
            "username": getattr(revision.created_by, "username", "") or "",
        }
        if revision.created_by_id
        else None,
    }


def _bundle_tag_payload(tag: SemanticBundleRevisionTag) -> dict:
    return {
        "name": tag.name,
        "note": tag.note,
        "revision_number": tag.revision.revision_number,
        "created_at": tag.created_at.isoformat(),
        "created_by": {
            "id": tag.created_by_id,
            "username": getattr(tag.created_by, "username", "") or "",
        }
        if tag.created_by_id
        else None,
    }


def _current_bundle_revision(bundle: SemanticBundle):
    return bundle.revisions.order_by("-revision_number", "-id").select_related("created_by").first()


def _bundle_access_role(bundle: SemanticBundle, user) -> str | None:
    if bundle.created_by_id == user.id:
        return "owner"
    share = bundle.shares.filter(user=user, is_active=True).order_by("-id").first()
    if not share:
        return None
    return share.permission


def _can_view_bundle(bundle: SemanticBundle, user) -> bool:
    return _bundle_access_role(bundle, user) in {"owner", SemanticBundleShare.PERMISSION_VIEW, SemanticBundleShare.PERMISSION_EDIT}


def _can_edit_bundle(bundle: SemanticBundle, user) -> bool:
    return _bundle_access_role(bundle, user) in {"owner", SemanticBundleShare.PERMISSION_EDIT}


def _persisted_bundle_row(bundle: SemanticBundle, user) -> dict:
    revision = _current_bundle_revision(bundle)
    current_revision = _bundle_revision_payload(revision) if revision else None
    tags = [
        _bundle_tag_payload(tag)
        for tag in bundle.revision_tags.select_related("revision", "created_by").all().order_by("name")
    ]
    return {
        "name": bundle.name,
        "label": revision.label if revision else bundle.label,
        "family": revision.family if revision else bundle.family,
        "description": revision.description if revision else bundle.description,
        "sequence": list(revision.sequence or bundle.sequence or []) if revision else list(bundle.sequence or []),
        "kind": "custom",
        "created_by": bundle.created_by_id,
        "created_by_username": getattr(bundle.created_by, "username", "") or "",
        "current_revision": current_revision,
        "revision_count": bundle.revisions.count(),
        "access_role": _bundle_access_role(bundle, user),
        "tags": tags,
    }


def _persisted_bundle_rows(user):
    rows = (
        SemanticBundle.objects.select_related("created_by")
        .prefetch_related("revisions", "revision_tags", "shares")
        .filter(Q(created_by=user) | Q(shares__user=user, shares__is_active=True))
        .distinct()
        .order_by("family", "name")
    )
    return [
        _persisted_bundle_row(row, user)
        for row in rows
    ]


def _all_bundle_catalog_rows(user):
    return [*PRESET_BUNDLE_CATALOG, *_persisted_bundle_rows(user)]


def _all_bundle_catalog_by_name(user):
    return {item["name"]: item for item in _all_bundle_catalog_rows(user)}


@require_http_methods(["GET"])
def classification_executive_view(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("Authentication required")

    is_staff = bool(getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False))
    if not is_staff:
        raise PermissionDenied("Staff access required")

    records = MLASClassificationRecord.objects.all()
    total_records = records.count()

    approved_term_count = (
        records
        .filter(target_layer=MLASClassificationRecord.TARGET_TERM, review_status=MLASClassificationRecord.REVIEW_APPROVED)
        .exclude(mlas_term_code="")
        .values("mlas_term_code")
        .distinct()
        .count()
    )
    term_goal = 64

    naics_ref_count = NAICSReference.objects.count()
    gics_ref_count = GICSReference.objects.count()
    gics_source_status = get_gics_source_status()
    naics_ref_last_updated = NAICSReference.objects.order_by("-updated_at").values_list("updated_at", flat=True).first()
    gics_ref_last_updated = GICSReference.objects.order_by("-updated_at").values_list("updated_at", flat=True).first()

    naics_codes_in_records = list(
        records.exclude(naics_code_6="")
        .values_list("naics_code_6", flat=True)
        .distinct()
    )
    gics_codes_in_records = list(
        records.exclude(gics_sub_industry_code="")
        .values_list("gics_sub_industry_code", flat=True)
        .distinct()
    )
    naics_matched_count = NAICSReference.objects.filter(code__in=naics_codes_in_records).count() if naics_codes_in_records else 0
    gics_matched_count = GICSReference.objects.filter(level=GICSReference.LEVEL_SUB_INDUSTRY, code__in=gics_codes_in_records).count() if gics_codes_in_records else 0

    green_count = records.filter(confidence_overall__gte=0.90).count()
    yellow_count = records.filter(confidence_overall__gte=0.75, confidence_overall__lt=0.90).count()
    red_count = records.filter(confidence_overall__lt=0.75).count()

    dewey_count = records.exclude(dewey_code="").count()
    gics_count = records.exclude(gics_sub_industry_code="").count()
    naics_count = records.exclude(naics_code_6="").count()
    any_external_count = records.exclude(dewey_code="", gics_sub_industry_code="", naics_code_6="").count()

    candidate_queue_count = records.filter(review_status=MLASClassificationRecord.REVIEW_CANDIDATE).count()
    draft_queue_count = records.filter(review_status=MLASClassificationRecord.REVIEW_DRAFT).count()
    rejected_count = records.filter(review_status=MLASClassificationRecord.REVIEW_REJECTED).count()

    duplicate_term_codes = list(
        records.filter(
            review_status=MLASClassificationRecord.REVIEW_APPROVED,
            target_layer=MLASClassificationRecord.TARGET_TERM,
        )
        .exclude(mlas_term_code="")
        .values("mlas_term_code")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .values_list("mlas_term_code", flat=True)
    )
    duplicate_labels = list(
        records.filter(
            review_status=MLASClassificationRecord.REVIEW_APPROVED,
            target_layer=MLASClassificationRecord.TARGET_TERM,
        )
        .exclude(basetrue_label="")
        .values("basetrue_label")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .values_list("basetrue_label", flat=True)
    )

    duplicate_term_count = records.filter(
        review_status=MLASClassificationRecord.REVIEW_APPROVED,
        target_layer=MLASClassificationRecord.TARGET_TERM,
        mlas_term_code__in=duplicate_term_codes,
    ).count()
    duplicate_label_count = records.filter(
        review_status=MLASClassificationRecord.REVIEW_APPROVED,
        target_layer=MLASClassificationRecord.TARGET_TERM,
        basetrue_label__in=duplicate_labels,
    ).count()
    approved_missing_external_count = records.filter(
        review_status=MLASClassificationRecord.REVIEW_APPROVED,
        dewey_code="",
        gics_sub_industry_code="",
        naics_code_6="",
    ).count()
    term_with_meta_count = records.filter(target_layer=MLASClassificationRecord.TARGET_TERM).exclude(mlas_meta_term_code="").count()
    meta_missing_meta_count = records.filter(target_layer=MLASClassificationRecord.TARGET_META, mlas_meta_term_code="").count()

    term_progress_pct = 0 if term_goal == 0 else round((approved_term_count / term_goal) * 100.0, 1)
    if total_records == 0:
        readiness_status = "Blocked"
    else:
        readiness_status = "Ready" if approved_term_count >= term_goal and red_count == 0 else "In Progress"
    admin_changelist_url = reverse("admin:platform_core_mlasclassificationrecord_changelist")
    naics_admin_changelist_url = reverse("admin:platform_core_naicsreference_changelist")
    gics_admin_changelist_url = reverse("admin:platform_core_gicsreference_changelist")

    def _admin_link(params: dict) -> str:
        query = urlencode(params)
        return f"{admin_changelist_url}?{query}" if query else admin_changelist_url

    missing_external_count = max(total_records - any_external_count, 0)
    missing_external_ratio = 0.0 if total_records == 0 else (missing_external_count / total_records)

    penalty_red_band = min(red_count * 6, 40)
    penalty_conflicts = min((
        duplicate_term_count
        + duplicate_label_count
        + approved_missing_external_count
        + term_with_meta_count
        + meta_missing_meta_count
    ) * 3, 30)
    penalty_candidate_backlog = min(candidate_queue_count * 2, 15)
    penalty_missing_external = min(int(round(missing_external_ratio * 20)), 15)

    if total_records == 0:
        readiness_heat_score = 0
        readiness_heat_band = "red"
        readiness_heat_label = "Blocked"
    else:
        readiness_heat_score = max(
            0,
            100 - penalty_red_band - penalty_conflicts - penalty_candidate_backlog - penalty_missing_external,
        )
        if readiness_heat_score >= 80:
            readiness_heat_band = "green"
            readiness_heat_label = "Ready"
        elif readiness_heat_score >= 60:
            readiness_heat_band = "yellow"
            readiness_heat_label = "Caution"
        else:
            readiness_heat_band = "red"
            readiness_heat_label = "Blocked"

        # Governance rule: readiness cannot be fully green until the 64-term goal is met.
        if approved_term_count < term_goal and readiness_heat_band == "green":
            readiness_heat_band = "yellow"
            readiness_heat_label = "Caution"

    context = {
        "total_records": total_records,
        "approved_term_count": approved_term_count,
        "term_goal": term_goal,
        "term_progress_pct": term_progress_pct,
        "confidence_bands": {
            "green": green_count,
            "yellow": yellow_count,
            "red": red_count,
        },
        "external_alignment": {
            "dewey": dewey_count,
            "gics": gics_count,
            "naics": naics_count,
            "any": any_external_count,
        },
        "reference_sync": {
            "naics": {
                "count": naics_ref_count,
                "matched": naics_matched_count,
                "last_updated": naics_ref_last_updated,
            },
            "gics": {
                "count": gics_ref_count,
                "matched": gics_matched_count,
                "last_updated": gics_ref_last_updated,
                "source_status": gics_source_status,
            },
        },
        "reviewer_queue": {
            "candidate": candidate_queue_count,
            "draft": draft_queue_count,
            "rejected": rejected_count,
        },
        "training_readiness": {
            "status": readiness_status,
            "has_full_term_coverage": approved_term_count >= term_goal,
            "has_no_red_band": red_count == 0,
            "has_candidate_backlog": candidate_queue_count > 0,
        },
        "training_readiness_heat": {
            "score": readiness_heat_score,
            "band": readiness_heat_band,
            "label": readiness_heat_label,
            "blockers": {
                "red_band_count": red_count,
                "semantic_conflict_total": (
                    duplicate_term_count
                    + duplicate_label_count
                    + approved_missing_external_count
                    + term_with_meta_count
                    + meta_missing_meta_count
                ),
                "candidate_backlog": candidate_queue_count,
                "missing_external_count": missing_external_count,
                "missing_external_ratio": round(missing_external_ratio, 4),
            },
            "penalties": {
                "red_band": penalty_red_band,
                "semantic_conflicts": penalty_conflicts,
                "candidate_backlog": penalty_candidate_backlog,
                "missing_external": penalty_missing_external,
            },
        },
        "semantic_conflicts": {
            "duplicate_term": duplicate_term_count,
            "duplicate_label": duplicate_label_count,
            "approved_missing_external": approved_missing_external_count,
            "term_with_meta": term_with_meta_count,
            "meta_missing_meta": meta_missing_meta_count,
            "total": (
                duplicate_term_count
                + duplicate_label_count
                + approved_missing_external_count
                + term_with_meta_count
                + meta_missing_meta_count
            ),
        },
        "admin_links": {
            "all": admin_changelist_url,
            "naics_reference": naics_admin_changelist_url,
            "gics_reference": gics_admin_changelist_url,
            "red_band": _admin_link({"validation_band": "red"}),
            "candidate_queue": _admin_link({"review_status__exact": MLASClassificationRecord.REVIEW_CANDIDATE}),
            "missing_external": _admin_link({"external_alignment": "missing"}),
            "conflict_duplicate_term": _admin_link({"semantic_conflict": "duplicate_term"}),
            "conflict_duplicate_label": _admin_link({"semantic_conflict": "duplicate_label"}),
            "conflict_approved_missing_external": _admin_link({"semantic_conflict": "approved_missing_external"}),
            "conflict_term_with_meta": _admin_link({"semantic_conflict": "term_with_meta"}),
            "conflict_meta_missing_meta": _admin_link({"semantic_conflict": "meta_missing_meta"}),
            "heat_red_band": _admin_link({"validation_band": "red"}),
            "heat_conflicts": _admin_link({"semantic_conflict": "duplicate_term"}),
            "heat_candidate_backlog": _admin_link({"review_status__exact": MLASClassificationRecord.REVIEW_CANDIDATE}),
            "heat_missing_external": _admin_link({"external_alignment": "missing"}),
        },
    }
    return TemplateResponse(request, "platform_core/classification_executive.html", context)


def _bundle_phase_distribution(sequence: list[str]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for preset_name in sequence:
        phase = _phase_for_preset_name(preset_name) or "unknown"
        distribution[phase] = distribution.get(phase, 0) + 1
    return distribution


@require_http_methods(["GET"])
def quadrant_route_view(request):
    current_hour = get_current_hour()
    current_pm = is_pm()
    slug, url = _resolve_navigation(current_hour, current_pm)
    return JsonResponse({"slug": slug, "url": url})


@require_http_methods(["GET"])
def quadrant_heatmap_view(request):
    qs = (
        QuadrantUsageEvent.objects
        .values("hour", "is_pm")
        .annotate(count=Count("id"))
    )

    am = {str(hour): 0 for hour in range(1, 13)}
    pm = {str(hour): 0 for hour in range(1, 13)}

    for row in qs:
        hour = str(row["hour"])
        if row["is_pm"]:
            pm[hour] = row["count"]
        else:
            am[hour] = row["count"]

    return JsonResponse({"am": am, "pm": pm})


def _slug_label(slug: str) -> str:
    return str(slug).replace("-", " ").replace("_", " ").title()


def _resolve_navigation(hour: int, pm: bool) -> tuple[str, str]:
    """
    Navigation truth rule: compartment 12 flips grid phase for user routing.
    """
    navigation_pm = (not bool(pm)) if int(hour) == HINGE_HOUR else bool(pm)
    slug = resolve_domain(hour=hour, pm=navigation_pm)
    url = resolve_url(hour=hour, pm=navigation_pm)

    # Runtime safety guard: enforce canonical hour-12 destinations even if future
    # mapping changes accidentally drift.
    if int(hour) == HINGE_HOUR:
        expected_slug = "harvestcrops" if bool(pm) else "tr"
        expected_url = f"/{'center' if bool(pm) else 'domain'}/grid/{expected_slug}/"
        if slug != expected_slug or url != expected_url:
            logger.critical(
                "Quadrant navigation safety override at hour 12",
                extra={
                    "source_hour": int(hour),
                    "source_is_pm": bool(pm),
                    "computed_slug": slug,
                    "computed_url": url,
                    "expected_slug": expected_slug,
                    "expected_url": expected_url,
                },
            )
            slug = expected_slug
            url = expected_url

    return slug, url


@require_http_methods(["GET"])
def quadrant_overlay_view(request):
    current_pm = is_pm()
    current_hour = get_current_hour()
    domain_map = PM_DOMAINS if current_pm else AM_DOMAINS
    inversion = build_inversion_payload(current_hour, current_pm)

    usage_rows = (
        QuadrantUsageEvent.objects
        .filter(is_pm=current_pm)
        .values("hour")
        .annotate(count=Count("id"))
    )
    usage_by_hour = {int(row["hour"]): int(row["count"]) for row in usage_rows}

    slots = []
    for hour in range(1, 13):
        slug = domain_map[hour]
        slots.append({
            "hour": hour,
            "slug": slug,
            "label": _slug_label(slug),
            "usage_count": usage_by_hour.get(hour, 0),
            "is_active": hour == current_hour,
            "is_hinge": hour == HINGE_HOUR,
        })

    return JsonResponse({
        "mode": "pm" if current_pm else "am",
        "active_hour": current_hour,
        "inversion": inversion,
        "slots": slots,
    })


@require_http_methods(["GET"])
def quadrant_redirect_view(request):
    current_hour = get_current_hour()
    current_pm = is_pm()
    slug, url = _resolve_navigation(current_hour, current_pm)
    QuadrantUsageEvent.objects.create(hour=current_hour, is_pm=current_pm, slug=slug)
    return HttpResponseRedirect(url)


def _executive_projection(sequence: list[str]) -> list[str]:
    projected = []
    for preset_name in sequence:
        phase = _phase_for_preset_name(preset_name)
        projected.append(PHASE_TO_EXECUTIVE_ALIAS.get((phase or "").lower(), preset_name))
    return projected


def _validate_bundle_sequence(sequence: list[str]) -> str | None:
    if not sequence:
        return "sequence must include at least one preset name."

    normalized = []
    for item in sequence:
        name = str(item).strip()
        if not name:
            return "sequence cannot include blank preset names."
        phase = _phase_for_preset_name(name)
        if not phase:
            return f"Unknown preset in sequence: {name}"
        normalized.append((name, phase))

    for index in range(1, len(normalized)):
        previous_name, previous_phase = normalized[index - 1]
        current_name, current_phase = normalized[index]
        if previous_phase == current_phase:
            return (
                "sequence cannot contain consecutive presets in the same phase: "
                f"{previous_name} -> {current_name}"
            )
    return None


def _normalize_bundle_request(bundle_name: str, body: dict, user) -> tuple[dict | None, JsonResponse | None]:
    if bundle_name:
        bundle = _all_bundle_catalog_by_name(user).get(bundle_name)
        if not bundle:
            return None, JsonResponse({"detail": "Bundle not found."}, status=404)
        return dict(bundle), None

    sequence = body.get("sequence")
    if not isinstance(sequence, list) or not sequence:
        return None, JsonResponse({"detail": "bundle or non-empty sequence is required."}, status=400)

    normalized_sequence = [str(item).strip() for item in sequence if str(item).strip()]
    if not normalized_sequence:
        return None, JsonResponse({"detail": "sequence must include preset names."}, status=400)

    validation_error = _validate_bundle_sequence(normalized_sequence)
    if validation_error:
        return None, JsonResponse({"detail": validation_error}, status=400)

    return {
        "name": str(body.get("name") or "custom.bundle").strip() or "custom.bundle",
        "label": str(body.get("label") or "Custom Bundle").strip() or "Custom Bundle",
        "family": str(body.get("family") or "custom.user").strip() or "custom.user",
        "description": str(body.get("description") or "").strip(),
        "sequence": normalized_sequence,
        "kind": "custom",
    }, None


def _apply_preset_name_to_slide(slide: Slide, preset_name: str, body: dict | None = None):
    body = body or {}
    preset, alias_ui_category = _resolve_preset_with_alias(preset_name)
    if not preset:
        return None, JsonResponse({"detail": "Preset not found."}, status=404)

    # Preserve an existing explicit category override unless caller explicitly sends one.
    explicit_category_override = body.get("ui_category")
    if explicit_category_override is None and alias_ui_category is not None:
        explicit_category_override = alias_ui_category
    prior_ui_category = slide.ui_category

    slide.phase = preset.phase
    slide.color_primary = preset.color_primary
    slide.metaphor = preset.metaphor
    slide.mlas_subject = preset.mlas_subject
    slide.mlas_branch = preset.mlas_branch
    slide.mlas_term = preset.mlas_term
    slide.mlas_meta = preset.mlas_meta
    slide.dewey_code = preset.dewey_code
    slide.industry_super_sector = preset.industry_super_sector
    slide.industry_sector = preset.industry_sector
    slide.industry_group = preset.industry_group
    slide.industry_sub_industry = preset.industry_sub_industry
    slide.ui_category = preset.ui_category

    # Optional metadata overrides for deterministic testing/workflows.
    for field_name in ("mlas_subject", "mlas_branch", "mlas_term", "mlas_meta"):
        if field_name in body:
            setattr(slide, field_name, body.get(field_name) or None)

    if explicit_category_override is not None:
        slide.ui_category = (explicit_category_override or "").strip() or None
    elif prior_ui_category:
        slide.ui_category = prior_ui_category

    slide.applied_preset = preset

    requested_component_pack = (body.get("component_pack") or "").strip()
    if requested_component_pack == "deep-pack" and not slide.mlas_meta:
        return None, JsonResponse(
            {"detail": "mlas_meta is required when component_pack=deep-pack is requested."},
            status=400,
        )

    apply_resolved_route(slide)

    if slide.component_pack == "deep-pack" and not slide.mlas_meta:
        return None, JsonResponse(
            {"detail": "mlas_meta is required when component_pack resolves to deep-pack."},
            status=400,
        )

    return slide, None


def customer_billing_view(request):
    tenant_key = (request.GET.get("tenant") or "").strip()
    client_key = (request.GET.get("client") or "").strip()
    access_token = (request.GET.get("access_token") or "").strip()
    try:
        window_days = int((request.GET.get("window_days") or "30").strip())
    except ValueError:
        window_days = 30
    if window_days <= 0:
        window_days = 30

    memberships = _customer_membership_payload(request.user, tenant_key=tenant_key, client_key=client_key)
    if (not tenant_key and not client_key) and memberships:
        tenant_key = memberships[0]["tenant_key"]
        client_key = memberships[0]["client_key"]

    if not tenant_key and not client_key:
        raise Http404("tenant or client query parameter required")

    is_staff = bool(getattr(request.user, "is_staff", False))
    has_membership = bool(_customer_membership_payload(request.user, tenant_key=tenant_key, client_key=client_key))
    if not is_staff and not has_membership and not _verify_billing_access_token(access_token, tenant_key, client_key, window_days=window_days):
        raise PermissionDenied("Signed billing access token required")

    summary = _contract_billing_summary_payload(
        window_days=window_days,
        tenant_key=tenant_key,
        client_key=client_key,
    )
    history = _billing_snapshot_history_payload(tenant_key=tenant_key, client_key=client_key)
    resolved_token = access_token or _billing_access_token(tenant_key, client_key, window_days=window_days)
    access_link, _ = _billing_access_link_from_token(
        resolved_token,
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=window_days,
    )
    notifications = _customer_billing_notifications_payload(tenant_key=tenant_key, client_key=client_key)
    access_link_analytics = _billing_access_link_analytics_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=window_days,
        status_filter="all",
        expires_filter="all",
    )
    scoped_links = _billing_access_links_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=window_days,
        limit=50,
        status_filter="all",
        expires_filter="all",
        sort_by="newest",
    )
    anomalies = _billing_access_link_anomalies_payload(scoped_links)
    invoice_notifications = _customer_billing_notifications_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        channel="invoice_email",
        limit=12,
    )
    email_diagnostics = _billing_invoice_email_diagnostics_payload(invoice_notifications)
    access_link_risk = _billing_access_link_risk_payload(scoped_links, anomalies, access_link_analytics)
    access_link_risk_trend = _billing_access_link_risk_trend_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        days=30,
    )
    health_score = _billing_health_score_payload(
        summary.get("summary", []),
        access_link_analytics,
        anomalies,
        email_diagnostics,
        access_link_risk,
    )
    health_explainer = _billing_health_explainer_payload(
        health_score,
        anomalies,
        email_diagnostics,
        access_link_risk,
    )
    health_score_change = _billing_health_score_change_payload(
        health_score,
        access_link_risk_trend,
        anomalies,
        email_diagnostics,
    )
    billing_forecast = _customer_billing_forecast_payload(summary, history)
    link_usage_insights = _customer_link_usage_insights_payload(scoped_links, access_link_analytics)
    micro_trends = _billing_micro_trends_payload(tenant_key=tenant_key, client_key=client_key, days=7)
    context = {
        "billing_summary": summary,
        "billing_history": history,
        "billing_notifications": notifications,
        "invoice_email_notifications": invoice_notifications,
        "billing_insights": {
            "health_score": health_score,
            "health_explainer": health_explainer,
            "health_score_change": health_score_change,
            "anomalies": anomalies,
            "email_diagnostics": email_diagnostics,
            "access_link_risk": access_link_risk,
            "access_link_risk_trend": access_link_risk_trend,
            "billing_forecast": billing_forecast,
            "link_usage_insights": link_usage_insights,
            "micro_trends": micro_trends,
        },
        "billing_filters": {
            "tenant": tenant_key,
            "client": client_key,
            "window_days": window_days,
        },
        "billing_access": {
            "token": resolved_token,
            "link": _billing_access_link_payload(access_link, token=resolved_token) if access_link else {},
        },
        "billing_memberships": memberships,
    }
    return TemplateResponse(request, "platform_core/customer_billing.html", context)


def customer_billing_invoice_view(request):
    tenant_key = (request.GET.get("tenant") or "").strip()
    client_key = (request.GET.get("client") or "").strip()
    access_token = (request.GET.get("access_token") or "").strip()
    output_format = (request.GET.get("format") or "json").strip().lower()
    if output_format not in {"json", "csv", "txt", "pdf"}:
        output_format = "json"
    try:
        window_days = int((request.GET.get("window_days") or "30").strip())
    except ValueError:
        window_days = 30
    if window_days <= 0:
        window_days = 30

    is_staff = bool(getattr(request.user, "is_staff", False))
    has_membership = bool(_customer_membership_payload(request.user, tenant_key=tenant_key, client_key=client_key))
    if not is_staff and not has_membership and not _verify_billing_access_token(access_token, tenant_key, client_key, window_days=window_days):
        raise PermissionDenied("Signed billing access token required")

    payload = _contract_billing_summary_payload(window_days=window_days, tenant_key=tenant_key, client_key=client_key)
    if output_format == "pdf":
        return _render_invoice_pdf_response(payload)

    if output_format == "json":
        return JsonResponse(payload)

    rows = payload.get("summary", [])
    if output_format == "csv":
        headers = [
            "invoice_number",
            "tenant_key",
            "client_key",
            "billing_plan",
            "billable_units",
            "estimated_amount",
            "overage_amount",
            "invoice_signature",
        ]
        csv_lines = [",".join(headers)]
        for row in rows:
            csv_lines.append(",".join(str(row.get(header, "")) for header in headers))
        response = HttpResponse("\n".join(csv_lines) + "\n", content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="customer-invoice.csv"'
        return response

    txt_lines = [
        f"Customer Invoice Window {payload.get('window_days')} days",
        f"Tenant: {payload.get('tenant_key')}",
        f"Client: {payload.get('client_key')}",
        "",
    ]
    for row in rows:
        txt_lines.extend(
            [
                f"Invoice {row.get('invoice_number')}",
                f"Plan: {row.get('billing_plan')}",
                f"Units: {row.get('billable_units')} | Estimated: {row.get('estimated_amount')} | Overage: {row.get('overage_amount')}",
                f"Signature: {row.get('invoice_signature')}",
                "",
            ]
        )
    response = HttpResponse("\n".join(txt_lines), content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="customer-invoice.txt"'
    return response


def customer_invoice_center_view(request):
    tenant_key = (request.GET.get("tenant") or "").strip()
    client_key = (request.GET.get("client") or "").strip()
    access_token = (request.GET.get("access_token") or "").strip()
    try:
        window_days = int((request.GET.get("window_days") or "30").strip())
    except ValueError:
        window_days = 30
    if window_days <= 0:
        window_days = 30

    memberships = _customer_membership_payload(request.user, tenant_key=tenant_key, client_key=client_key)
    if (not tenant_key and not client_key) and memberships:
        tenant_key = memberships[0]["tenant_key"]
        client_key = memberships[0]["client_key"]

    is_staff = bool(getattr(request.user, "is_staff", False))
    has_membership = bool(_customer_membership_payload(request.user, tenant_key=tenant_key, client_key=client_key))
    if not is_staff and not has_membership and not _verify_billing_access_token(access_token, tenant_key, client_key, window_days=window_days):
        raise PermissionDenied("Signed billing access token required")

    summary = _contract_billing_summary_payload(window_days=window_days, tenant_key=tenant_key, client_key=client_key)
    history = _billing_snapshot_history_payload(tenant_key=tenant_key, client_key=client_key)
    invoice_notifications = _customer_billing_notifications_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        channel="invoice_email",
        limit=16,
    )
    invoice_timeline = _customer_invoice_timeline_payload(summary, history, invoice_notifications)
    invoice_event_feed = _customer_invoice_event_feed_payload(
        summary,
        history,
        invoice_notifications,
        limit=24,
    )
    resolved_token = access_token or _billing_access_token(tenant_key, client_key, window_days=window_days)
    access_link, _ = _billing_access_link_from_token(
        resolved_token,
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=window_days,
    )
    context = {
        "billing_summary": summary,
        "billing_history": history,
        "billing_filters": {
            "tenant": tenant_key,
            "client": client_key,
            "window_days": window_days,
        },
        "billing_access": {
            "token": resolved_token,
            "link": _billing_access_link_payload(access_link, token=resolved_token) if access_link else {},
        },
        "billing_memberships": memberships,
        "invoice_timeline": invoice_timeline,
        "invoice_event_feed": invoice_event_feed,
        "invoice_email_notifications": invoice_notifications,
    }
    return TemplateResponse(request, "platform_core/customer_invoice_center.html", context)


def _slide_payload(slide: Slide) -> dict:
    return {
        "id": slide.id,
        "title": slide.title,
        "phase": slide.phase,
        "phase_resolved": slide.phase_resolved,
        "color_primary": slide.color_primary,
        "metaphor": slide.metaphor,
        "mlas": {
            "subject": slide.mlas_subject,
            "branch": slide.mlas_branch,
            "term": slide.mlas_term,
            "meta": slide.mlas_meta,
        },
        "dewey": {
            "code": slide.dewey_code,
            "nav_group": slide.nav_group,
        },
        "industry": {
            "super_sector": slide.industry_super_sector,
            "sector": slide.industry_sector,
            "group": slide.industry_group,
            "sub_industry": slide.industry_sub_industry,
            "page_signature": slide.page_signature,
        },
        "ui": {
            "category": slide.ui_category,
            "category_resolved": slide.ui_category_resolved,
            "layout_archetype": slide.layout_archetype,
            "component_pack": slide.component_pack,
        },
        "applied_preset": slide.applied_preset.name if slide.applied_preset_id else None,
    }


@require_http_methods(["GET"])
def preset_list_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    phase_order = {"create": 0, "post": 1, "work": 2}
    rows = [
        {
            "name": row["name"],
            "phase": row["phase"],
            "kind": "preset",
        }
        for row in SemanticPreset.objects.values("name", "phase")
    ]
    rows.extend(PRESET_ALIAS_CATALOG)
    rows.sort(key=lambda row: (phase_order.get((row.get("phase") or "").lower(), 99), row.get("name") or ""))

    return JsonResponse({"presets": rows}, status=200)


@require_http_methods(["GET"])
def preset_bundle_list_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    bundles = sorted(
        (_bundle_metadata(row) for row in _all_bundle_catalog_rows(request.user)),
        key=lambda row: row["family"] + row["name"],
    )
    return JsonResponse({"bundles": bundles}, status=200)


@require_http_methods(["POST"])
def preset_bundle_create_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    sequence = body.get("sequence")
    if not isinstance(sequence, list):
        return JsonResponse({"detail": "sequence must be a list."}, status=400)

    validation_error = _validate_bundle_sequence([str(item) for item in sequence])
    if validation_error:
        return JsonResponse({"detail": validation_error}, status=400)

    name = (body.get("name") or "").strip()
    label = (body.get("label") or "").strip()
    family = (body.get("family") or "custom.user").strip() or "custom.user"
    if not name or not label:
        return JsonResponse({"detail": "name and label are required."}, status=400)

    existing = SemanticBundle.objects.filter(name=name).first()
    if existing and not _can_edit_bundle(existing, request.user):
        access_role = _bundle_access_role(existing, request.user)
        detail = "You do not have edit access to this bundle." if access_role else "You do not own this bundle."
        return JsonResponse({"detail": detail}, status=403)

    bundle, created = SemanticBundle.objects.get_or_create(
        name=name,
        defaults={
            "label": label,
            "family": family,
            "description": (body.get("description") or "").strip(),
            "sequence": [str(item).strip() for item in sequence],
            "created_by": request.user,
        },
    )
    if not created:
        bundle.label = label
        bundle.family = family
        bundle.description = (body.get("description") or "").strip()
        bundle.sequence = [str(item).strip() for item in sequence]
        bundle.save(update_fields=["label", "family", "description", "sequence", "updated_at"])

    latest_revision = _current_bundle_revision(bundle)
    next_revision_number = 1 if not latest_revision else latest_revision.revision_number + 1
    sequence_values = [str(item).strip() for item in sequence]
    if not latest_revision or (
        latest_revision.label != label
        or latest_revision.family != family
        or latest_revision.description != (body.get("description") or "").strip()
        or list(latest_revision.sequence or []) != sequence_values
    ):
        revision = SemanticBundleRevision.objects.create(
            bundle=bundle,
            revision_number=next_revision_number,
            label=label,
            family=family,
            description=(body.get("description") or "").strip(),
            sequence=sequence_values,
            created_by=request.user,
        )
    else:
        revision = latest_revision
    status_code = 201 if created else 200
    return JsonResponse({"bundle": _bundle_metadata(_persisted_bundle_row(bundle, request.user))}, status=status_code)


@require_http_methods(["GET"])
def preset_bundle_history_view(request, bundle_name: str):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    bundle = (
        SemanticBundle.objects.select_related("created_by")
        .prefetch_related("shares", "revisions", "revision_tags")
        .filter(name=bundle_name)
        .first()
    )
    if not bundle or not _can_view_bundle(bundle, request.user):
        return JsonResponse({"detail": "Bundle not found."}, status=404)

    revisions = [
        _bundle_revision_payload(revision)
        for revision in bundle.revisions.select_related("created_by").all().order_by("-revision_number", "-id")
    ]
    tags = [
        _bundle_tag_payload(tag)
        for tag in bundle.revision_tags.select_related("revision", "created_by").all().order_by("name")
    ]
    return JsonResponse(
        {
            "bundle": _bundle_metadata(_persisted_bundle_row(bundle, request.user)),
            "history": revisions,
            "tags": tags,
        },
        status=200,
    )


@require_http_methods(["GET"])
def preset_bundle_compare_view(request, bundle_name: str):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    bundle = (
        SemanticBundle.objects.select_related("created_by")
        .prefetch_related("shares", "revisions", "revision_tags")
        .filter(name=bundle_name)
        .first()
    )
    if not bundle or not _can_view_bundle(bundle, request.user):
        return JsonResponse({"detail": "Bundle not found."}, status=404)

    try:
        from_revision = int((request.GET.get("from") or "").strip())
        to_revision = int((request.GET.get("to") or "").strip())
    except ValueError:
        return JsonResponse({"detail": "from and to query params must be integers."}, status=400)

    if from_revision <= 0 or to_revision <= 0:
        return JsonResponse({"detail": "from and to query params must be positive integers."}, status=400)

    revisions_by_number = {
        row.revision_number: row
        for row in bundle.revisions.select_related("created_by").all()
    }
    base = revisions_by_number.get(from_revision)
    target = revisions_by_number.get(to_revision)
    if not base or not target:
        return JsonResponse({"detail": "One or both revisions were not found."}, status=404)

    from_sequence = list(base.sequence or [])
    to_sequence = list(target.sequence or [])
    from_index = {name: idx for idx, name in enumerate(from_sequence)}
    to_index = {name: idx for idx, name in enumerate(to_sequence)}

    added = [name for name in to_sequence if name not in from_index]
    removed = [name for name in from_sequence if name not in to_index]
    reordered = [
        name
        for name in to_sequence
        if name in from_index and from_index[name] != to_index[name]
    ]

    before_distribution = _bundle_phase_distribution(from_sequence)
    after_distribution = _bundle_phase_distribution(to_sequence)
    all_phases = sorted(set(before_distribution.keys()) | set(after_distribution.keys()))
    delta_distribution = {
        phase: after_distribution.get(phase, 0) - before_distribution.get(phase, 0)
        for phase in all_phases
    }

    executive_from = _executive_projection(from_sequence)
    executive_to = _executive_projection(to_sequence)
    executive_changed_positions = [
        index + 1
        for index in range(min(len(executive_from), len(executive_to)))
        if executive_from[index] != executive_to[index]
    ]

    return JsonResponse(
        {
            "bundle": _bundle_metadata(_persisted_bundle_row(bundle, request.user)),
            "compare": {
                "from_revision": _bundle_revision_payload(base),
                "to_revision": _bundle_revision_payload(target),
                "changes": {
                    "label_changed": base.label != target.label,
                    "family_changed": base.family != target.family,
                    "description_changed": base.description != target.description,
                    "sequence_changed": from_sequence != to_sequence,
                },
                "sequence": {
                    "from": from_sequence,
                    "to": to_sequence,
                    "added": added,
                    "removed": removed,
                    "reordered": reordered,
                },
                "distribution": {
                    "before_phase_distribution": before_distribution,
                    "after_phase_distribution": after_distribution,
                    "phase_distribution_delta": delta_distribution,
                },
                "executive_projection": {
                    "from": executive_from,
                    "to": executive_to,
                    "changed_positions": executive_changed_positions,
                    "changed_count": len(executive_changed_positions),
                },
            },
        },
        status=200,
    )


@require_http_methods(["POST"])
def preset_bundle_rollback_view(request, bundle_name: str):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    bundle = SemanticBundle.objects.select_related("created_by").prefetch_related("shares", "revisions", "revision_tags").filter(name=bundle_name).first()
    if not bundle:
        return JsonResponse({"detail": "Bundle not found."}, status=404)
    if not _can_edit_bundle(bundle, request.user):
        return JsonResponse({"detail": "You do not have edit access to this bundle."}, status=403)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    try:
        target_revision_number = int(body.get("revision_number"))
    except (TypeError, ValueError):
        return JsonResponse({"detail": "revision_number must be an integer."}, status=400)

    target_revision = bundle.revisions.filter(revision_number=target_revision_number).select_related("created_by").first()
    if not target_revision:
        return JsonResponse({"detail": "Revision not found."}, status=404)

    latest_revision = _current_bundle_revision(bundle)
    if latest_revision and latest_revision.revision_number == target_revision_number:
        return JsonResponse({"detail": "Target revision is already current."}, status=400)

    next_revision_number = 1 if not latest_revision else latest_revision.revision_number + 1
    bundle.label = target_revision.label
    bundle.family = target_revision.family
    bundle.description = target_revision.description
    bundle.sequence = list(target_revision.sequence or [])
    bundle.save(update_fields=["label", "family", "description", "sequence", "updated_at"])

    new_revision = SemanticBundleRevision.objects.create(
        bundle=bundle,
        revision_number=next_revision_number,
        label=target_revision.label,
        family=target_revision.family,
        description=target_revision.description,
        sequence=list(target_revision.sequence or []),
        created_by=request.user,
    )

    return JsonResponse(
        {
            "bundle": _bundle_metadata(_persisted_bundle_row(bundle, request.user)),
            "rolled_back_to": target_revision_number,
            "new_revision": _bundle_revision_payload(new_revision),
        },
        status=200,
    )


@require_http_methods(["GET", "POST"])
def preset_bundle_tag_view(request, bundle_name: str):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    bundle = SemanticBundle.objects.select_related("created_by").prefetch_related("shares", "revisions", "revision_tags").filter(name=bundle_name).first()
    if not bundle or not _can_view_bundle(bundle, request.user):
        return JsonResponse({"detail": "Bundle not found."}, status=404)

    if request.method == "GET":
        tags = [
            _bundle_tag_payload(tag)
            for tag in bundle.revision_tags.select_related("revision", "created_by").all().order_by("name")
        ]
        return JsonResponse({"bundle": _bundle_metadata(_persisted_bundle_row(bundle, request.user)), "tags": tags}, status=200)

    if not _can_edit_bundle(bundle, request.user):
        return JsonResponse({"detail": "You do not have edit access to this bundle."}, status=403)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    tag_name = (body.get("name") or "").strip().lower()
    if not tag_name:
        return JsonResponse({"detail": "name is required."}, status=400)

    revision_number = body.get("revision_number")
    if revision_number is None:
        target_revision = _current_bundle_revision(bundle)
    else:
        try:
            revision_number = int(revision_number)
        except (TypeError, ValueError):
            return JsonResponse({"detail": "revision_number must be an integer."}, status=400)
        target_revision = bundle.revisions.filter(revision_number=revision_number).select_related("created_by").first()

    if not target_revision:
        return JsonResponse({"detail": "Revision not found."}, status=404)

    tag, created = SemanticBundleRevisionTag.objects.get_or_create(
        bundle=bundle,
        name=tag_name,
        defaults={
            "revision": target_revision,
            "note": (body.get("note") or "").strip(),
            "created_by": request.user,
        },
    )
    if not created:
        tag.revision = target_revision
        tag.note = (body.get("note") or "").strip()
        tag.created_by = request.user
        tag.save(update_fields=["revision", "note", "created_by"])

    return JsonResponse({"tag": _bundle_tag_payload(tag)}, status=201 if created else 200)


@require_http_methods(["GET", "POST"])
def preset_bundle_share_view(request, bundle_name: str):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    bundle = SemanticBundle.objects.select_related("created_by").prefetch_related("shares").filter(name=bundle_name).first()
    if not bundle:
        return JsonResponse({"detail": "Bundle not found."}, status=404)

    if request.method == "GET":
        if bundle.created_by_id != request.user.id:
            return JsonResponse({"detail": "Only owners can view share grants."}, status=403)
        shares = [
            {
                "username": share.user.username,
                "permission": share.permission,
                "is_active": share.is_active,
                "updated_at": share.updated_at.isoformat(),
            }
            for share in bundle.shares.select_related("user").all().order_by("user__username")
        ]
        return JsonResponse({"shares": shares}, status=200)

    if bundle.created_by_id != request.user.id:
        return JsonResponse({"detail": "Only owners can manage share grants."}, status=403)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    username = (body.get("username") or "").strip()
    if not username:
        return JsonResponse({"detail": "username is required."}, status=400)

    permission = (body.get("permission") or SemanticBundleShare.PERMISSION_VIEW).strip().lower()
    if permission not in {SemanticBundleShare.PERMISSION_VIEW, SemanticBundleShare.PERMISSION_EDIT}:
        return JsonResponse({"detail": "permission must be view or edit."}, status=400)

    user_model = get_user_model()
    target_user = user_model.objects.filter(username=username).first()
    if not target_user:
        return JsonResponse({"detail": "Target user not found."}, status=404)
    if target_user.id == request.user.id:
        return JsonResponse({"detail": "Owner already has full access."}, status=400)

    share, created = SemanticBundleShare.objects.get_or_create(
        bundle=bundle,
        user=target_user,
        defaults={
            "permission": permission,
            "is_active": bool(body.get("is_active", True)),
            "created_by": request.user,
        },
    )
    if not created:
        share.permission = permission
        share.is_active = bool(body.get("is_active", True))
        share.created_by = request.user
        share.save(update_fields=["permission", "is_active", "created_by", "updated_at"])

    return JsonResponse(
        {
            "share": {
                "username": share.user.username,
                "permission": share.permission,
                "is_active": share.is_active,
                "updated_at": share.updated_at.isoformat(),
            }
        },
        status=201 if created else 200,
    )


@require_http_methods(["DELETE"])
def preset_bundle_delete_view(request, bundle_name: str):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    bundle = SemanticBundle.objects.filter(name=bundle_name).first()
    if not bundle:
        return JsonResponse({"detail": "Bundle not found."}, status=404)
    if bundle.created_by_id != request.user.id:
        return JsonResponse({"detail": "You do not own this bundle."}, status=403)

    deleted, _ = SemanticBundle.objects.filter(name=bundle_name, created_by=request.user).delete()
    if not deleted:
        return JsonResponse({"detail": "Bundle not found."}, status=404)
    return JsonResponse({"deleted": bundle_name}, status=200)


@require_http_methods(["GET"])
def slide_detail_view(request, slide_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    slide = Slide.objects.filter(pk=slide_id).first()
    if not slide:
        return JsonResponse({"detail": "Slide not found."}, status=404)

    return JsonResponse(_slide_payload(slide), status=200)


@require_http_methods(["POST"])
def slide_apply_preset_view(request, slide_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    slide = Slide.objects.filter(pk=slide_id).first()
    if not slide:
        return JsonResponse({"detail": "Slide not found."}, status=404)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    preset_name = (body.get("preset") or body.get("preset_name") or "").strip()
    if not preset_name:
        return JsonResponse({"detail": "preset or preset_name is required."}, status=400)

    slide, error = _apply_preset_name_to_slide(slide, preset_name, body=body)
    if error:
        return error

    slide.save()
    return JsonResponse(_slide_payload(slide), status=200)


@require_http_methods(["POST"])
def slide_generate_bundle_view(request, slide_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=403)

    base_slide = Slide.objects.filter(pk=slide_id).first()
    if not base_slide:
        return JsonResponse({"detail": "Slide not found."}, status=404)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    bundle_name = (body.get("bundle") or "").strip()
    inversion_mode = (body.get("inversion") or "none").strip().lower()
    persist_generated = bool(body.get("persist_generated", True))
    bundle, error = _normalize_bundle_request(bundle_name, body, request.user)
    if error:
        return error

    generated_slides = []
    sequence = bundle.get("sequence") or []
    for index, preset_name in enumerate(sequence, start=1):
        effective_preset_name = preset_name
        if inversion_mode == "executive":
            phase = _phase_for_preset_name(preset_name)
            effective_preset_name = PHASE_TO_EXECUTIVE_ALIAS.get((phase or "").lower(), preset_name)

        cloned_slide = Slide.objects.get(pk=base_slide.pk)
        cloned_slide.pk = None
        cloned_slide.title = f"{base_slide.title} · {bundle.get('name')} · {index}"
        cloned_slide.applied_preset = None

        cloned_slide, error = _apply_preset_name_to_slide(cloned_slide, effective_preset_name, body={})
        if error:
            return error

        if persist_generated:
            cloned_slide.save()
        generated_slides.append(
            {
                "sequence": index,
                "bundle_preset": preset_name,
                "effective_preset": effective_preset_name,
                "slide": _slide_payload(cloned_slide),
            }
        )

    return JsonResponse(
        {
            "bundle": bundle.get("name"),
            "label": bundle.get("label"),
            "family": bundle.get("family"),
            "description": bundle.get("description"),
            "inversion": inversion_mode,
            "persist_generated": persist_generated,
            "source_slide_id": base_slide.id,
            "metadata": _bundle_metadata(bundle),
            "generated": generated_slides,
        },
        status=200,
    )
