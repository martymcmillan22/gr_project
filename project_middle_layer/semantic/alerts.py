from project_middle_layer.schemas import ProjectSchema


def build_semantic_alerts(
    schema: ProjectSchema,
    *,
    drift_forecast: dict[str, object],
    confidence: dict[str, object],
    stability_analysis: dict[str, object],
    schema_validation_errors: list[str],
    recent_schema_issue_count: int,
    prior_drift_values: list[float],
) -> list[dict[str, object]]:
    alerts: list[dict[str, object]] = []

    risk_block = drift_forecast.get("risk", {}) if isinstance(drift_forecast, dict) else {}
    drift_value = float(risk_block.get("blended_semantic_drift_risk", 0.0) or 0.0)
    confidence_score = int(confidence.get("confidence_score", 0) or 0)
    stability_score = int(stability_analysis.get("stability_score", 0) or 0)

    def add_alert(alert_type: str, severity: str, message: str, **metadata: object) -> None:
        alerts.append(
            {
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "metadata": metadata,
            }
        )

    if drift_value >= 0.67:
        add_alert(
            "high_drift",
            "high",
            f"{schema['name']} has high semantic drift risk at {drift_value:.2f}.",
            drift_value=round(drift_value, 4),
        )

    if confidence_score < 60:
        add_alert(
            "low_confidence",
            "medium",
            f"{schema['name']} confidence is below the stability threshold ({confidence_score}).",
            confidence_score=confidence_score,
        )

    if stability_score < 60:
        add_alert(
            "unstable_stability",
            "medium",
            f"{schema['name']} stability score is below the operational threshold ({stability_score}).",
            stability_score=stability_score,
        )

    if schema_validation_errors:
        add_alert(
            "schema_failure",
            "high",
            f"{schema['name']} compiled with schema validation issues.",
            schema_issue_count=len(schema_validation_errors),
            errors=schema_validation_errors,
        )

    if recent_schema_issue_count >= 2:
        add_alert(
            "repeated_schema_failure",
            "critical",
            f"{schema['name']} has repeated schema failures across recent compiles.",
            recent_schema_issue_count=recent_schema_issue_count,
        )

    if len(prior_drift_values) >= 2 and drift_value - min(prior_drift_values) >= 0.15:
        add_alert(
            "timeline_drift_trend",
            "medium",
            f"{schema['name']} drift is trending upward across recent timeline snapshots.",
            current_drift=round(drift_value, 4),
            prior_drift_values=[round(value, 4) for value in prior_drift_values],
        )

    return alerts
