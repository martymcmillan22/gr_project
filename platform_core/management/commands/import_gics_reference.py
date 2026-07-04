import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from platform_core.models import GICSReference


class Command(BaseCommand):
    help = "Import licensed GICS CSV into GICSReference table."

    PLACEHOLDER_HINTS = (
        "/absolute/path/",
        "/users/you/path/",
        "<path>",
        "your_gics.csv",
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "filepath",
            nargs="?",
            default="",
            help="Path to licensed GICS CSV file (positional alternative to --file).",
        )
        parser.add_argument(
            "--file",
            default="",
            help="Path to licensed GICS CSV file.",
        )

    def handle(self, *args, **options):
        raw_path = options.get("file") or options.get("filepath") or ""
        if not raw_path:
            raise CommandError("Provide a GICS CSV path using --file <path> or positional filepath.")

        normalized_raw_path = raw_path.strip().lower()
        if any(hint in normalized_raw_path for hint in self.PLACEHOLDER_HINTS):
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
                _, is_created = GICSReference.objects.update_or_create(code=code, level=level, defaults=payload)
                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"GICS reference import complete: created={created}, updated={updated}"))
