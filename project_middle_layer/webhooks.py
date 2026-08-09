from __future__ import annotations

import json
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from django.utils import timezone

from project_middle_layer.models import SemanticWebhook, SemanticWebhookDelivery


def _build_headers(*, event_type: str, secret_token: str | None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Semantic-Event": event_type,
    }
    if secret_token:
        headers["X-Semantic-Webhook-Token"] = secret_token
    return headers


def _normalize_timeline_event_envelope(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}

    normalized = dict(payload)
    timeline_event = normalized.get("timeline_event", {})
    if not isinstance(timeline_event, dict):
        return normalized

    priority_order = ["critical", "warn", "info"]
    priority_rank = {"critical": 0, "warn": 1, "info": 2}

    gate_locked = bool(
        timeline_event.get("gate_locked")
        if timeline_event.get("gate_locked") is not None
        else timeline_event.get("locked")
    )
    slot_completed = bool(
        timeline_event.get("slot_completed")
        if timeline_event.get("slot_completed") is not None
        else timeline_event.get("completed")
    )

    try:
        slot_index = int(timeline_event.get("slot_index") or 0)
    except (TypeError, ValueError):
        slot_index = 0

    normalized_timeline_event = {
        "event_type": str(timeline_event.get("event_type") or ""),
        "event_version": str(timeline_event.get("event_version") or "v1"),
        "source": str(timeline_event.get("source") or "project_middle_layer.calculus_timeline_runtime"),
        "slot_index": slot_index,
        "phase": str(timeline_event.get("phase") or ""),
        "temporal_alignment": str(timeline_event.get("temporal_alignment") or ""),
        "calculus_operation": str(timeline_event.get("calculus_operation") or ""),
        "gate_locked": gate_locked,
        "slot_completed": slot_completed,
        "drift_score": timeline_event.get("drift_score"),
        "stability_score": timeline_event.get("stability_score"),
        "alignment_score": timeline_event.get("alignment_score"),
        "industry_metadata": timeline_event.get("industry_metadata")
        if isinstance(timeline_event.get("industry_metadata"), dict)
        else {},
        "semantic_state": timeline_event.get("semantic_state")
        if isinstance(timeline_event.get("semantic_state"), dict)
        else {},
        "priority": str(timeline_event.get("priority") or "info").lower(),
        "completed_slots": timeline_event.get("completed_slots")
        if isinstance(timeline_event.get("completed_slots"), list)
        else normalized.get("completed_slots")
        if isinstance(normalized.get("completed_slots"), list)
        else [],
    }

    raw_queue = normalized.get("orchestration_priority_queue", [])
    normalized_queue = []
    if isinstance(raw_queue, list):
        for entry in raw_queue:
            if not isinstance(entry, dict):
                continue
            try:
                slot_index = int(entry.get("slot_index") or 0)
            except (TypeError, ValueError):
                slot_index = 0
            try:
                queue_index = int(entry.get("queue_index") or 0)
            except (TypeError, ValueError):
                queue_index = 0
            priority = str(entry.get("priority") or "info").lower()
            normalized_queue.append(
                {
                    "queue_index": queue_index,
                    "event_type": str(entry.get("event_type") or ""),
                    "slot_index": slot_index,
                    "priority": priority,
                    "orchestration_reason": str(entry.get("orchestration_reason") or ""),
                }
            )

    normalized_queue.sort(
        key=lambda item: (
            priority_rank.get(str(item.get("priority") or "info"), len(priority_rank)),
            int(item.get("slot_index") or 0),
            str(item.get("event_type") or ""),
            int(item.get("queue_index") or 0),
        )
    )
    for index, entry in enumerate(normalized_queue):
        entry["queue_index"] = index

    phase_gates = normalized.get("phase_gates") if isinstance(normalized.get("phase_gates"), list) else []
    completed_slots = normalized_timeline_event.get("completed_slots") if isinstance(normalized_timeline_event.get("completed_slots"), list) else []
    latest_drift = normalized_timeline_event.get("drift_score")
    latest_stability = normalized_timeline_event.get("stability_score")
    latest_alignment = normalized_timeline_event.get("alignment_score")
    try:
        latest_drift_value = float(latest_drift)
    except (TypeError, ValueError):
        latest_drift_value = 0.0
    try:
        latest_stability_value = float(latest_stability)
    except (TypeError, ValueError):
        latest_stability_value = 0.0
    try:
        latest_alignment_value = float(latest_alignment)
    except (TypeError, ValueError):
        latest_alignment_value = 0.0

    risk_level = "low"
    if latest_drift_value >= 0.67 or latest_alignment_value <= 0.4 or gate_locked:
        risk_level = "medium"
    if latest_drift_value >= 0.85 or latest_alignment_value <= 0.2:
        risk_level = "high"

    locked_phases = [
        str(item.get("phase") or "")
        for item in phase_gates
        if isinstance(item, dict) and bool(item.get("locked"))
    ]
    unlocked_phases = [
        str(item.get("phase") or "")
        for item in phase_gates
        if isinstance(item, dict) and not bool(item.get("locked"))
    ]

    highest_priority = "info"
    if normalized_queue:
        highest_priority = str(normalized_queue[0].get("priority") or "info")

    provided_platform_intelligence = normalized.get("platform_intelligence")
    if isinstance(provided_platform_intelligence, dict):
        platform_intelligence = dict(provided_platform_intelligence)
    else:
        platform_intelligence = {}

    platform_intelligence.setdefault("source", "project_middle_layer.webhook_normalizer")
    platform_intelligence["orchestration"] = {
        "priority_order": priority_order,
        "trigger_count": len(normalized_queue),
        "highest_priority": highest_priority,
    }
    platform_intelligence["semantic_metadata"] = {
        "drift_score": round(max(0.0, min(1.0, latest_drift_value)), 3),
        "stability_score": round(max(0.0, min(1.0, latest_stability_value)), 3),
        "alignment_score": round(max(0.0, min(1.0, latest_alignment_value)), 3),
    }
    platform_intelligence["phase_gate_state"] = {
        "locked_phases": locked_phases,
        "unlocked_phases": unlocked_phases,
    }
    platform_intelligence["slot_progression"] = {
        "slot_count": 16,
        "completed_count": len(completed_slots),
        "completion_ratio": round(len(completed_slots) / 16.0, 3),
        "latest_slot_index": slot_index,
        "latest_phase": normalized_timeline_event.get("phase"),
    }
    platform_intelligence["synthesis"] = {
        "risk_level": risk_level,
        "drift_trend": {
            "direction": "stable",
            "delta": 0.0,
            "sample_count": 1,
        },
        "alignment_trajectory": {
            "direction": "stable",
            "delta": 0.0,
            "sample_count": 1,
        },
    }

    normalized["timeline_event"] = normalized_timeline_event
    normalized["priority_order"] = priority_order
    normalized["orchestration_priority_queue"] = normalized_queue
    normalized["platform_intelligence"] = platform_intelligence
    return normalized


def dispatch_semantic_webhook_event(*, event_type: str, payload: dict[str, object]) -> list[SemanticWebhookDelivery]:
    deliveries: list[SemanticWebhookDelivery] = []
    normalized_payload = _normalize_timeline_event_envelope(payload)
    webhooks = SemanticWebhook.objects.filter(status="active", event_type=event_type)

    for webhook in webhooks:
        delivery = SemanticWebhookDelivery.objects.create(
            webhook=webhook,
            event_type=event_type,
            payload=normalized_payload,
            status="pending",
        )
        deliveries.append(delivery)

        body = json.dumps(normalized_payload).encode("utf-8")
        headers = _build_headers(event_type=event_type, secret_token=webhook.secret_token)
        req = urllib_request.Request(webhook.target_url, data=body, headers=headers, method="POST")

        try:
            with urllib_request.urlopen(req, timeout=5) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                status_code = int(getattr(response, "status", 200) or 200)

            delivery.status = "delivered" if 200 <= status_code < 300 else "failed"
            delivery.response_code = status_code
            delivery.response_body = response_body[:4000]
            delivery.error_message = "" if delivery.status == "delivered" else f"HTTP status {status_code}"
            delivery.delivered_at = timezone.now()
            delivery.save(update_fields=["status", "response_code", "response_body", "error_message", "delivered_at"])

            webhook.last_delivery = delivery.delivered_at
            webhook.save(update_fields=["last_delivery", "updated_at"])
        except HTTPError as exc:
            try:
                err_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                err_body = ""
            delivery.status = "failed"
            delivery.response_code = getattr(exc, "code", None)
            delivery.response_body = err_body[:4000]
            delivery.error_message = str(exc)
            delivery.delivered_at = timezone.now()
            delivery.save(update_fields=["status", "response_code", "response_body", "error_message", "delivered_at"])
        except URLError as exc:
            delivery.status = "failed"
            delivery.error_message = str(exc)
            delivery.delivered_at = timezone.now()
            delivery.save(update_fields=["status", "error_message", "delivered_at"])
        except Exception as exc:
            delivery.status = "failed"
            delivery.error_message = str(exc)
            delivery.delivered_at = timezone.now()
            delivery.save(update_fields=["status", "error_message", "delivered_at"])

    return deliveries


def retry_webhook_delivery(delivery: SemanticWebhookDelivery) -> SemanticWebhookDelivery:
    webhook = delivery.webhook
    payload = delivery.payload if isinstance(delivery.payload, dict) else {}
    payload = _normalize_timeline_event_envelope(payload)
    event_type = delivery.event_type

    body = json.dumps(payload).encode("utf-8")
    headers = _build_headers(event_type=event_type, secret_token=webhook.secret_token)
    req = urllib_request.Request(webhook.target_url, data=body, headers=headers, method="POST")

    try:
        with urllib_request.urlopen(req, timeout=5) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            status_code = int(getattr(response, "status", 200) or 200)

        delivery.status = "delivered" if 200 <= status_code < 300 else "failed"
        delivery.response_code = status_code
        delivery.response_body = response_body[:4000]
        delivery.error_message = "" if delivery.status == "delivered" else f"HTTP status {status_code}"
        delivery.delivered_at = timezone.now()
        delivery.save(update_fields=["status", "response_code", "response_body", "error_message", "delivered_at"])

        webhook.last_delivery = delivery.delivered_at
        webhook.save(update_fields=["last_delivery", "updated_at"])
    except Exception as exc:
        delivery.status = "failed"
        delivery.error_message = str(exc)
        delivery.delivered_at = timezone.now()
        delivery.save(update_fields=["status", "error_message", "delivered_at"])

    return delivery
