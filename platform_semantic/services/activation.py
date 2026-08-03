from django.db.models import Count

from platform_reference.services.reference_sync import get_gics_source_status

from platform_semantic.models import GICSReference
from platform_semantic.models import MLASClassificationRecord
from platform_semantic.models import NAICSReference
from platform_semantic.models import SemanticBundle
from platform_semantic.models import SemanticBundleRevision
from platform_semantic.models import SemanticBundleRevisionTag
from platform_semantic.models import SemanticPreset
from platform_semantic.models import Slide


def _phase_catalog() -> dict[str, int]:
    rows = SemanticPreset.objects.values("phase").annotate(total=Count("id"))
    return {row["phase"]: row["total"] for row in rows}


def _bundle_family_catalog() -> dict[str, int]:
    rows = SemanticBundle.objects.values("family").annotate(total=Count("id"))
    return {row["family"]: row["total"] for row in rows}


def _ui_category_catalog() -> dict[str, int]:
    rows = Slide.objects.values("ui_category_resolved").annotate(total=Count("id"))
    return {row["ui_category_resolved"]: row["total"] for row in rows}


def get_semantic_activation_payload() -> dict[str, object]:
    approved_status = MLASClassificationRecord.REVIEW_APPROVED
    term_target = MLASClassificationRecord.TARGET_TERM

    total_presets = SemanticPreset.objects.count()
    total_slides = Slide.objects.count()
    total_bundles = SemanticBundle.objects.count()
    total_revisions = SemanticBundleRevision.objects.count()
    total_tags = SemanticBundleRevisionTag.objects.count()

    gics_total = GICSReference.objects.count()
    gics_sub_industry_count = GICSReference.objects.filter(
        level=GICSReference.LEVEL_SUB_INDUSTRY
    ).count()
    naics_total = NAICSReference.objects.count()

    approved_classifications = MLASClassificationRecord.objects.filter(
        review_status=approved_status
    ).count()
    approved_term_classifications = MLASClassificationRecord.objects.filter(
        review_status=approved_status,
        target_layer=term_target,
    ).count()

    gics_mapped_classifications = MLASClassificationRecord.objects.exclude(
        gics_sub_industry_code=""
    ).count()
    naics_mapped_classifications = MLASClassificationRecord.objects.exclude(
        naics_code_6=""
    ).count()

    gics_source_status = get_gics_source_status()
    has_reference_truth = gics_total > 0 and naics_total > 0 and gics_source_status != "missing"

    capability_flags = {
        "semantic_pipelines": has_reference_truth and total_presets > 0,
        "semantic_schedules": total_bundles > 0 and total_revisions > 0,
        "semantic_analytics": has_reference_truth and approved_classifications > 0,
        "semantic_merge": total_bundles > 0 and total_tags > 0,
        "semantic_versioning": total_revisions > 0,
    }

    return {
        "app": "platform_semantic",
        "boundary": "semantic-services",
        "status": "active",
        "semantic_assets": {
            "presets": total_presets,
            "slides": total_slides,
            "bundles": total_bundles,
            "revisions": total_revisions,
            "revision_tags": total_tags,
        },
        "reference_truth": {
            "gics_source_status": gics_source_status,
            "gics_total": gics_total,
            "gics_sub_industry": gics_sub_industry_count,
            "naics_total": naics_total,
        },
        "classification_truth": {
            "approved_total": approved_classifications,
            "approved_term_total": approved_term_classifications,
            "gics_mapped": gics_mapped_classifications,
            "naics_mapped": naics_mapped_classifications,
        },
        "semantic_catalogs": {
            "phase": _phase_catalog(),
            "bundle_family": _bundle_family_catalog(),
            "ui_category_resolved": _ui_category_catalog(),
        },
        "capability_flags": capability_flags,
        "deterministic_ready": all(capability_flags.values()),
    }
