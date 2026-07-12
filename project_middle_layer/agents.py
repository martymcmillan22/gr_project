from __future__ import annotations

from project_middle_layer.analytics import build_semantic_analytics_snapshot
from project_middle_layer.insights import build_semantic_insights
from project_middle_layer.models import SemanticAgentRun, SemanticPipeline, SemanticSchedule
from project_middle_layer.pipelines import run_semantic_pipeline
from project_middle_layer.schedules import run_semantic_schedule


AGENT_NAMES = [
    "Drift Agent",
    "Stability Agent",
    "Lineage Agent",
    "Tag Agent",
    "Evolution Agent",
]


def _trigger_first_active_pipeline(*, triggered_by: str) -> dict[str, object]:
    pipeline = SemanticPipeline.objects.filter(is_active=True).order_by("name").first()
    if not pipeline:
        return {"triggered": False, "reason": "no_active_pipeline"}

    run = run_semantic_pipeline(pipeline, triggered_by=triggered_by)
    return {
        "triggered": True,
        "pipeline_slug": pipeline.slug,
        "run_id": run.id,
        "status": run.status,
        "error_message": run.error_message,
    }


def _trigger_first_active_schedule(*, triggered_by: str) -> dict[str, object]:
    schedule = SemanticSchedule.objects.filter(is_paused=False).order_by("name").first()
    if not schedule:
        return {"triggered": False, "reason": "no_active_schedule"}

    run = run_semantic_schedule(schedule, triggered_by=triggered_by)
    return {
        "triggered": True,
        "schedule_slug": schedule.slug,
        "run_id": run.id,
        "status": run.status,
        "error_message": run.error_message,
    }


def run_semantic_agent(agent_name: str) -> SemanticAgentRun:
    if agent_name not in AGENT_NAMES:
        raise ValueError(f"Unknown semantic agent: {agent_name}")

    actions_taken = []
    insights_generated = []

    try:
        analytics_snapshot = build_semantic_analytics_snapshot(triggered_by=f"agent:{agent_name}")
        actions_taken.append({"action": "analytics_snapshot", "snapshot_id": analytics_snapshot.id})

        insights = build_semantic_insights(limit=8)
        insights_generated.extend(insights)
        actions_taken.append({"action": "insights_refresh", "insight_count": len(insights)})

        if agent_name == "Drift Agent" and analytics_snapshot.drift_mean >= 0.55:
            actions_taken.append(
                {
                    "action": "pipeline_trigger",
                    **_trigger_first_active_pipeline(triggered_by=f"agent:{agent_name}"),
                }
            )

        if agent_name == "Stability Agent" and analytics_snapshot.stability_mean < 60:
            actions_taken.append(
                {
                    "action": "schedule_trigger",
                    **_trigger_first_active_schedule(triggered_by=f"agent:{agent_name}"),
                }
            )

        if agent_name == "Lineage Agent" and len(analytics_snapshot.lineage_cluster_map or {}) >= 4:
            actions_taken.append(
                {
                    "action": "pipeline_trigger",
                    **_trigger_first_active_pipeline(triggered_by=f"agent:{agent_name}"),
                }
            )

        if agent_name == "Tag Agent":
            hot_tags = sorted((analytics_snapshot.tag_frequency_map or {}).items(), key=lambda item: item[1], reverse=True)[:5]
            actions_taken.append(
                {
                    "action": "tag_normalization_scan",
                    "hot_tags": hot_tags,
                    "triggered": bool(hot_tags),
                }
            )

        if agent_name == "Evolution Agent" and analytics_snapshot.drift_mean >= 0.45 and analytics_snapshot.confidence_mean < 70:
            actions_taken.append(
                {
                    "action": "schedule_trigger",
                    **_trigger_first_active_schedule(triggered_by=f"agent:{agent_name}"),
                }
            )

        return SemanticAgentRun.objects.create(
            agent_name=agent_name,
            status="completed",
            actions_taken=actions_taken,
            insights_generated=insights_generated,
        )
    except Exception as exc:
        return SemanticAgentRun.objects.create(
            agent_name=agent_name,
            status="failed",
            actions_taken=actions_taken,
            insights_generated=insights_generated,
            error_message=str(exc),
        )
