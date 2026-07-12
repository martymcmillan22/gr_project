from __future__ import annotations

from django.utils import timezone

from project_middle_layer.exports import build_semantic_export_payload
from project_middle_layer.models import SemanticPipeline, SemanticPipelineRun
from project_middle_layer.semantic import build_semantic_diff
from project_middle_layer.services import compile_and_store_project_node
from project_middle_layer.webhooks import dispatch_semantic_webhook_event

from .scaffold import build_project_creation_payload


def _normalize_compile_payload(raw: dict[str, object]) -> dict[str, object]:
    title = str(raw.get("title") or raw.get("name") or "").strip()
    intent = str(raw.get("intent") or raw.get("semantic_intent") or "").strip()
    tier = str(raw.get("tier") or raw.get("visibility_tier") or "public").strip()
    tags_value = raw.get("tags") or raw.get("semantic_tags") or []

    if not isinstance(tags_value, list):
        raise ValueError("Compile payload tags must be a list.")
    tags = sorted({str(tag).strip().lower() for tag in tags_value if str(tag).strip()})

    if not title:
        raise ValueError("Compile payload requires title or name.")
    if not intent:
        raise ValueError("Compile payload requires intent or semantic_intent.")
    if not tags:
        raise ValueError("Compile payload requires at least one tag.")

    return {
        "slug": str(raw.get("slug") or title.lower().replace(" ", "-")).strip(),
        "name": title,
        "semantic_intent": intent,
        "mlas_tier": str(raw.get("mlas_tier") or "Semantic Utility"),
        "btif_classification": str(raw.get("btif_classification") or "ExpansionFlow"),
        "semantic_tags": tags,
        "visibility_tier": tier,
        "metadata": raw.get("metadata", {}) if isinstance(raw.get("metadata", {}), dict) else {},
    }


def _action_compile(step: dict[str, object]) -> dict[str, object]:
    payload = _normalize_compile_payload(step.get("payload", {}) if isinstance(step.get("payload", {}), dict) else {})
    compiled, node = compile_and_store_project_node(payload)
    return {
        "status": "compiled",
        "slug": node.slug,
        "identity_uri": compiled.get("identity_payload", {}).get("identity", {}).get("identity_uri", ""),
        "alerts": len(compiled.get("semantic_alerts", [])),
    }


def _action_batch_compile(step: dict[str, object]) -> dict[str, object]:
    payload = step.get("payload", {}) if isinstance(step.get("payload", {}), dict) else {}
    projects = payload.get("projects", [])
    if not isinstance(projects, list) or not projects:
        raise ValueError("batch-compile step requires payload.projects list.")

    items = []
    for raw in projects:
        if not isinstance(raw, dict):
            raise ValueError("batch-compile project item must be an object.")
        normalized = _normalize_compile_payload(raw)
        compiled, node = compile_and_store_project_node(normalized)
        items.append(
            {
                "slug": node.slug,
                "identity_uri": compiled.get("identity_payload", {}).get("identity", {}).get("identity_uri", ""),
            }
        )

    return {
        "status": "completed",
        "compiled": len(items),
        "items": items,
    }


def _action_diff(step: dict[str, object]) -> dict[str, object]:
    payload = step.get("payload", {}) if isinstance(step.get("payload", {}), dict) else {}
    source = payload.get("source", {}) if isinstance(payload.get("source", {}), dict) else {}
    target = payload.get("target", {}) if isinstance(payload.get("target", {}), dict) else {}
    if not source or not target:
        raise ValueError("diff step requires payload.source and payload.target objects.")

    diff = build_semantic_diff(source, target)
    return {
        "status": "completed",
        "summary": diff.get("summary", {}),
        "impact": diff.get("impact", {}),
    }


def _action_export(step: dict[str, object], *, triggered_by: str) -> dict[str, object]:
    payload = step.get("payload", {}) if isinstance(step.get("payload", {}), dict) else {}
    export_payload = build_semantic_export_payload(
        scope=str(payload.get("scope") or "all"),
        project_slug=str(payload.get("project_slug") or "") or None,
        include_history=bool(payload.get("include_history", False)),
        max_items=int(payload.get("max_items") or 100),
        exported_by=triggered_by,
    )
    return {
        "status": "completed",
        "summary": export_payload.get("summary", {}),
    }


def _action_recommend(step: dict[str, object]) -> dict[str, object]:
    payload = _normalize_compile_payload(step.get("payload", {}) if isinstance(step.get("payload", {}), dict) else {})
    compiled = build_project_creation_payload(
        slug=payload["slug"],
        name=payload["name"],
        semantic_intent=payload["semantic_intent"],
        mlas_tier=payload["mlas_tier"],
        btif_classification=payload["btif_classification"],
        semantic_tags=payload["semantic_tags"],
    )
    recommendations = compiled.get("recommendations", [])
    return {
        "status": "completed",
        "count": len(recommendations),
        "labels": [str(item.get("label", "Recommendation")) for item in recommendations if isinstance(item, dict)],
    }


def _action_alert_check(step: dict[str, object]) -> dict[str, object]:
    payload = _normalize_compile_payload(step.get("payload", {}) if isinstance(step.get("payload", {}), dict) else {})
    compiled = build_project_creation_payload(
        slug=payload["slug"],
        name=payload["name"],
        semantic_intent=payload["semantic_intent"],
        mlas_tier=payload["mlas_tier"],
        btif_classification=payload["btif_classification"],
        semantic_tags=payload["semantic_tags"],
    )
    alerts = compiled.get("semantic_alerts", [])
    return {
        "status": "completed",
        "count": len(alerts),
        "severities": sorted({str(item.get("severity", "low")) for item in alerts if isinstance(item, dict)}),
    }


def _run_step(step: dict[str, object], *, triggered_by: str) -> dict[str, object]:
    action = str(step.get("action") or "").strip().lower()
    if action == "compile":
        return _action_compile(step)
    if action == "batch-compile":
        return _action_batch_compile(step)
    if action == "diff":
        return _action_diff(step)
    if action == "export":
        return _action_export(step, triggered_by=triggered_by)
    if action == "recommend":
        return _action_recommend(step)
    if action == "alert-check":
        return _action_alert_check(step)
    raise ValueError(f"Unsupported pipeline action: {action}")


def run_semantic_pipeline(pipeline: SemanticPipeline, *, triggered_by: str = "manual") -> SemanticPipelineRun:
    pipeline.status = "running"
    pipeline.save(update_fields=["status", "updated_at"])

    run = SemanticPipelineRun.objects.create(
        pipeline=pipeline,
        status="running",
        triggered_by=triggered_by,
        result={"steps": []},
    )

    step_results: list[dict[str, object]] = []

    try:
        for index, step in enumerate(pipeline.steps or []):
            if not isinstance(step, dict):
                raise ValueError(f"Pipeline step {index} must be an object.")
            started_at = timezone.now().isoformat()
            result = _run_step(step, triggered_by=triggered_by)
            step_results.append(
                {
                    "index": index,
                    "action": str(step.get("action") or ""),
                    "started_at": started_at,
                    "result": result,
                }
            )

        run.status = "completed"
        run.completed_at = timezone.now()
        run.result = {"steps": step_results, "status": "completed"}
        run.error_message = ""

        pipeline.status = "completed"
        pipeline.last_run = run.completed_at
        pipeline.save(update_fields=["status", "last_run", "updated_at"])
        dispatch_semantic_webhook_event(
            event_type="pipeline.completed",
            payload={
                "pipeline": {
                    "id": pipeline.id,
                    "slug": pipeline.slug,
                    "name": pipeline.name,
                },
                "run": {
                    "id": run.id,
                    "status": run.status,
                    "step_count": len(step_results),
                },
            },
        )
    except Exception as exc:
        run.status = "failed"
        run.completed_at = timezone.now()
        run.result = {"steps": step_results, "status": "failed"}
        run.error_message = str(exc)

        pipeline.status = "failed"
        pipeline.last_run = run.completed_at
        pipeline.save(update_fields=["status", "last_run", "updated_at"])
        dispatch_semantic_webhook_event(
            event_type="pipeline.failed",
            payload={
                "pipeline": {
                    "id": pipeline.id,
                    "slug": pipeline.slug,
                    "name": pipeline.name,
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
