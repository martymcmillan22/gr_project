import os

from platform_reference.models import PlatformReferenceGICSReferenceSchema


DEMO_SOURCE_HINTS = (
    "demo",
    "unlicensed",
    "template",
)

PRODUCTION_ENV_HINTS = {
    "prod",
    "production",
    "live",
}


def is_demo_gics_source(source_version: str) -> bool:
    value = str(source_version or "").strip().lower()
    if not value:
        return True
    return any(hint in value for hint in DEMO_SOURCE_HINTS)


def get_gics_source_status() -> str:
    gics_ref_count = PlatformReferenceGICSReferenceSchema.objects.count()
    if gics_ref_count == 0:
        return "missing"

    source_versions = list(
        PlatformReferenceGICSReferenceSchema.objects.exclude(source_version="")
        .values_list("source_version", flat=True)
        .distinct()
    )

    if any(not is_demo_gics_source(version) for version in source_versions):
        return "licensed"
    return "demo"


def is_production_environment() -> bool:
    env_candidates = [
        os.getenv("DJANGO_ENV", ""),
        os.getenv("ENVIRONMENT", ""),
        os.getenv("APP_ENV", ""),
    ]
    for candidate in env_candidates:
        if str(candidate or "").strip().lower() in PRODUCTION_ENV_HINTS:
            return True

    from django.conf import settings

    return not bool(getattr(settings, "DEBUG", True))
