from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from project_middle_layer.exports import build_semantic_export_payload
from project_middle_layer.models import SemanticAlert, SemanticSchedule, SemanticScheduleRun
from project_middle_layer.pipelines import run_semantic_pipeline
from project_middle_layer.webhooks import dispatch_semantic_webhook_event


def _parse_cron_to_next_run(cron_expression: str, *, base_time=None):
    now = base_time or timezone.now()
    expr = (cron_expression or "").strip()
    if expr.startswith("*/") and expr.endswith(" * * * *"):
        minutes_str = expr[2:].split(" ", 1)[0]
        try:
            minutes = int(minutes_str)
            if minutes > 0:
                return now + timedelta(minutes=minutes)
        except ValueError:
            return now + timedelta(hours=24)
    return now + timedelta(hours=24)


def run_semantic_schedule(schedule: SemanticSchedule, *, triggered_by: str = "manual") -> SemanticScheduleRun:
    if schedule.is_paused:
        run = SemanticScheduleRun.objects.create(
            schedule=schedule,
            status="failed",
            triggered_by=triggered_by,
            result={"status": "failed"},
            error_message="Schedule is paused.",
            completed_at=timezone.now(),
        )
        return run

    schedule.status = "running"
    schedule.save(update_fields=["status", "updated_at"])

    run = SemanticScheduleRun.objects.create(
        schedule=schedule,
        status="running",
        triggered_by=triggered_by,
        result={"status": "running"},
    )

    try:
        action = schedule.action
        payload = schedule.payload if isinstance(schedule.payload, dict) else {}

        if action == "pipeline-run":
            if not schedule.pipeline_id:
                raise ValueError("Schedule action 'pipeline-run' requires a linked pipeline.")
            pipeline_run = run_semantic_pipeline(schedule.pipeline, triggered_by=triggered_by)
            result = {
                "pipeline_slug": schedule.pipeline.slug,
                "pipeline_run_id": pipeline_run.id,
                "pipeline_status": pipeline_run.status,
                "pipeline_error": pipeline_run.error_message,
            }
            if pipeline_run.status != "completed":
                raise ValueError(pipeline_run.error_message or "Pipeline run failed.")
        elif action == "export":
            export_payload = build_semantic_export_payload(
                scope=str(payload.get("scope") or "all"),
                project_slug=str(payload.get("project_slug") or "") or None,
                include_history=bool(payload.get("include_history", False)),
                max_items=int(payload.get("max_items") or 100),
                exported_by=triggered_by,
            )
            result = {"summary": export_payload.get("summary", {})}
        elif action == "alert-check":
            alert_qs = SemanticAlert.objects.all()
            result = {
                "total_alerts": alert_qs.count(),
                "high_alerts": alert_qs.filter(severity="high").count(),
                "critical_alerts": alert_qs.filter(severity="critical").count(),
            }
        else:
            raise ValueError(f"Unsupported schedule action: {action}")

        now = timezone.now()
        run.status = "completed"
        run.completed_at = now
        run.result = {"status": "completed", "action": action, "result": result}
        run.error_message = ""

        schedule.status = "completed"
        schedule.last_run = now
        schedule.next_run = _parse_cron_to_next_run(schedule.cron_expression, base_time=now)
        schedule.save(update_fields=["status", "last_run", "next_run", "updated_at"])
        dispatch_semantic_webhook_event(
            event_type="schedule.completed",
            payload={
                "schedule": {
                    "id": schedule.id,
                    "slug": schedule.slug,
                    "name": schedule.name,
                    "action": schedule.action,
                },
                "run": {
                    "id": run.id,
                    "status": run.status,
                },
            },
        )
    except Exception as exc:
        now = timezone.now()
        run.status = "failed"
        run.completed_at = now
        run.result = {"status": "failed", "action": schedule.action}
        run.error_message = str(exc)

        schedule.status = "failed"
        schedule.last_run = now
        schedule.next_run = _parse_cron_to_next_run(schedule.cron_expression, base_time=now)
        schedule.save(update_fields=["status", "last_run", "next_run", "updated_at"])
        dispatch_semantic_webhook_event(
            event_type="schedule.failed",
            payload={
                "schedule": {
                    "id": schedule.id,
                    "slug": schedule.slug,
                    "name": schedule.name,
                    "action": schedule.action,
                },
                "run": {
                    "id": run.id,
                    "status": run.status,
                    "error_message": run.error_message,
                },
            },
        )

    run.save(update_fields=["status", "completed_at", "result", "error_message"])
    return run
