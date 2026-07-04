from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from platform_core.presentation_mdx import sync_presentation_blueprints


class Command(BaseCommand):
    help = "Parse MDX UI blueprints and generate React components/pages."

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        summary = sync_presentation_blueprints(base_dir)
        for warning in summary.get("validation_warnings", []):
            self.stdout.write(self.style.WARNING(f"[presentation warning] {warning}"))
        self.stdout.write(
            self.style.SUCCESS(
                "Generated presentation UI artifacts: "
                f"slides={summary['slide_count']} tags={summary['tag_count']} "
                f"architecture_out={summary['generated_dir']} frontend_out={summary['frontend_generated_dir']}"
            )
        )
