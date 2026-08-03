from django.core.management.base import BaseCommand, CommandError

from platform_reference.services.reference_sync import get_gics_source_status, is_production_environment


class Command(BaseCommand):
    help = "Gate production promotion when GICS reference is not licensed."

    def add_arguments(self, parser):
        parser.add_argument(
            "--enforce-production",
            action="store_true",
            help="Treat current run as production regardless of env settings.",
        )

    def handle(self, *args, **options):
        enforce_production = bool(options.get("enforce_production", False))
        production = enforce_production or is_production_environment()
        gics_status = get_gics_source_status()

        if production and gics_status != "licensed":
            raise CommandError(
                "Promotion gate failed: production requires licensed GICS reference data "
                f"(current status: {gics_status})."
            )

        if production:
            self.stdout.write(self.style.SUCCESS("Promotion gate passed: licensed GICS reference data detected."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                "Promotion gate skipped: non-production environment detected "
                f"(current GICS status: {gics_status})."
            )
        )