from django.core.management.base import BaseCommand

from platform_reference.services.reference_validation import validate_gics_csv


class Command(BaseCommand):
    help = "Validate licensed GICS CSV structure via platform_reference service layer."

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
        result = validate_gics_csv(raw_path)
        breakdown = ", ".join(
            [
                f"sector={result['sector']}",
                f"industry_group={result['industry_group']}",
                f"industry={result['industry']}",
                f"sub_industry={result['sub_industry']}",
            ]
        )
        self.stdout.write(self.style.SUCCESS(f"GICS CSV validation passed: rows={result['rows']} ({breakdown})"))
