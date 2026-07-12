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


def dispatch_semantic_webhook_event(*, event_type: str, payload: dict[str, object]) -> list[SemanticWebhookDelivery]:
    deliveries: list[SemanticWebhookDelivery] = []
    webhooks = SemanticWebhook.objects.filter(status="active", event_type=event_type)

    for webhook in webhooks:
        delivery = SemanticWebhookDelivery.objects.create(
            webhook=webhook,
            event_type=event_type,
            payload=payload,
            status="pending",
        )
        deliveries.append(delivery)

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
