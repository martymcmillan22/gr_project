import csv
from pathlib import Path

from django.core.management.base import CommandError

from platform_reference.models import GICSReference
from platform_reference.models import PlatformReferenceGICSReferenceSchema
from platform_reference.models import PlatformReferenceNAICSReferenceSchema

from .reference_validation import PLACEHOLDER_HINTS


def import_gics_csv(raw_path: str):
    """Import licensed GICS CSV rows into platform_reference GICS schema rows and return counts."""
    if not raw_path:
        raise CommandError("Provide a GICS CSV path using --file <path> or positional filepath.")

    normalized_raw_path = raw_path.strip().lower()
    if any(hint in normalized_raw_path for hint in PLACEHOLDER_HINTS):
        raise CommandError(
            "Detected placeholder path. Use your actual licensed file path, e.g. "
            "python manage.py import_gics_reference --file /Users/martymcmillan/Downloads/gics.csv"
        )

    file_path = Path(raw_path).expanduser().resolve()
    if not file_path.exists():
        raise CommandError(f"GICS file not found: {file_path}")

    created = 0
    updated = 0

    with file_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"code", "name", "level", "parent_code", "description", "source_version"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise CommandError(
                "GICS CSV missing required columns: code,name,level,parent_code,description,source_version"
            )

        allowed_levels = {
            GICSReference.LEVEL_SECTOR,
            GICSReference.LEVEL_INDUSTRY_GROUP,
            GICSReference.LEVEL_INDUSTRY,
            GICSReference.LEVEL_SUB_INDUSTRY,
        }

        for row in reader:
            code = (row.get("code") or "").strip()
            level = (row.get("level") or "").strip().lower()
            if not code:
                continue
            if level not in allowed_levels:
                raise CommandError(f"Unsupported GICS level '{level}' for code {code}")

            payload = {
                "name": (row.get("name") or "").strip(),
                "parent_code": (row.get("parent_code") or "").strip(),
                "description": (row.get("description") or "").strip(),
                "source_version": (row.get("source_version") or "").strip(),
                "is_active": True,
            }
            _, is_created = PlatformReferenceGICSReferenceSchema.objects.update_or_create(
                code=code,
                level=level,
                defaults=payload,
            )
            if is_created:
                created += 1
            else:
                updated += 1

    return {"created": created, "updated": updated}


def load_naics_snapshot_csv(raw_path: str = ""):
    """Load a NAICS snapshot CSV into platform_reference schema rows and return created/updated counts."""
    default_path = Path(__file__).resolve().parents[2] / "platform_core" / "data" / "naics_reference_snapshot.csv"
    file_path = Path(raw_path).expanduser().resolve() if raw_path else default_path
    if not file_path.exists():
        raise CommandError(f"NAICS snapshot file not found: {file_path}")

    created = 0
    updated = 0

    with file_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"code", "title", "sector_code", "description", "source_version"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise CommandError(
                "NAICS CSV missing required columns: code,title,sector_code,description,source_version"
            )

        for row in reader:
            code = (row.get("code") or "").strip()
            if not code:
                continue
            payload = {
                "title": (row.get("title") or "").strip(),
                "sector_code": (row.get("sector_code") or "").strip(),
                "description": (row.get("description") or "").strip(),
                "source_version": (row.get("source_version") or "").strip(),
                "is_active": True,
            }
            _, is_created = PlatformReferenceNAICSReferenceSchema.objects.update_or_create(
                code=code,
                defaults=payload,
            )
            if is_created:
                created += 1
            else:
                updated += 1

    return {"created": created, "updated": updated}
