from platform_core.resolvers.quadrant import AM_DOMAINS
from platform_core.resolvers.quadrant import PM_DOMAINS
from platform_core.resolvers.quadrant import get_current_hour
from platform_core.resolvers.quadrant import is_pm
from platform_core.resolvers.quadrant import resolve_domain
from platform_core.resolvers.quadrant import resolve_url
from platform_reference.services.reference_sync import get_gics_source_status

from platform_quadrant.models import GICSReference
from platform_quadrant.models import MLASClassificationRecord
from platform_quadrant.models import NAICSReference
from platform_quadrant.models import SemanticBundle
from platform_quadrant.models import SemanticBundleRevision
from platform_quadrant.models import SemanticPreset
from platform_quadrant.models import Slide


def _resolver_matrix() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for hour in range(1, 13):
        rows.append(
            {
                "hour": hour,
                "am_slug": AM_DOMAINS[hour],
                "pm_slug": PM_DOMAINS[hour],
            }
        )
    return rows


def get_quadrant_activation_payload() -> dict[str, object]:
    current_hour = get_current_hour()
    current_is_pm = is_pm()
    current_slug = resolve_domain(hour=current_hour, pm=current_is_pm)
    current_url = resolve_url(hour=current_hour, pm=current_is_pm)

    gics_total = GICSReference.objects.count()
    naics_total = NAICSReference.objects.count()
    gics_source_status = get_gics_source_status()

    semantic_bundles = SemanticBundle.objects.count()
    semantic_revisions = SemanticBundleRevision.objects.count()
    semantic_presets = SemanticPreset.objects.count()
    semantic_slides = Slide.objects.count()

    classified_total = MLASClassificationRecord.objects.count()
    classified_with_quadrant = MLASClassificationRecord.objects.exclude(quadrant_slug="").count()
    classified_with_gics = MLASClassificationRecord.objects.exclude(gics_sub_industry_code="").count()
    classified_with_naics = MLASClassificationRecord.objects.exclude(naics_code_6="").count()

    reference_ready = gics_total > 0 and naics_total > 0 and gics_source_status != "missing"
    semantic_ready = semantic_bundles > 0 and semantic_revisions > 0 and semantic_presets > 0 and semantic_slides > 0
    routing_ready = classified_with_quadrant > 0 or classified_total == 0

    capability_flags = {
        "industry_hierarchy": reference_ready,
        "temporal_slots": True,
        "semantic_bundle_routing": semantic_ready,
        "reference_truth_binding": reference_ready,
        "deterministic_quadrant_routing": reference_ready and semantic_ready and routing_ready,
    }

    return {
        "app": "platform_quadrant",
        "boundary": "quadrant-services",
        "status": "active",
        "resolver_clock": {
            "hour": current_hour,
            "is_pm": current_is_pm,
            "slug": current_slug,
            "url": current_url,
        },
        "resolver_catalog": {
            "am_domains": AM_DOMAINS,
            "pm_domains": PM_DOMAINS,
            "matrix": _resolver_matrix(),
        },
        "reference_truth": {
            "gics_source_status": gics_source_status,
            "gics_total": gics_total,
            "naics_total": naics_total,
        },
        "semantic_truth": {
            "bundles": semantic_bundles,
            "revisions": semantic_revisions,
            "presets": semantic_presets,
            "slides": semantic_slides,
        },
        "classification_truth": {
            "total": classified_total,
            "quadrant_mapped": classified_with_quadrant,
            "gics_mapped": classified_with_gics,
            "naics_mapped": classified_with_naics,
        },
        "capability_flags": capability_flags,
        "deterministic_ready": all(capability_flags.values()),
    }
