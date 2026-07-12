from project_middle_layer.models import ProjectEvolutionSnapshot, ProjectNode, SemanticAlert, SemanticLineageRecord
from project_middle_layer.pipelines import build_project_creation_payload
from project_middle_layer.semantic import build_semantic_alerts
from project_middle_layer.webhooks import dispatch_semantic_webhook_event


def _record_project_evolution_snapshot(*, project: ProjectNode, compiled: dict[str, object]) -> ProjectEvolutionSnapshot:
    identity_payload = compiled.get("identity_payload", {})
    identity = identity_payload.get("identity", {}) if isinstance(identity_payload, dict) else {}
    branch_resolution = identity.get("branch_resolution", {}) if isinstance(identity, dict) else {}
    drift_forecast = compiled.get("drift_forecast", {})
    drift_risk = drift_forecast.get("risk", {}) if isinstance(drift_forecast, dict) else {}
    specialized_path = compiled.get("specialized_path", {})
    semantic_tags = compiled.get("schema", {}).get("semantic_tags", []) if isinstance(compiled.get("schema", {}), dict) else []
    confidence = compiled.get("confidence", {}) if isinstance(compiled.get("confidence", {}), dict) else {}
    lineage_explorer = compiled.get("lineage_explorer", {}) if isinstance(compiled.get("lineage_explorer", {}), dict) else {}
    lineage_tree = lineage_explorer.get("lineage_tree", {}) if isinstance(lineage_explorer, dict) else {}
    semantic_clusters = lineage_explorer.get("semantic_clusters", []) if isinstance(lineage_explorer, dict) else []

    return ProjectEvolutionSnapshot.objects.create(
        project=project,
        identity_payload=identity_payload,
        drift_forecast=drift_forecast,
        branch_resolution=branch_resolution,
        specialized_path=specialized_path,
        semantic_tags=semantic_tags,
        identity_uri=str(identity.get("identity_uri", "")),
        branch_name=str(branch_resolution.get("selected_branch", "")),
        drift_risk=float(drift_risk.get("blended_semantic_drift_risk", 0.0) or 0.0),
        confidence_score=int(confidence.get("confidence_score", 0) or 0),
        confidence_label=str(confidence.get("confidence_label", "Volatile")),
        schema_issue_count=len(compiled.get("schema_validation_errors", []) or []),
        recommendations=compiled.get("recommendations", []),
    )


def _record_semantic_lineage(*, project: ProjectNode, compiled: dict[str, object]) -> SemanticLineageRecord:
    lineage_explorer = compiled.get("lineage_explorer", {}) if isinstance(compiled.get("lineage_explorer", {}), dict) else {}
    lineage_tree = lineage_explorer.get("lineage_tree", {}) if isinstance(lineage_explorer, dict) else {}
    semantic_clusters = lineage_explorer.get("semantic_clusters", []) if isinstance(lineage_explorer, dict) else []

    return SemanticLineageRecord.objects.create(
        project=project,
        lineage_tree=lineage_tree,
        semantic_clusters=semantic_clusters,
        recommendations=compiled.get("recommendations", []),
    )


def _record_semantic_alerts(*, project: ProjectNode, snapshot: ProjectEvolutionSnapshot, compiled: dict[str, object]) -> list[SemanticAlert]:
    prior_snapshots = list(
        ProjectEvolutionSnapshot.objects.filter(project=project)
        .exclude(id=snapshot.id)
        .order_by("-created_at", "-id")[:5]
    )
    recent_schema_issue_count = sum(1 for item in prior_snapshots if (item.schema_issue_count or 0) > 0) + (1 if snapshot.schema_issue_count > 0 else 0)
    prior_drift_values = [float(item.drift_risk or 0.0) for item in prior_snapshots[:3]]

    alerts_payload = build_semantic_alerts(
        compiled.get("schema", {}),
        drift_forecast=compiled.get("drift_forecast", {}),
        confidence=compiled.get("confidence", {}),
        stability_analysis=compiled.get("stability_analysis", {}),
        schema_validation_errors=compiled.get("schema_validation_errors", []),
        recent_schema_issue_count=recent_schema_issue_count,
        prior_drift_values=prior_drift_values,
    )

    alerts: list[SemanticAlert] = []
    for alert_payload in alerts_payload:
        alerts.append(
            SemanticAlert.objects.create(
                project=project,
                source_snapshot=snapshot,
                alert_type=alert_payload["alert_type"],
                severity=alert_payload["severity"],
                message=alert_payload["message"],
                metadata=alert_payload.get("metadata", {}),
            )
        )
    return alerts


def compile_and_store_project_node(payload: dict[str, object]) -> tuple[dict[str, object], ProjectNode]:
    compiled = build_project_creation_payload(
        slug=payload["slug"],
        name=payload["name"],
        semantic_intent=payload["semantic_intent"],
        mlas_tier=payload["mlas_tier"],
        btif_classification=payload["btif_classification"],
        semantic_tags=payload["semantic_tags"],
    )

    metadata = {
        **payload.get("metadata", {}),
        "semantic_tags": payload["semantic_tags"],
        "visibility_tier": payload.get("visibility_tier"),
        "drift_forecast": compiled["drift_forecast"],
        "confidence": compiled.get("confidence", {}),
        "lineage_explorer": compiled.get("lineage_explorer", {}),
        "drift_heatmap_data": compiled.get("drift_heatmap_data", {}),
        "stability_analysis": compiled.get("stability_analysis", {}),
        "recommendations": compiled.get("recommendations", []),
        "identity_payload": compiled["identity_payload"],
        "specialized_path": compiled["specialized_path"],
        "semantic_tree": compiled["semantic_tree"],
    }

    node, _ = ProjectNode.objects.update_or_create(
        slug=payload["slug"],
        defaults={
            "name": payload["name"],
            "semantic_intent": payload["semantic_intent"],
            "mlas_tier": payload["mlas_tier"],
            "btif_classification": payload["btif_classification"],
            "metadata": metadata,
        },
    )
    snapshot = _record_project_evolution_snapshot(project=node, compiled=compiled)
    _record_semantic_lineage(project=node, compiled=compiled)
    alerts = _record_semantic_alerts(project=node, snapshot=snapshot, compiled=compiled)

    compiled["semantic_alerts"] = [
        {
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "metadata": alert.metadata,
        }
        for alert in alerts
    ]

    dispatch_semantic_webhook_event(
        event_type="compile.completed",
        payload={
            "project": {
                "id": node.id,
                "slug": node.slug,
                "name": node.name,
            },
            "snapshot": {
                "id": snapshot.id,
                "identity_uri": snapshot.identity_uri,
                "branch_name": snapshot.branch_name,
                "drift_risk": snapshot.drift_risk,
                "confidence_score": snapshot.confidence_score,
            },
            "alert_count": len(alerts),
        },
    )

    for alert in alerts:
        dispatch_semantic_webhook_event(
            event_type="alert.created",
            payload={
                "project": {
                    "id": node.id,
                    "slug": node.slug,
                },
                "alert": {
                    "id": alert.id,
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                },
            },
        )

    return compiled, node
