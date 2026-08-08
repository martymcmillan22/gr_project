from django.db import models

from project_middle_layer.models import ProjectEvolutionSnapshot, ProjectNode, SemanticAlert, SemanticLineageRecord
from project_middle_layer.pipelines import build_project_creation_payload
from project_middle_layer.semantic import build_semantic_alerts
from project_middle_layer.webhooks import dispatch_semantic_webhook_event
from polish.task_manager.constants import ASSIGNMENT_TWELVE_POINT
from polish.task_manager.routing import build_middle_layer_compartment_drift_detection
from platform_core.models import MLASClassificationRecord
from platform_reference.models import PlatformReferenceGICSReferenceSchema
from platform_reference.models import PlatformReferenceNAICSReferenceSchema
from platform_reference.services.reference_sync import get_gics_source_status
from seeds.rr_visual_system import build_rr_dashboard_payload


def build_middle_layer_rr_color_context() -> dict[str, object]:
    rr_payload = build_rr_dashboard_payload(limit_per_lane=3)
    active_lanes = [lane for lane in rr_payload.get("lanes", []) if lane.get("node_count", 0) > 0]
    active_lanes.sort(key=lambda lane: int(lane.get("node_count", 0)), reverse=True)
    dominant = [
        {
            "compartment_id": lane.get("compartment_id"),
            "subject": lane.get("subject"),
            "phase": lane.get("phase"),
            "node_count": lane.get("node_count"),
            "integrity": lane.get("integrity", {}),
            "display_anchor_band": lane.get("display_anchor_band", {}),
        }
        for lane in active_lanes[:6]
    ]

    return {
        "lane_count": rr_payload.get("lane_count", 0),
        "status_bands": rr_payload.get("status_bands", {}),
        "integrity_strip": rr_payload.get("integrity_strip", {}),
        "dominant_lanes": dominant,
    }


def get_project_middle_layer_activation_payload() -> dict[str, object]:
    gics_total = PlatformReferenceGICSReferenceSchema.objects.count()
    naics_total = PlatformReferenceNAICSReferenceSchema.objects.count()
    gics_source_status = get_gics_source_status()

    classified_total = MLASClassificationRecord.objects.count()
    classified_with_gics = MLASClassificationRecord.objects.exclude(gics_sub_industry_code="").count()
    classified_with_naics = MLASClassificationRecord.objects.exclude(naics_code_6="").count()

    project_total = ProjectNode.objects.count()
    snapshot_total = ProjectEvolutionSnapshot.objects.count()
    lineage_total = SemanticLineageRecord.objects.count()
    alert_total = SemanticAlert.objects.count()

    reference_ready = gics_total > 0 and naics_total > 0 and gics_source_status != "missing"
    drift_signal_ready = snapshot_total > 0 and lineage_total > 0
    classification_ready = classified_total == 0 or (classified_with_gics > 0 and classified_with_naics > 0)

    capability_flags = {
        "canonical_reference_truth": reference_ready,
        "classification_truth_binding": classification_ready,
        "drift_signal_readiness": drift_signal_ready,
        "compile_export_chain": project_total > 0 or snapshot_total > 0,
        "analytics_alert_surface": alert_total > 0 or snapshot_total > 0,
    }
    rr_color_context = build_middle_layer_rr_color_context()

    recent_snapshots = list(ProjectEvolutionSnapshot.objects.order_by("-created_at", "-id")[:12])
    avg_drift_risk = 0.0
    if recent_snapshots:
        avg_drift_risk = sum(float(item.drift_risk or 0.0) for item in recent_snapshots) / len(recent_snapshots)

    severity_weights = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for row in SemanticAlert.objects.values("severity").annotate(total=models.Count("id")):
        severity = str(row.get("severity", "")).lower()
        if severity in severity_weights:
            severity_weights[severity] = int(row.get("total", 0) or 0)

    compartment_drift_detection = build_middle_layer_compartment_drift_detection(
        assignment_type=ASSIGNMENT_TWELVE_POINT,
        deliverable_name="project middle layer governance",
        drift_risk=avg_drift_risk,
        alert_count=alert_total,
        severity_weights=severity_weights,
    )
    capability_flags["compartment_drift_governance"] = bool(compartment_drift_detection.get("compartments"))

    return {
        "app": "project_middle_layer",
        "boundary": "project-middle-layer",
        "status": "active",
        "reference_truth": {
            "gics_source_status": gics_source_status,
            "gics_total": gics_total,
            "naics_total": naics_total,
        },
        "classification_truth": {
            "total": classified_total,
            "gics_mapped": classified_with_gics,
            "naics_mapped": classified_with_naics,
        },
        "semantic_state": {
            "projects": project_total,
            "snapshots": snapshot_total,
            "lineage_records": lineage_total,
            "alerts": alert_total,
            "drift_baseline": round(avg_drift_risk, 3),
        },
        "rr_color_context": rr_color_context,
        "capability_flags": capability_flags,
        "compartment_drift_detection": compartment_drift_detection,
        "deterministic_ready": all(capability_flags.values()),
    }


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
