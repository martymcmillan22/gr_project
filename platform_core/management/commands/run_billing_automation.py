from django.core.management.base import BaseCommand

from platform_core.unified_admin import _enqueue_billing_job, _process_pending_billing_jobs


class Command(BaseCommand):
    help = "Queue and process billing operational automation jobs."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default="default")
        parser.add_argument("--client", default="all")
        parser.add_argument("--window-days", type=int, default=30)
        parser.add_argument("--schedule-hint", default="hourly")
        parser.add_argument("--limit", type=int, default=25)
        parser.add_argument(
            "--queue-only",
            action="store_true",
            help="Queue the automation job without processing pending jobs.",
        )

    def handle(self, *args, **options):
        tenant = (options.get("tenant") or "default").strip() or "default"
        client = (options.get("client") or "all").strip() or "all"
        window_days = int(options.get("window_days") or 30)
        schedule_hint = (options.get("schedule_hint") or "hourly").strip() or "hourly"
        limit = int(options.get("limit") or 25)
        queue_only = bool(options.get("queue_only"))

        job = _enqueue_billing_job(
            job_type="automation",
            tenant_key=tenant,
            client_key=client,
            payload={
                "tenant": tenant,
                "client": client,
                "window_days": window_days,
                "schedule_hint": schedule_hint,
            },
            requested_by=None,
        )
        if not job:
            self.stderr.write(self.style.ERROR("Failed to queue billing automation job."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Queued billing automation job #{job.id} for tenant={tenant} client={client}."
            )
        )

        if queue_only:
            return

        processed_jobs = _process_pending_billing_jobs(limit=limit)
        processed_ids = [pending_job.id for pending_job in processed_jobs]
        if job.id not in processed_ids:
            self.stdout.write(
                self.style.WARNING(
                    f"Queued job #{job.id} not processed in this run. Increase --limit if needed."
                )
            )
            return

        refreshed = type(job).objects.filter(id=job.id).first()
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed job #{job.id} with status={getattr(refreshed, 'status', 'unknown')}."
            )
        )
