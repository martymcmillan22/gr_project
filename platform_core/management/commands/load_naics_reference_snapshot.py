from django.core.management.base import BaseCommand

from platform_reference.services.reference_import import load_naics_snapshot_csv


class Command(BaseCommand):
    help = "Load NAICS reference snapshot from CSV into NAICSReference table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="",
            help="Optional CSV path. Defaults to platform_core/data/naics_reference_snapshot.csv",
        )

    def handle(self, *args, **options):
        result = load_naics_snapshot_csv(options.get("file") or "")
        self.stdout.write(
            self.style.SUCCESS(
                f"NAICS reference sync complete: created={result['created']}, updated={result['updated']}"
            )
        )
