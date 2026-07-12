from __future__ import annotations

from project_middle_layer.analytics import build_semantic_analytics_dashboard
from project_middle_layer.models import ProjectEvolutionSnapshot, SemanticPipelineRun, SemanticScheduleRun


def build_semantic_insights(*, limit: int = 12) -> list[dict[str, object]]:
    dashboard = build_semantic_analytics_dashboard(limit=30)
    latest = dashboard.get("latest")
    trend_points = dashboard.get("trend_points", [])

    insights: list[dict[str, object]] = []

    if latest and latest.drift_mean >= 0.45 and latest.confidence_mean >= 65:
        insights.append(
            {
                "code": "rising_drift_stable_confidence",
                "title": "Rising drift with stable confidence",
                "detail": "Global drift is elevated while confidence remains stable.",
                "severity": "medium",
            }
        )

    if latest and latest.stability_mean < 65:
        insights.append(
            {
                "code": "stability_drop",
                "title": "System stability drop",
                "detail": "Average stability has fallen below watch threshold.",
                "severity": "high",
            }
        )

    if latest and isinstance(latest.tag_frequency_map, dict):
        hot_tags = sorted(latest.tag_frequency_map.items(), key=lambda item: item[1], reverse=True)[:3]
        if hot_tags:
            insights.append(
                {
                    "code": "top_tags",
                    "title": "Top semantic tags",
                    "detail": ", ".join(f"{label} ({count})" for label, count in hot_tags),
                    "severity": "low",
                }
            )

    if len(trend_points) >= 2:
        first = trend_points[0]
        last = trend_points[-1]
        drift_delta = float(last.get("drift_mean", 0.0)) - float(first.get("drift_mean", 0.0))
        if drift_delta >= 0.1:
            insights.append(
                {
                    "code": "drift_trend_up",
                    "title": "Drift trend increasing",
                    "detail": f"Drift mean increased by {drift_delta:.2f} across recent snapshots.",
                    "severity": "medium",
                }
            )

    recent_snapshots = list(ProjectEvolutionSnapshot.objects.select_related("project")[:200])
    risky_projects = [item for item in recent_snapshots if float(item.drift_risk or 0.0) >= 0.6]
    if risky_projects:
        unique_projects = sorted({item.project.slug for item in risky_projects})[:5]
        insights.append(
            {
                "code": "high_risk_projects",
                "title": "Projects with high drift",
                "detail": ", ".join(unique_projects),
                "severity": "high",
            }
        )

    ordered = list(
        ProjectEvolutionSnapshot.objects.select_related("project").order_by("project_id", "created_at", "id")[:2000]
    )
    considered = 0
    improved = 0
    for index in range(1, len(ordered)):
        previous = ordered[index - 1]
        current = ordered[index]
        if previous.project_id != current.project_id:
            continue
        previous_recommendations = previous.recommendations or []
        if not previous_recommendations:
            continue
        considered += 1
        if int(current.confidence_score or 0) > int(previous.confidence_score or 0):
            improved += 1

    if considered:
        adoption_rate = round((improved / considered) * 100.0, 2)
        insights.append(
            {
                "code": "recommendation_adoption_rate",
                "title": "Recommendation adoption effectiveness",
                "detail": f"{adoption_rate}% of recommendation-bearing snapshot transitions improved confidence.",
                "severity": "low" if adoption_rate >= 60 else "medium" if adoption_rate >= 40 else "high",
            }
        )

    pipeline_runs = list(SemanticPipelineRun.objects.all()[:1000])
    schedule_runs = list(SemanticScheduleRun.objects.all()[:1000])
    success_count = 0
    failure_count = 0
    for run in pipeline_runs + schedule_runs:
        if run.status == "completed":
            success_count += 1
        elif run.status == "failed":
            failure_count += 1

    total_pattern_runs = success_count + failure_count
    if total_pattern_runs:
        failure_rate = round((failure_count / total_pattern_runs) * 100.0, 2)
        insights.append(
            {
                "code": "compile_success_failure_patterns",
                "title": "Compile orchestration success/failure pattern",
                "detail": f"Completed: {success_count}, Failed: {failure_count}, Failure rate: {failure_rate}%.",
                "severity": "high" if failure_rate >= 25 else "medium" if failure_rate >= 10 else "low",
            }
        )

    if not insights:
        insights.append(
            {
                "code": "steady_state",
                "title": "Semantic system is steady",
                "detail": "No significant risk spikes detected in current snapshot window.",
                "severity": "low",
            }
        )

    return insights[:limit]
