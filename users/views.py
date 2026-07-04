from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, RedirectView, UpdateView, CreateView, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from uuid import uuid4


from .forms import UserCreationForm, UserChangeForm
from .billing import (
    get_billing_provider_adapter,
    verify_stripe_webhook_signature,
    verify_webhook_signature,
)
from .models import BillingCheckoutIntent, BillingWebhookEvent

User = get_user_model()


def _friendly_billing_error_message(error_message: str) -> str:
    raw = (error_message or "").strip()
    lowered = raw.lower()

    if "stripe secret key" in lowered or "sdk is not installed" in lowered:
        return "Billing provider setup is temporarily unavailable. Please try again later."
    if "price mapping" in lowered or "invalid subscription tier" in lowered or "unknown" in lowered:
        return "Your selected plan could not be mapped at checkout. Please retry or contact support."
    if "idempotency key" in lowered:
        return "A similar billing request is already in progress. Please retry with a new request."
    if "invalid webhook signature" in lowered:
        return "We could not verify the billing provider update. Please try again."
    if "user not found" in lowered or "no user found" in lowered:
        return "The billing update could not be matched to your account."
    if "missing user email" in lowered:
        return "The billing provider update is incomplete. Please retry shortly."
    if raw:
        return raw
    return "Billing request failed. Please try again."


def _provider_badge(provider_name: str) -> tuple[str, str]:
    token = (provider_name or "").strip().lower()
    if token == "stripe":
        return "Stripe", "is-info"
    if token == "generic":
        return "Generic", "is-primary"
    if "test" in token:
        return "Test provider", "is-warning"
    if token:
        return provider_name.title(), "is-dark"
    return "Provider", "is-light"


def _build_billing_timeline(user, *, limit=20, status_filter="all"):
    timeline_rows = []
    valid_tiers = {choice[0] for choice in User.SUBSCRIPTION_CHOICES}
    premium_tiers = valid_tiers - {User.SUBSCRIPTION_FREE}

    intents = list(
        BillingCheckoutIntent.objects.filter(user=user)
        .order_by("-updated_at", "-id")[:limit]
    )
    for intent in intents:
        timestamp = intent.updated_at or intent.created_at
        provider_label, provider_badge_class = _provider_badge(intent.provider)
        if intent.status == BillingCheckoutIntent.STATUS_CREATED:
            support_context = f"source=intent;intent_id={intent.id};idempotency_key={intent.idempotency_key}"
            timeline_rows.append(
                {
                    "timestamp": timestamp,
                    "provider_label": provider_label,
                    "provider_badge_class": provider_badge_class,
                    "title": "Checkout started",
                    "status": "pending",
                    "status_label": "Pending",
                    "status_class": "is-warning",
                    "details": f"Provider: {intent.provider} | Requested tier: {intent.requested_tier}",
                    "error_text": "",
                    "retry_available": False,
                    "retry_tier": "",
                    "support_context": support_context,
                }
            )
        elif intent.status == BillingCheckoutIntent.STATUS_SESSION_CREATED:
            support_context = (
                f"source=intent;intent_id={intent.id};idempotency_key={intent.idempotency_key};"
                f"session_id={intent.provider_session_id or 'unknown'}"
            )
            timeline_rows.append(
                {
                    "timestamp": timestamp,
                    "provider_label": provider_label,
                    "provider_badge_class": provider_badge_class,
                    "title": "Stripe session created",
                    "status": "pending",
                    "status_label": "Pending",
                    "status_class": "is-warning",
                    "details": f"Session ready for {intent.requested_tier}.",
                    "error_text": "",
                    "retry_available": False,
                    "retry_tier": "",
                    "support_context": support_context,
                }
            )
        elif intent.status == BillingCheckoutIntent.STATUS_COMPLETED:
            support_context = (
                f"source=intent;intent_id={intent.id};idempotency_key={intent.idempotency_key};"
                f"requested_tier={intent.requested_tier}"
            )
            timeline_rows.append(
                {
                    "timestamp": timestamp,
                    "provider_label": provider_label,
                    "provider_badge_class": provider_badge_class,
                    "title": "Subscription activated",
                    "status": "completed",
                    "status_label": "Completed",
                    "status_class": "is-success",
                    "details": f"Plan activated: {intent.requested_tier}.",
                    "error_text": "",
                    "retry_available": False,
                    "retry_tier": "",
                    "support_context": support_context,
                }
            )
        elif intent.status == BillingCheckoutIntent.STATUS_FAILED:
            retry_tier = intent.requested_tier if intent.requested_tier in premium_tiers else ""
            retry_unavailable_reason = "" if retry_tier else "No reusable plan was found for this failure."
            support_context = (
                f"source=intent;provider={intent.provider};intent_id={intent.id};"
                f"idempotency_key={intent.idempotency_key};requested_tier={intent.requested_tier};"
                f"provider_session_id={intent.provider_session_id or 'unknown'};"
                f"timestamp={timestamp.isoformat()}"
            )
            timeline_rows.append(
                {
                    "timestamp": timestamp,
                    "provider_label": provider_label,
                    "provider_badge_class": provider_badge_class,
                    "title": "Subscription failed",
                    "status": "failed",
                    "status_label": "Failed",
                    "status_class": "is-danger",
                    "details": "Retry required",
                    "error_text": _friendly_billing_error_message(intent.error_message),
                    "retry_available": bool(retry_tier),
                    "retry_tier": retry_tier,
                    "retry_unavailable_reason": retry_unavailable_reason,
                    "support_context": support_context,
                }
            )

    events = list(
        BillingWebhookEvent.objects.filter(user=user)
        .order_by("-created_at", "-id")[:limit]
    )
    for event in events:
        event_timestamp = event.processed_at or event.created_at
        provider_label, provider_badge_class = _provider_badge(event.provider)
        if event.status == BillingWebhookEvent.STATUS_RECEIVED:
            support_context = (
                f"source=webhook;event_id={event.provider_event_id or 'unknown'};"
                f"idempotency_key={event.idempotency_key}"
            )
            timeline_rows.append(
                {
                    "timestamp": event_timestamp,
                    "provider_label": provider_label,
                    "provider_badge_class": provider_badge_class,
                    "title": "Webhook received",
                    "status": "pending",
                    "status_label": "Pending",
                    "status_class": "is-warning",
                    "details": event.event_type or "Subscription webhook",
                    "error_text": "",
                    "retry_available": False,
                    "retry_tier": "",
                    "support_context": support_context,
                }
            )
        elif event.status == BillingWebhookEvent.STATUS_PROCESSED:
            support_context = (
                f"source=webhook;event_id={event.provider_event_id or 'unknown'};"
                f"idempotency_key={event.idempotency_key};target_tier={event.target_tier or 'unknown'}"
            )
            timeline_rows.append(
                {
                    "timestamp": event_timestamp,
                    "provider_label": provider_label,
                    "provider_badge_class": provider_badge_class,
                    "title": "Subscription activated",
                    "status": "completed",
                    "status_label": "Completed",
                    "status_class": "is-success",
                    "details": f"Webhook applied: {event.target_tier or 'subscription update'}.",
                    "error_text": "",
                    "retry_available": False,
                    "retry_tier": "",
                    "support_context": support_context,
                }
            )
        elif event.status == BillingWebhookEvent.STATUS_FAILED:
            retry_tier = event.target_tier if event.target_tier in premium_tiers else ""
            retry_unavailable_reason = "" if retry_tier else "No reusable plan was found for this failure."
            support_context = (
                f"source=webhook;provider={event.provider};event_id={event.provider_event_id or 'unknown'};"
                f"idempotency_key={event.idempotency_key};event_type={event.event_type or 'unknown'};"
                f"target_tier={event.target_tier or 'unknown'};timestamp={event_timestamp.isoformat()}"
            )
            timeline_rows.append(
                {
                    "timestamp": event_timestamp,
                    "provider_label": provider_label,
                    "provider_badge_class": provider_badge_class,
                    "title": "Subscription failed",
                    "status": "failed",
                    "status_label": "Failed",
                    "status_class": "is-danger",
                    "details": "Retry required",
                    "error_text": _friendly_billing_error_message(event.error_message),
                    "retry_available": bool(retry_tier),
                    "retry_tier": retry_tier,
                    "retry_unavailable_reason": retry_unavailable_reason,
                    "support_context": support_context,
                }
            )

    timeline_rows.sort(key=lambda item: (item.get("timestamp") or timezone.now()), reverse=True)

    if status_filter in {"pending", "completed", "failed"}:
        timeline_rows = [row for row in timeline_rows if row.get("status") == status_filter]

    return timeline_rows[:limit]


def _parse_support_context(raw_context: str) -> dict:
    parsed = {}
    for token in (raw_context or "").split(";"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _build_support_context_summary(user):
    timeline_rows = _build_billing_timeline(user, limit=20, status_filter="all")
    if not timeline_rows:
        return None

    latest = timeline_rows[0]
    support_context = latest.get("support_context") or ""
    context_map = _parse_support_context(support_context)

    summary = {
        "event_id": context_map.get("event_id", "unknown"),
        "idempotency_key": context_map.get("idempotency_key", "unknown"),
        "provider_session_id": context_map.get("provider_session_id", "unknown"),
        "tier": context_map.get("target_tier") or context_map.get("requested_tier") or "unknown",
        "timestamp": latest.get("timestamp"),
        "safe_error_text": latest.get("error_text") if latest.get("status") == "failed" else "",
        "copy_payload": support_context,
    }
    return summary


def _build_support_context_diff(user):
    latest_intent = (
        BillingCheckoutIntent.objects.filter(user=user)
        .order_by("-updated_at", "-id")
        .first()
    )
    latest_webhook = (
        BillingWebhookEvent.objects.filter(user=user)
        .order_by("-processed_at", "-created_at", "-id")
        .first()
    )

    if not latest_intent and not latest_webhook:
        return None

    def _safe(value, fallback="unknown"):
        cleaned = (value or "").strip()
        return cleaned if cleaned else fallback

    intent_timestamp = latest_intent.updated_at.isoformat() if latest_intent and latest_intent.updated_at else "unknown"
    webhook_timestamp = "unknown"
    if latest_webhook:
        event_ts = latest_webhook.processed_at or latest_webhook.created_at
        if event_ts:
            webhook_timestamp = event_ts.isoformat()

    intent_failure = (
        _friendly_billing_error_message(latest_intent.error_message)
        if latest_intent and latest_intent.status == BillingCheckoutIntent.STATUS_FAILED
        else "none"
    )
    webhook_failure = (
        _friendly_billing_error_message(latest_webhook.error_message)
        if latest_webhook and latest_webhook.status == BillingWebhookEvent.STATUS_FAILED
        else "none"
    )

    comparisons = [
        {
            "label": "Tier",
            "key": "tier",
            "intent": _safe(latest_intent.requested_tier if latest_intent else ""),
            "webhook": _safe(latest_webhook.target_tier if latest_webhook else ""),
        },
        {
            "label": "Provider session ID",
            "key": "provider_session_id",
            "intent": _safe(latest_intent.provider_session_id if latest_intent else ""),
            "webhook": "not_reported" if latest_webhook else "missing",
        },
        {
            "label": "Idempotency key",
            "key": "idempotency_key",
            "intent": _safe(latest_intent.idempotency_key if latest_intent else ""),
            "webhook": _safe(latest_webhook.idempotency_key if latest_webhook else ""),
        },
        {
            "label": "Event type",
            "key": "event_type",
            "intent": "not_reported",
            "webhook": _safe(latest_webhook.event_type if latest_webhook else ""),
        },
        {
            "label": "Failure reason",
            "key": "failure_reason",
            "intent": intent_failure,
            "webhook": webhook_failure,
        },
    ]

    mismatches = []
    for entry in comparisons:
        if entry["intent"] != entry["webhook"]:
            mismatches.append(entry)

    if not mismatches:
        return None

    copy_payload = ";".join(
        [
            f"intent_tier={_safe(latest_intent.requested_tier if latest_intent else '')}",
            f"webhook_tier={_safe(latest_webhook.target_tier if latest_webhook else '')}",
            f"intent_provider_session_id={_safe(latest_intent.provider_session_id if latest_intent else '')}",
            f"webhook_event_type={_safe(latest_webhook.event_type if latest_webhook else '')}",
            f"intent_idempotency_key={_safe(latest_intent.idempotency_key if latest_intent else '')}",
            f"webhook_idempotency_key={_safe(latest_webhook.idempotency_key if latest_webhook else '')}",
            f"intent_failure_reason={intent_failure}",
            f"webhook_failure_reason={webhook_failure}",
            f"intent_timestamp={intent_timestamp}",
            f"webhook_timestamp={webhook_timestamp}",
        ]
    )

    return {
        "mismatches": mismatches,
        "intent_timestamp": intent_timestamp,
        "webhook_timestamp": webhook_timestamp,
        "copy_payload": copy_payload,
    }


def _build_billing_health_indicator(user, *, window=8):
    timeline_rows = _build_billing_timeline(user, limit=window, status_filter="all")
    if not timeline_rows:
        return None

    intents = list(
        BillingCheckoutIntent.objects.filter(user=user)
        .order_by("-updated_at", "-id")[:window]
    )
    webhook_events = list(
        BillingWebhookEvent.objects.filter(user=user)
        .order_by("-processed_at", "-created_at", "-id")[:window]
    )

    success_count = sum(1 for row in timeline_rows if row.get("status") == "completed")
    failure_count = sum(1 for row in timeline_rows if row.get("status") == "failed")
    latest_failed_row = next((row for row in timeline_rows if row.get("status") == "failed"), None)

    retry_attempt_count = 0
    failed_tier_seen = set()
    for intent in reversed(intents):
        tier = (intent.requested_tier or "").strip()
        if not tier:
            continue
        if intent.status == BillingCheckoutIntent.STATUS_FAILED:
            failed_tier_seen.add(tier)
            continue
        if tier in failed_tier_seen and intent.status in {
            BillingCheckoutIntent.STATUS_CREATED,
            BillingCheckoutIntent.STATUS_SESSION_CREATED,
            BillingCheckoutIntent.STATUS_COMPLETED,
        }:
            retry_attempt_count += 1

    latest_webhook_by_idempotency = {}
    for event in webhook_events:
        key = (event.idempotency_key or "").strip()
        if not key or key in latest_webhook_by_idempotency:
            continue
        latest_webhook_by_idempotency[key] = event

    webhook_miss_count = 0
    aligned_diff_count = 0
    mismatched_diff_count = 0
    for intent in intents:
        key = (intent.idempotency_key or "").strip()
        if not key:
            continue
        event = latest_webhook_by_idempotency.get(key)
        if not event:
            webhook_miss_count += 1
            mismatched_diff_count += 1
            continue

        tier_intent = (intent.requested_tier or "unknown").strip() or "unknown"
        tier_webhook = (event.target_tier or "unknown").strip() or "unknown"
        safe_intent_error = (
            _friendly_billing_error_message(intent.error_message)
            if intent.status == BillingCheckoutIntent.STATUS_FAILED
            else "none"
        )
        safe_webhook_error = (
            _friendly_billing_error_message(event.error_message)
            if event.status == BillingWebhookEvent.STATUS_FAILED
            else "none"
        )
        is_mismatch = (
            tier_intent != tier_webhook
            or key != (event.idempotency_key or "").strip()
            or safe_intent_error != safe_webhook_error
        )
        if is_mismatch:
            mismatched_diff_count += 1
        else:
            aligned_diff_count += 1

    webhook_terminal = [
        event for event in webhook_events if event.status in {
            BillingWebhookEvent.STATUS_PROCESSED,
            BillingWebhookEvent.STATUS_FAILED,
        }
    ]
    if webhook_terminal:
        webhook_processed = sum(1 for event in webhook_terminal if event.status == BillingWebhookEvent.STATUS_PROCESSED)
        webhook_reliability = round((webhook_processed / len(webhook_terminal)) * 100)
    else:
        webhook_reliability = 100

    checkout_terminal = [
        intent for intent in intents if intent.status in {
            BillingCheckoutIntent.STATUS_COMPLETED,
            BillingCheckoutIntent.STATUS_FAILED,
        }
    ]
    if checkout_terminal:
        checkout_completed = sum(1 for intent in checkout_terminal if intent.status == BillingCheckoutIntent.STATUS_COMPLETED)
        checkout_reliability = round((checkout_completed / len(checkout_terminal)) * 100)
    else:
        checkout_reliability = 100

    health_level = "healthy"
    health_label = "Billing healthy"
    health_class = "is-success"

    if (
        failure_count >= max(3, len(timeline_rows) // 2)
        or webhook_reliability < 50
        or checkout_reliability < 50
    ):
        health_level = "failing"
        health_label = "Billing failing"
        health_class = "is-danger"
    elif failure_count > 0 or webhook_miss_count > 0 or mismatched_diff_count > 0:
        health_level = "degraded"
        health_label = "Billing degraded"
        health_class = "is-warning"

    return {
        "health_level": health_level,
        "health_label": health_label,
        "health_class": health_class,
        "window": len(timeline_rows),
        "success_count": success_count,
        "failure_count": failure_count,
        "retry_attempt_count": retry_attempt_count,
        "webhook_miss_count": webhook_miss_count,
        "aligned_diff_count": aligned_diff_count,
        "mismatched_diff_count": mismatched_diff_count,
        "webhook_reliability": webhook_reliability,
        "checkout_reliability": checkout_reliability,
        "safe_recent_failure_reason": latest_failed_row.get("error_text", "") if latest_failed_row else "",
    }


def _build_billing_event_export_payload(user, *, window=8):
    timeline_rows = _build_billing_timeline(user, limit=window, status_filter="all")
    if not timeline_rows:
        return None

    health = _build_billing_health_indicator(user, window=window) or {}
    summary = _build_support_context_summary(user) or {}
    diff = _build_support_context_diff(user) or {}

    lines = [
        "billing_support_bundle_v1",
        "[health]",
        f"health_level={health.get('health_level', 'unknown')}",
        f"health_label={health.get('health_label', 'unknown')}",
        f"window={health.get('window', len(timeline_rows))}",
        f"success_count={health.get('success_count', 0)}",
        f"failure_count={health.get('failure_count', 0)}",
        f"retry_attempt_count={health.get('retry_attempt_count', 0)}",
        f"webhook_miss_count={health.get('webhook_miss_count', 0)}",
        f"aligned_diff_count={health.get('aligned_diff_count', 0)}",
        f"mismatched_diff_count={health.get('mismatched_diff_count', 0)}",
        f"webhook_reliability={health.get('webhook_reliability', 0)}",
        f"checkout_reliability={health.get('checkout_reliability', 0)}",
        f"safe_recent_failure_reason={health.get('safe_recent_failure_reason', 'none') or 'none'}",
        "[summary]",
        f"summary_event_id={summary.get('event_id', 'unknown')}",
        f"summary_idempotency_key={summary.get('idempotency_key', 'unknown')}",
        f"summary_provider_session_id={summary.get('provider_session_id', 'unknown')}",
        f"summary_tier={summary.get('tier', 'unknown')}",
        f"summary_timestamp={summary.get('timestamp').isoformat() if summary.get('timestamp') else 'unknown'}",
        f"summary_safe_error={summary.get('safe_error_text', 'none') or 'none'}",
    ]

    if diff:
        lines.extend(
            [
                "[diff]",
                f"diff_mismatch_count={len(diff.get('mismatches', []))}",
                f"intent_timestamp={diff.get('intent_timestamp', 'unknown')}",
                f"webhook_timestamp={diff.get('webhook_timestamp', 'unknown')}",
            ]
        )
        for index, mismatch in enumerate(diff.get("mismatches", []), start=1):
            lines.append(
                f"diff_{index}={mismatch.get('key', 'unknown')}|intent={mismatch.get('intent', 'unknown')}|webhook={mismatch.get('webhook', 'unknown')}"
            )
    else:
        lines.extend(["[diff]", "diff_mismatch_count=0"])

    lines.append("[timeline]")
    for index, row in enumerate(timeline_rows, start=1):
        context = _parse_support_context(row.get("support_context") or "")
        timestamp = row.get("timestamp")
        timestamp_value = timestamp.isoformat() if timestamp else "unknown"
        lines.extend(
            [
                f"timeline_{index}_title={row.get('title', 'unknown')}",
                f"timeline_{index}_status={row.get('status', 'unknown')}",
                f"timeline_{index}_timestamp={timestamp_value}",
                f"timeline_{index}_safe_error={row.get('error_text', '') or 'none'}",
                f"timeline_{index}_retry_available={bool(row.get('retry_available'))}",
                f"timeline_{index}_retry_tier={row.get('retry_tier', '') or 'none'}",
                f"timeline_{index}_provider={context.get('provider', 'unknown')}",
                f"timeline_{index}_event_id={context.get('event_id', 'unknown')}",
                f"timeline_{index}_idempotency_key={context.get('idempotency_key', 'unknown')}",
                f"timeline_{index}_provider_session_id={context.get('provider_session_id', 'unknown')}",
                f"timeline_{index}_tier={context.get('target_tier') or context.get('requested_tier') or 'unknown'}",
            ]
        )

    return "\n".join(lines)


def _build_webhook_reliability_sparkline(user, *, window=12):
    events = list(
        BillingWebhookEvent.objects.filter(user=user)
        .order_by("-processed_at", "-created_at", "-id")[:window]
    )
    if not events:
        return None

    points = []
    for event in reversed(events):
        event_ts = event.processed_at or event.created_at
        timestamp = event_ts.isoformat() if event_ts else "unknown"
        if event.status == BillingWebhookEvent.STATUS_PROCESSED:
            state = "success"
            text_class = "has-text-success"
        elif event.status == BillingWebhookEvent.STATUS_FAILED:
            state = "failed"
            text_class = "has-text-danger"
        else:
            state = "pending"
            text_class = "has-text-warning"

        points.append(
            {
                "event_id": event.provider_event_id or "unknown",
                "state": state,
                "text_class": text_class,
                "timestamp": timestamp,
            }
        )

    success_count = sum(1 for point in points if point["state"] == "success")
    failure_count = sum(1 for point in points if point["state"] == "failed")

    return {
        "points": points,
        "window": len(points),
        "success_count": success_count,
        "failure_count": failure_count,
    }


def _create_checkout_intent_for_user(*, user, provider_name: str, requested_tier: str, idempotency_key: str):
    adapter_cls = get_billing_provider_adapter(provider_name)
    if not adapter_cls:
        return None, None, "unsupported provider", 400

    valid_tiers = {choice[0] for choice in User.SUBSCRIPTION_CHOICES}
    premium_tiers = valid_tiers - {User.SUBSCRIPTION_FREE}
    if requested_tier not in premium_tiers:
        return None, None, "invalid premium subscription tier", 400

    intent, created = BillingCheckoutIntent.objects.get_or_create(
        user=user,
        provider=provider_name,
        idempotency_key=idempotency_key,
        defaults={
            "requested_tier": requested_tier,
            "status": BillingCheckoutIntent.STATUS_CREATED,
        },
    )

    if not created:
        if intent.requested_tier != requested_tier:
            return intent, True, "idempotency key already used with a different tier", 409
        return intent, True, "", 200

    result = adapter_cls.create_checkout_session(intent=intent, settings_obj=settings)
    if not result.success:
        intent.status = BillingCheckoutIntent.STATUS_FAILED
        intent.error_message = result.error_message or "Failed to create checkout session."
        intent.save(update_fields=["status", "error_message", "updated_at"])
        return intent, False, intent.error_message, 502

    intent.status = BillingCheckoutIntent.STATUS_SESSION_CREATED
    intent.provider_session_id = result.session_id
    intent.checkout_url = result.checkout_url
    intent.error_message = ""
    intent.save(
        update_fields=[
            "status",
            "provider_session_id",
            "checkout_url",
            "error_message",
            "updated_at",
        ]
    )
    return intent, False, "", 200


def _reconcile_checkout_intent_after_success(*, user, provider_name: str, idempotency_key: str, target_tier: str):
    intent = BillingCheckoutIntent.objects.filter(
        user=user,
        provider=provider_name,
        idempotency_key=idempotency_key,
    ).first()
    if not intent:
        return

    intent.status = BillingCheckoutIntent.STATUS_COMPLETED
    intent.error_message = ""
    if target_tier:
        intent.requested_tier = target_tier
    intent.save(update_fields=["status", "error_message", "requested_tier", "updated_at"])


class UserSignUp(CreateView):
    success_url = reverse_lazy('index')
    template_name = 'users/signup.html'
    form_class = UserCreationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.add_message(self.request, messages.SUCCESS, f"Signup success!")
        login(self.request, self.object)
        return response


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_object(self, *args, **kwargs):
        if "username" not in self.kwargs:
            return User.objects.get(username=self.request.user.username)
        else:
            return super().get_object(*args, **kwargs)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserChangeForm

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self):
        return User.objects.get(username=self.request.user.username)

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Your info was updated")
        return super().form_valid(form)


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("index")


class SubscriptionUpgradeView(LoginRequiredMixin, TemplateView):
    template_name = "users/subscription_upgrade.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        billing_status_filter = (self.request.GET.get("billing_status") or "all").strip().lower()
        if billing_status_filter not in {"all", "pending", "completed", "failed"}:
            billing_status_filter = "all"
        context["subscription_choices"] = User.SUBSCRIPTION_CHOICES
        context["current_tier"] = self.request.user.subscription_tier
        context["billing_timeline"] = _build_billing_timeline(
            self.request.user,
            limit=20,
            status_filter=billing_status_filter,
        )
        context["support_context_summary"] = _build_support_context_summary(self.request.user)
        context["support_context_diff"] = _build_support_context_diff(self.request.user)
        context["billing_health_indicator"] = _build_billing_health_indicator(self.request.user, window=8)
        context["billing_event_export_payload"] = _build_billing_event_export_payload(self.request.user, window=8)
        context["billing_webhook_sparkline"] = _build_webhook_reliability_sparkline(self.request.user, window=12)
        context["billing_status_filter"] = billing_status_filter
        return context

    def post(self, request, *args, **kwargs):
        tier = (request.POST.get("subscription_tier") or User.SUBSCRIPTION_FREE).strip()
        valid_tiers = {choice[0] for choice in User.SUBSCRIPTION_CHOICES}
        if tier not in valid_tiers:
            messages.error(request, "Invalid subscription tier.")
            return render(request, self.template_name, self.get_context_data())

        if tier != User.SUBSCRIPTION_FREE:
            intent, is_duplicate, error_message, status_code = _create_checkout_intent_for_user(
                user=request.user,
                provider_name="stripe",
                requested_tier=tier,
                idempotency_key=uuid4().hex,
            )
            if status_code != 200 or not intent:
                messages.error(request, _friendly_billing_error_message(error_message))
                return render(request, self.template_name, self.get_context_data())

            if intent.checkout_url:
                if is_duplicate:
                    messages.info(request, "Reusing existing checkout session.")
                else:
                    messages.info(request, "Redirecting to secure checkout for plan upgrade.")
                return redirect(intent.checkout_url)

            messages.error(request, "Checkout session did not return a redirect URL.")
            return render(request, self.template_name, self.get_context_data())

        request.user.subscription_tier = tier
        request.user.save(update_fields=["subscription_tier"])
        messages.success(request, "Subscription updated successfully.")
        return redirect("users:subscription-upgrade")


@require_GET
@login_required
def list_view(request):
    if request.user.is_staff:
        users = User.objects.all()
    else:
        users = User.objects.filter(is_staff=False)
    context = {"users": users}
    return render(request, "users/user_list.html", context=context)


class ListView(LoginRequiredMixin, View):  # Same functionality as list_view()
    def get(self, request):
        if request.user.is_staff:
            users = User.objects.all()
        else:
            users = User.objects.filter(is_staff=False)
        context = {"users": users}
        return render(request, "users/user_list.html", context=context)

    
class LogoutInterfaceView(LogoutView):
    template_name = 'users/logout.html'


@method_decorator(csrf_exempt, name="dispatch")
class BillingWebhookView(View):
    def post(self, request):
        provider_name = (request.headers.get("X-Billing-Provider") or "generic").strip().lower()
        adapter_cls = get_billing_provider_adapter(provider_name)
        if not adapter_cls:
            return JsonResponse({"ok": False, "error": "unsupported provider"}, status=400)

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": "invalid json payload"}, status=400)

        parsed = adapter_cls.parse_webhook_payload(
            payload,
            price_tier_map=getattr(settings, "BILLING_STRIPE_PRICE_TIER_MAP", {}),
        )
        if not parsed.idempotency_key:
            return JsonResponse({"ok": False, "error": "missing idempotency key"}, status=400)

        event, created = BillingWebhookEvent.objects.get_or_create(
            provider=provider_name,
            idempotency_key=parsed.idempotency_key,
            defaults={
                "provider_event_id": parsed.provider_event_id,
                "event_type": parsed.event_type,
                "target_tier": parsed.target_tier,
                "payload": parsed.raw_payload,
                "status": BillingWebhookEvent.STATUS_RECEIVED,
            },
        )
        if not created:
            return JsonResponse({"ok": True, "duplicate": True, "event_id": event.id})

        if provider_name == "stripe":
            stripe_signature = (request.headers.get("Stripe-Signature") or "").strip()
            stripe_secret = getattr(settings, "BILLING_WEBHOOK_SECRET_STRIPE", "") or getattr(
                settings,
                "BILLING_WEBHOOK_SECRET",
                "",
            )
            signature_valid = verify_stripe_webhook_signature(
                request.body,
                stripe_signature,
                stripe_secret,
                tolerance_seconds=getattr(settings, "BILLING_STRIPE_SIGNATURE_TOLERANCE_SECONDS", 300),
            )
        else:
            signature = (request.headers.get("X-Billing-Signature") or "").strip()
            secret = getattr(settings, "BILLING_WEBHOOK_SECRET", "")
            signature_valid = verify_webhook_signature(request.body, signature, secret)
        event.signature_valid = signature_valid
        if not signature_valid:
            event.status = BillingWebhookEvent.STATUS_FAILED
            event.error_message = "Invalid webhook signature."
            event.processed_at = timezone.now()
            event.save(update_fields=["signature_valid", "status", "error_message", "processed_at"])
            return JsonResponse({"ok": False, "error": "invalid signature"}, status=400)

        valid_tiers = {choice[0] for choice in User.SUBSCRIPTION_CHOICES}
        event_type = parsed.event_type or ""
        generic_supported_event_types = {
            "subscription.updated",
            "subscription.changed",
            "subscription.upgraded",
            "subscription.downgraded",
        }
        stripe_supported_event_types = {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "checkout.session.completed",
        }
        supported_event_types = stripe_supported_event_types if provider_name == "stripe" else generic_supported_event_types
        if event_type not in supported_event_types:
            event.status = BillingWebhookEvent.STATUS_IGNORED
            event.error_message = "Event type ignored by handler."
            event.processed_at = timezone.now()
            event.save(update_fields=["signature_valid", "status", "error_message", "processed_at"])
            return JsonResponse({"ok": True, "status": "ignored"})

        if not parsed.user_email:
            event.status = BillingWebhookEvent.STATUS_FAILED
            event.error_message = "Missing user email in webhook payload."
            event.processed_at = timezone.now()
            event.save(update_fields=["signature_valid", "status", "error_message", "processed_at"])
            return JsonResponse({"ok": False, "error": "missing user email"}, status=400)

        user = User.objects.filter(email=parsed.user_email).first()
        if not user:
            event.status = BillingWebhookEvent.STATUS_FAILED
            event.error_message = "No user found for provided email."
            event.processed_at = timezone.now()
            event.save(update_fields=["signature_valid", "status", "error_message", "processed_at"])
            return JsonResponse({"ok": False, "error": "user not found"}, status=404)

        if parsed.target_tier not in valid_tiers:
            event.user = user
            event.status = BillingWebhookEvent.STATUS_FAILED
            event.error_message = "Invalid subscription tier in payload."
            event.processed_at = timezone.now()
            event.save(update_fields=["user", "signature_valid", "status", "error_message", "processed_at"])
            return JsonResponse({"ok": False, "error": "invalid subscription tier"}, status=400)

        user.subscription_tier = parsed.target_tier
        user.save(update_fields=["subscription_tier"])

        event.user = user
        event.target_tier = parsed.target_tier
        event.status = BillingWebhookEvent.STATUS_PROCESSED
        event.error_message = ""
        event.processed_at = timezone.now()
        event.save(
            update_fields=[
                "user",
                "target_tier",
                "signature_valid",
                "status",
                "error_message",
                "processed_at",
            ]
        )

        _reconcile_checkout_intent_after_success(
            user=user,
            provider_name=provider_name,
            idempotency_key=parsed.idempotency_key,
            target_tier=parsed.target_tier,
        )
        return JsonResponse({"ok": True, "status": "processed"})


class BillingCheckoutSessionCreateView(LoginRequiredMixin, View):
    def post(self, request):
        provider_name = (request.POST.get("provider") or "stripe").strip().lower()
        requested_tier = (request.POST.get("subscription_tier") or "").strip()
        idempotency_key = (request.POST.get("idempotency_key") or "").strip() or uuid4().hex

        intent, is_duplicate, error_message, status_code = _create_checkout_intent_for_user(
            user=request.user,
            provider_name=provider_name,
            requested_tier=requested_tier,
            idempotency_key=idempotency_key,
        )

        if status_code != 200 or not intent:
            safe_error = _friendly_billing_error_message(error_message)
            return JsonResponse(
                {
                    "ok": False,
                    "intent_id": intent.id if intent else None,
                    "status": intent.status if intent else "failed",
                    "error": safe_error,
                },
                status=status_code,
            )

        return JsonResponse(
            {
                "ok": True,
                "duplicate": is_duplicate,
                "intent_id": intent.id,
                "status": intent.status,
                "checkout_url": intent.checkout_url,
            }
        )
