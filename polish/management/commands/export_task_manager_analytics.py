from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from polish.views import (
    _build_operational_metrics_csv,
    _build_operational_metrics_pdf,
    _build_task_manager_metrics,
)
from polish.task_manager.models import TaskManagerAnalyticsExportRun


class Command(BaseCommand):
    help = "Export Task Manager operational analytics as CSV and PDF files (weekly schedule compatible)."

    def add_arguments(self, parser):
        parser.add_argument("--email", action="append", help="Target user email (repeat for multiple users).")
        parser.add_argument(
            "--all-staff",
            action="store_true",
            help="Export reports for all staff users.",
        )
        parser.add_argument(
            "--output-dir",
            default="exports/task_manager/weekly",
            help="Output directory for generated reports (relative to BASE_DIR if not absolute).",
        )

    def handle(self, *args, **options):
        emails = options.get("email") or []
        all_staff = options.get("all_staff")
        output_dir = options.get("output_dir")

        User = get_user_model()
        queryset = User.objects.none()

        if all_staff:
            queryset = User.objects.filter(is_staff=True)
        elif emails:
            queryset = User.objects.filter(email__in=emails)
        else:
            raise CommandError("Provide --all-staff or at least one --email value.")

        users = list(queryset)
        if not users:
            raise CommandError("No users matched export target parameters.")

        output_path = Path(output_dir)
        if not output_path.is_absolute():
            output_path = Path(settings.BASE_DIR) / output_path
        output_path.mkdir(parents=True, exist_ok=True)

        date_token = timezone.now().date().isoformat()
        exported_count = 0
        failed_count = 0

        for user in users:
            try:
                metrics = _build_task_manager_metrics(user)
                csv_content = _build_operational_metrics_csv(metrics)
                pdf_buffer = _build_operational_metrics_pdf(
                    metrics,
                    generated_for=user.username or user.email or f"user-{user.pk}",
                )

                user_token = (user.username or user.email or f"user-{user.pk}").replace("@", "_").replace("/", "_")
                csv_file = output_path / f"task_manager_ops_{user_token}_{date_token}.csv"
                pdf_file = output_path / f"task_manager_ops_{user_token}_{date_token}.pdf"

                csv_file.write_text(csv_content, encoding="utf-8")
                with pdf_file.open("wb") as handle:
                    handle.write(pdf_buffer.getvalue())

                TaskManagerAnalyticsExportRun.objects.create(
                    requested_by=None,
                    target_user=user,
                    trigger_source=TaskManagerAnalyticsExportRun.SOURCE_COMMAND,
                    export_format=TaskManagerAnalyticsExportRun.FORMAT_BOTH,
                    status=TaskManagerAnalyticsExportRun.STATUS_SUCCESS,
                    output_dir=str(output_path),
                    artifact_paths=f"{csv_file.name};{pdf_file.name}",
                    notes="Weekly scheduled analytics export command run.",
                    completed_at=timezone.now(),
                )

                exported_count += 1
                self.stdout.write(self.style.SUCCESS(f"Exported reports for {user.email} -> {csv_file.name}, {pdf_file.name}"))
            except Exception as exc:
                failed_count += 1
                TaskManagerAnalyticsExportRun.objects.create(
                    requested_by=None,
                    target_user=user,
                    trigger_source=TaskManagerAnalyticsExportRun.SOURCE_COMMAND,
                    export_format=TaskManagerAnalyticsExportRun.FORMAT_BOTH,
                    status=TaskManagerAnalyticsExportRun.STATUS_FAILED,
                    output_dir=str(output_path),
                    artifact_paths="",
                    notes="Weekly scheduled analytics export command failed.",
                    error_message=str(exc),
                    completed_at=timezone.now(),
                )
                self.stderr.write(self.style.ERROR(f"Failed export for {user.email}: {exc}"))

        self.stdout.write(self.style.SUCCESS(f"Completed {exported_count} Task Manager analytics export(s)."))
        if failed_count:
            raise CommandError(f"{failed_count} Task Manager analytics export(s) failed.")
