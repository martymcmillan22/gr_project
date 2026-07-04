import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from platform_core.models import NAICSReference


class Command(BaseCommand):
    help = "Load NAICS reference snapshot from CSV into NAICSReference table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="",
            help="Optional CSV path. Defaults to platform_core/data/naics_reference_snapshot.csv",
        )

    def handle(self, *args, **options):
        default_path = Path(__file__).resolve().parents[2] / "data" / "naics_reference_snapshot.csv"
        file_path = Path(options["file"]).expanduser().resolve() if options.get("file") else default_path
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
                _, is_created = NAICSReference.objects.update_or_create(code=code, defaults=payload)
                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"NAICS reference sync complete: created={created}, updated={updated}"))
