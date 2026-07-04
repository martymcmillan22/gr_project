import hashlib
import hmac
from dataclasses import dataclass
import time
from uuid import uuid4


@dataclass
class BillingWebhookEventPayload:
    provider: str
    provider_event_id: str
    idempotency_key: str
    event_type: str
    user_email: str
    target_tier: str
    raw_payload: dict


@dataclass
class BillingCheckoutSessionResult:
    success: bool
    session_id: str = ""
    checkout_url: str = ""
    error_message: str = ""


class GenericBillingProviderAdapter:
    provider_name = "generic"

    @classmethod
    def parse_webhook_payload(cls, payload: dict, **_kwargs) -> BillingWebhookEventPayload:
        event_id = str(payload.get("event_id") or payload.get("id") or "")
        idempotency_key = str(payload.get("idempotency_key") or event_id or "")
        event_type = str(payload.get("event_type") or payload.get("type") or "")

        data = payload.get("data") or {}
        user_email = str(data.get("email") or data.get("user_email") or payload.get("user_email") or "")
        target_tier = str(data.get("subscription_tier") or data.get("tier") or payload.get("subscription_tier") or "")

        return BillingWebhookEventPayload(
            provider=cls.provider_name,
            provider_event_id=event_id,
            idempotency_key=idempotency_key,
            event_type=event_type,
            user_email=user_email,
            target_tier=target_tier,
            raw_payload=payload,
        )

    @classmethod
    def create_checkout_session(cls, *, intent, settings_obj) -> BillingCheckoutSessionResult:
        token = uuid4().hex
        return BillingCheckoutSessionResult(
            success=True,
            session_id=f"generic_{token}",
            checkout_url=f"/users/subscription/upgrade/?billing_intent={intent.id}",
        )


class StripeBillingProviderAdapter:
    provider_name = "stripe"

    @classmethod
    def parse_webhook_payload(cls, payload: dict, *, price_tier_map=None) -> BillingWebhookEventPayload:
        price_tier_map = price_tier_map or {}

        event_id = str(payload.get("id") or "")
        request_payload = payload.get("request") or {}
        idempotency_key = str(request_payload.get("idempotency_key") or event_id or "")
        event_type = str(payload.get("type") or "")

        data_object = ((payload.get("data") or {}).get("object") or {})
        metadata = data_object.get("metadata") or {}

        user_email = str(
            data_object.get("customer_email")
            or ((data_object.get("customer_details") or {}).get("email"))
            or metadata.get("user_email")
            or metadata.get("email")
            or ""
        )

        target_tier = str(metadata.get("subscription_tier") or metadata.get("target_tier") or "")

        if not target_tier and event_type == "customer.subscription.deleted":
            target_tier = "free"

        if not target_tier:
            items = ((data_object.get("items") or {}).get("data") or [])
            if items:
                first_item = items[0] or {}
                price_id = str(((first_item.get("price") or {}).get("id")) or "")
                if price_id:
                    target_tier = str(price_tier_map.get(price_id) or "")

        return BillingWebhookEventPayload(
            provider=cls.provider_name,
            provider_event_id=event_id,
            idempotency_key=idempotency_key,
            event_type=event_type,
            user_email=user_email,
            target_tier=target_tier,
            raw_payload=payload,
        )

    @classmethod
    def create_checkout_session(cls, *, intent, settings_obj) -> BillingCheckoutSessionResult:
        stripe_secret_key = getattr(settings_obj, "BILLING_STRIPE_SECRET_KEY", "")
        if not stripe_secret_key:
            return BillingCheckoutSessionResult(success=False, error_message="Stripe secret key is not configured.")

        price_tier_map = getattr(settings_obj, "BILLING_STRIPE_PRICE_TIER_MAP", {}) or {}
        tier_price_map = {tier: price for price, tier in price_tier_map.items()}
        price_id = tier_price_map.get(intent.requested_tier)
        if not price_id:
            return BillingCheckoutSessionResult(
                success=False,
                error_message="No Stripe price mapping configured for requested tier.",
            )

        try:
            import stripe
        except ImportError:
            return BillingCheckoutSessionResult(success=False, error_message="Stripe SDK is not installed.")

        stripe.api_key = stripe_secret_key

        success_url = getattr(settings_obj, "BILLING_CHECKOUT_SUCCESS_URL", "http://localhost:8000/users/subscription/upgrade/?checkout=success")
        cancel_url = getattr(settings_obj, "BILLING_CHECKOUT_CANCEL_URL", "http://localhost:8000/users/subscription/upgrade/?checkout=cancel")

        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                customer_email=intent.user.email,
                client_reference_id=str(intent.user_id),
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_email": intent.user.email,
                    "subscription_tier": intent.requested_tier,
                    "idempotency_key": intent.idempotency_key,
                    "intent_id": str(intent.id),
                },
                payment_method_types=["card"],
                allow_promotion_codes=True,
                subscription_data={
                    "metadata": {
                        "user_email": intent.user.email,
                        "subscription_tier": intent.requested_tier,
                        "idempotency_key": intent.idempotency_key,
                        "intent_id": str(intent.id),
                    }
                },
                idempotency_key=intent.idempotency_key,
            )
        except Exception as exc:
            return BillingCheckoutSessionResult(success=False, error_message=str(exc))

        return BillingCheckoutSessionResult(
            success=True,
            session_id=str(getattr(session, "id", "")),
            checkout_url=str(getattr(session, "url", "")),
        )


def get_billing_provider_adapter(provider_name: str):
    normalized = (provider_name or "generic").strip().lower()
    if normalized == "generic":
        return GenericBillingProviderAdapter
    if normalized == "stripe":
        return StripeBillingProviderAdapter
    return None


def verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return False

    computed = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, (signature or "").strip())


def verify_stripe_webhook_signature(
    raw_body: bytes,
    signature_header: str,
    secret: str,
    *,
    tolerance_seconds: int = 300,
    now_timestamp: int | None = None,
) -> bool:
    if not secret or not signature_header:
        return False

    parts = {}
    for entry in signature_header.split(","):
        if "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        parts[key.strip()] = value.strip()

    timestamp_raw = parts.get("t")
    signature_v1 = parts.get("v1")
    if not timestamp_raw or not signature_v1:
        return False

    try:
        timestamp = int(timestamp_raw)
    except (TypeError, ValueError):
        return False

    current_time = int(now_timestamp if now_timestamp is not None else time.time())
    if abs(current_time - timestamp) > tolerance_seconds:
        return False

    signed_payload = f"{timestamp}.{raw_body.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_v1)
