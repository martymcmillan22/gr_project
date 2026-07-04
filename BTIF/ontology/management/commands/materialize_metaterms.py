from django.core.management.base import BaseCommand
from django.db import transaction

from ontology.models import SubIndustry


META_TERM_SUFFIXES = {
    1: "Foundations",
    2: "Operations",
    3: "Intelligence",
    4: "Governance",
}


def should_replace_name(name):
    return " Sub " in name and name.rsplit(" ", 1)[-1].isdigit()


class Command(BaseCommand):
    help = "Replace placeholder sub-industry names with deterministic meta-term names."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Rewrite all sub-industry names.")
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing.")

    @transaction.atomic
    def handle(self, *args, **options):
        force = options["force"]
        dry_run = options["dry_run"]
        changed = 0

        for sub in SubIndustry.objects.select_related("industry").order_by("industry__name", "order"):
            if not force and not should_replace_name(sub.name):
                continue

            suffix = META_TERM_SUFFIXES[sub.order]
            new_name = f"{sub.industry.name} {suffix}"
            if sub.name == new_name:
                continue

            changed += 1
            if not dry_run:
                sub.name = new_name
                sub.save(update_fields=["name"])

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run complete. {changed} rows would be updated."))
            transaction.set_rollback(True)
            return

        self.stdout.write(self.style.SUCCESS(f"Meta-terms materialized. Updated rows: {changed}"))