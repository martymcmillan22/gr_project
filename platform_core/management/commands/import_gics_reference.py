from django.core.management.base import BaseCommand

from platform_reference.services.reference_import import import_gics_csv


class Command(BaseCommand):
    help = "Import licensed GICS CSV into GICSReference table."

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
        result = import_gics_csv(raw_path)
        self.stdout.write(
            self.style.SUCCESS(
                f"GICS reference import complete: created={result['created']}, updated={result['updated']}"
            )
        )
