from functools import wraps
from datetime import date, datetime, timedelta
from collections import Counter
from decimal import Decimal
import hashlib
from io import BytesIO
import re
from urllib.parse import urlencode

from django.apps import apps
from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry
from django.core import signing
from django.core.mail import send_mail
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from .admin_analytics import build_admin_metrics


CONTRACT_RELEASE_DATE = date(2026, 6, 28)
CONTRACT_STABILITY_WINDOW_DAYS = 90
CURRENT_SCHEMA_VERSION = "1.1.0"
BILLING_ACCESS_SALT = "platform_core.billing_access"
BILLING_ACCESS_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
BILLING_ACCESS_DEFAULT_TTL_DAYS = 7
BILLING_NOTIFICATION_RETRY_DELAY_MINUTES = 60


def _int_param(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed


def _billing_console_redirect(
    tenant_key="",
    client_key="",
    link_tenant="",
    link_client="",
    link_status="",
    link_expires="",
    link_sort="",
):
    params = {}
    if tenant_key:
        params["billing_tenant"] = tenant_key
    if client_key:
        params["billing_client"] = client_key
    if link_tenant:
        params["billing_link_tenant"] = link_tenant
    if link_client:
        params["billing_link_client"] = link_client
    if link_status:
        params["billing_link_status"] = link_status
    if link_expires:
        params["billing_link_expires"] = link_expires
    if link_sort:
        params["billing_link_sort"] = link_sort
    query = urlencode(params)
    suffix = f"?{query}" if query else ""
    return HttpResponseRedirect(f"/admin/basetrue-insights/{suffix}#bt-ins-billing")


def _version_key(version):
    parts = (version or "0.0.0").split(".")
    normalized = []
    for part in parts[:3]:
        try:
            normalized.append(int(part))
        except ValueError:
            normalized.append(0)
    while len(normalized) < 3:
        normalized.append(0)
    return tuple(normalized)


def _parse_schema_versions(raw):
    versions = []
    seen = set()
    for part in (raw or "").split(","):
        value = part.strip()
        if value and value not in seen:
            versions.append(value)
            seen.add(value)
    return versions


def _schema_version_aliases(catalog):
    ordered_versions = sorted(catalog.keys(), key=_version_key, reverse=True)
    active_versions = [
        version
        for version in ordered_versions
        if catalog.get(version, {}).get("lifecycle_state") == "active"
    ]
    supported_versions = [
        version
        for version in ordered_versions
        if catalog.get(version, {}).get("lifecycle_state") in {"active", "deprecated"}
    ]
    deprecated_versions = [
        version
        for version in ordered_versions
        if catalog.get(version, {}).get("lifecycle_state") == "deprecated"
    ]

    latest = ordered_versions[0] if ordered_versions else CURRENT_SCHEMA_VERSION
    stable = active_versions[0] if active_versions else CURRENT_SCHEMA_VERSION
    lts = deprecated_versions[0] if deprecated_versions else stable

    aliases = {
        "current": CURRENT_SCHEMA_VERSION,
        "stable": stable,
        "lts": lts,
        "latest": latest,
    }
    if supported_versions:
        aliases["safe"] = supported_versions[0]
    return aliases


def _resolve_schema_version_alias(value, catalog):
    normalized = (value or "").strip().lower()
    if not normalized:
        return ""
    aliases = _schema_version_aliases(catalog)
    return aliases.get(normalized, value.strip())


def _parse_bool(value):
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _parse_capability_tokens(raw):
    return {
        token.strip().lower()
        for token in (raw or "").split(",")
        if token.strip()
    }


def _client_profile_defaults(client_name, tenant_key="default"):
    if not client_name:
        return None

    try:
        from .models import ClientContractProfile
    except Exception:
        return None

    profile = ClientContractProfile.objects.filter(
        tenant_key=tenant_key or "default",
        client_key=client_name,
        is_active=True,
    ).first()
    if not profile:
        return None

    return {
        "tenant_key": profile.tenant_key,
        "client_key": profile.client_key,
        "default_schema_version": (profile.default_schema_version or "").strip(),
        "capabilities": sorted(_parse_capability_tokens(profile.default_capabilities)),
        "strict_negotiation": bool(profile.strict_negotiation),
        "strict_payload_shape": bool(profile.strict_payload_shape),
    }


def _merge_profile_defaults(
    request,
    tenant_key,
    client_name,
    requested_default_schema_version,
    capability_tokens,
    strict_negotiation,
    strict_payload_shape,
):
    defaults = _client_profile_defaults(client_name, tenant_key=tenant_key)
    if not defaults:
        return {
            "default_schema_version": requested_default_schema_version,
            "capability_tokens": capability_tokens,
            "strict_negotiation": strict_negotiation,
            "strict_payload_shape": strict_payload_shape,
            "profile": None,
        }

    if "default_schema_version" not in request.GET and defaults.get("default_schema_version"):
        requested_default_schema_version = defaults["default_schema_version"]
    if "capabilities" not in request.GET and defaults.get("capabilities"):
        capability_tokens = set(defaults["capabilities"])
    if "strict_negotiation" not in request.GET:
        strict_negotiation = defaults.get("strict_negotiation", False)
    if "strict_payload_shape" not in request.GET:
        strict_payload_shape = defaults.get("strict_payload_shape", False)

    return {
        "default_schema_version": requested_default_schema_version,
        "capability_tokens": capability_tokens,
        "strict_negotiation": strict_negotiation,
        "strict_payload_shape": strict_payload_shape,
        "profile": defaults,
    }


def _schema_compatibility_matrix():
    return {
        "legacy_csv_bridge": {
            "supported_versions": ["1.0.0"],
            "preferred_version": "1.0.0",
            "notes": "Legacy consumers should stay pinned to v1.0.0 until upgraded.",
        },
        "executive_dashboard_widgets": {
            "supported_versions": ["1.0.0", "1.1.0"],
            "preferred_version": "1.1.0",
            "notes": "Widget set supports roadmap references introduced in v1.1.0.",
        },
        "migration_tooling_bundle_export": {
            "supported_versions": ["1.0.0", "1.1.0", "2.0.0"],
            "preferred_version": "1.1.0",
            "notes": "Use multi-version bundle exports for cross-version migration checks.",
        },
        "contract_sdk_generator": {
            "supported_versions": ["1.1.0", "2.0.0"],
            "preferred_version": "1.1.0",
            "notes": "Prefer stable v1.1.0; v2.0.0 is experimental.",
        },
    }


def _schema_negotiation_hint(catalog, client="", capabilities=None, preferred_default=""):
    capabilities = set(capabilities or [])
    compatibility = _schema_compatibility_matrix()
    client_info = compatibility.get(client or "", {})

    ordered_versions = sorted(catalog.keys(), key=_version_key, reverse=True)
    stable_versions = [
        version
        for version in ordered_versions
        if catalog.get(version, {}).get("lifecycle_state") in {"active", "deprecated"}
    ]
    active_versions = [
        version
        for version in ordered_versions
        if catalog.get(version, {}).get("lifecycle_state") == "active"
    ]

    recommended = active_versions[0] if active_versions else CURRENT_SCHEMA_VERSION
    reasons = ["Selected highest active schema version by default."]

    preferred_from_client = client_info.get("preferred_version")
    if preferred_from_client in catalog:
        recommended = preferred_from_client
        reasons = [f"Client '{client}' prefers schema version {preferred_from_client}."]

    if preferred_default in catalog:
        recommended = preferred_default
        reasons.append("Client provided a default schema pin.")

    if "legacy_only" in capabilities and "1.0.0" in catalog:
        recommended = "1.0.0"
        reasons.append("Capability 'legacy_only' requires the legacy contract.")

    if "roadmap_ref" in capabilities and _version_key(recommended) < _version_key("1.1.0"):
        if "1.1.0" in catalog:
            recommended = "1.1.0"
            reasons.append("Capability 'roadmap_ref' requires v1.1.0+.")

    if "experimental_fields" in capabilities and "2.0.0" in catalog:
        recommended = "2.0.0"
        reasons.append("Capability 'experimental_fields' opts into v2.0.0.")

    if "stable_only" in capabilities and catalog.get(recommended, {}).get("lifecycle_state") == "experimental":
        if stable_versions:
            recommended = stable_versions[0]
            reasons.append("Capability 'stable_only' excludes experimental versions.")

    if client_info.get("supported_versions"):
        allowed = set(client_info["supported_versions"])
        if recommended not in allowed:
            fallback = next((version for version in ordered_versions if version in allowed), None)
            if fallback:
                recommended = fallback
                reasons.append("Adjusted to the client's compatibility matrix.")

    return {
        "client": client or "generic",
        "capabilities": sorted(capabilities),
        "recommended_version": recommended,
        "lifecycle_state": catalog.get(recommended, {}).get("lifecycle_state", "unknown"),
        "reasons": reasons,
    }


def _version_matches_capabilities(version, catalog, client="", capabilities=None):
    capabilities = set(capabilities or [])
    contract = catalog.get(version, {})
    if not contract:
        return False
    if not contract.get("export_enabled", True):
        return False

    lifecycle_state = contract.get("lifecycle_state", "unknown")
    if "legacy_only" in capabilities and version != "1.0.0":
        return False
    if "roadmap_ref" in capabilities and _version_key(version) < _version_key("1.1.0"):
        return False
    if "experimental_fields" in capabilities and _version_key(version) < _version_key("2.0.0"):
        return False
    if "stable_only" in capabilities and lifecycle_state in {"experimental", "sunset"}:
        return False

    client_info = _schema_compatibility_matrix().get(client or "", {})
    supported = set(client_info.get("supported_versions", []))
    if supported and version not in supported:
        return False
    return True


def _select_schema_version(
    catalog,
    requested_schema_version="",
    preferred_default="",
    client="",
    capabilities=None,
    strict=False,
):
    requested = (requested_schema_version or "").strip().lower()
    if requested in {"auto", "negotiate", "best"}:
        requested = ""

    if requested:
        resolved_requested = _resolve_schema_version_alias(requested, catalog)
        if resolved_requested not in catalog:
            return {
                "ok": False,
                "error": "Unsupported schema_version",
                "requested": requested_schema_version,
                "available_versions": sorted(catalog.keys()),
            }

        if strict and not _version_matches_capabilities(
            resolved_requested,
            catalog,
            client=client,
            capabilities=capabilities,
        ):
            return {
                "ok": False,
                "error": "Requested schema_version incompatible with strict negotiation constraints",
                "requested": requested_schema_version,
                "available_versions": sorted(catalog.keys()),
            }

        return {
            "ok": True,
            "selected_version": resolved_requested,
            "source": "explicit",
            "negotiation": _schema_negotiation_hint(
                catalog,
                client=client,
                capabilities=capabilities,
                preferred_default=preferred_default,
            ),
        }

    hint = _schema_negotiation_hint(
        catalog,
        client=client,
        capabilities=capabilities,
        preferred_default=preferred_default,
    )
    selected = hint.get("recommended_version") or preferred_default or CURRENT_SCHEMA_VERSION
    if selected not in catalog:
        return {
            "ok": False,
            "error": "Unable to negotiate schema_version",
            "requested": requested_schema_version,
            "available_versions": sorted(catalog.keys()),
        }

    if strict:
        ordered_versions = sorted(catalog.keys(), key=_version_key, reverse=True)
        preferred_order = []
        if selected in ordered_versions:
            preferred_order.append(selected)
        preferred_order.extend(version for version in ordered_versions if version not in preferred_order)

        strict_match = next(
            (
                version
                for version in preferred_order
                if _version_matches_capabilities(
                    version,
                    catalog,
                    client=client,
                    capabilities=capabilities,
                )
            ),
            None,
        )
        if not strict_match:
            return {
                "ok": False,
                "error": "No compatible schema_version for strict negotiation",
                "requested": requested_schema_version,
                "available_versions": sorted(catalog.keys()),
            }
        selected = strict_match

    return {
        "ok": True,
        "selected_version": selected,
        "source": "negotiated-strict" if strict else "negotiated",
        "negotiation": hint,
    }


def _resolve_default_schema_version(catalog, requested_default=""):
    candidate = _resolve_schema_version_alias((requested_default or "").strip(), catalog) or CURRENT_SCHEMA_VERSION
    if candidate not in catalog:
        return None
    return candidate


def _shape_payload_for_contract(payload, contract, strict_payload_shape=False):
    if not strict_payload_shape:
        return payload

    required_fields = contract.get("required_fields", [])
    optional_fields = contract.get("optional_fields", [])
    shaped = {}

    for field in required_fields:
        shaped[field] = payload.get(field)

    for field in optional_fields:
        if field in payload:
            shaped[field] = payload[field]

    return shaped


def _billing_access_link_expires_at(ttl_days=BILLING_ACCESS_DEFAULT_TTL_DAYS):
    try:
        ttl_value = int(ttl_days or BILLING_ACCESS_DEFAULT_TTL_DAYS)
    except (TypeError, ValueError):
        ttl_value = BILLING_ACCESS_DEFAULT_TTL_DAYS
    if ttl_value <= 0:
        ttl_value = BILLING_ACCESS_DEFAULT_TTL_DAYS
    return timezone.now() + timedelta(days=ttl_value)


def _create_signed_billing_access_token(link_key, tenant_key, client_key, window_days=30):
    payload = {
        "tenant": tenant_key or "default",
        "client": client_key or "all",
        "window_days": int(window_days or 30),
        "link_key": link_key,
    }
    return signing.dumps(payload, salt=BILLING_ACCESS_SALT)


def _issue_billing_access_link(
    tenant_key,
    client_key,
    window_days=30,
    created_by=None,
    label="",
    recipient_email="",
    ttl_days=BILLING_ACCESS_DEFAULT_TTL_DAYS,
    reuse_existing=True,
):
    try:
        from .models import ContractBillingAccessLink
    except Exception:
        return None

    now = timezone.now()
    queryset = ContractBillingAccessLink.objects.filter(
        tenant_key=tenant_key or "default",
        client_key=client_key or "all",
        window_days=int(window_days or 30),
        is_active=True,
        revoked_at__isnull=True,
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
    if label:
        queryset = queryset.filter(label=label)
    if recipient_email:
        queryset = queryset.filter(recipient_email=recipient_email)

    link = queryset.order_by("-created_at").first() if reuse_existing else None
    if link is None:
        link = ContractBillingAccessLink.objects.create(
            tenant_key=tenant_key or "default",
            client_key=client_key or "all",
            window_days=int(window_days or 30),
            label=label or "Customer billing portal",
            recipient_email=recipient_email or "",
            created_by=created_by,
            expires_at=_billing_access_link_expires_at(ttl_days=ttl_days),
        )
    return link


def _billing_access_link_status(link):
    if not link:
        return "legacy"
    if link.revoked_at or not link.is_active:
        return "revoked"
    if link.expires_at and link.expires_at <= timezone.now():
        return "expired"
    return "active"


def _billing_access_token(
    tenant_key,
    client_key,
    window_days=30,
    created_by=None,
    label="",
    recipient_email="",
    ttl_days=BILLING_ACCESS_DEFAULT_TTL_DAYS,
    reuse_existing=True,
):
    link = _issue_billing_access_link(
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=window_days,
        created_by=created_by,
        label=label,
        recipient_email=recipient_email,
        ttl_days=ttl_days,
        reuse_existing=reuse_existing,
    )
    if not link:
        payload = {
            "tenant": tenant_key or "default",
            "client": client_key or "all",
            "window_days": int(window_days or 30),
        }
        return signing.dumps(payload, salt=BILLING_ACCESS_SALT)
    return _create_signed_billing_access_token(link.link_key, tenant_key, client_key, window_days=window_days)


def _billing_access_link_from_token(token, tenant_key, client_key, window_days=30, max_age=BILLING_ACCESS_MAX_AGE_SECONDS):
    if not token:
        return None, None
    try:
        payload = signing.loads(token, salt=BILLING_ACCESS_SALT, max_age=max_age)
    except signing.BadSignature:
        return None, None

    tenant_match = payload.get("tenant") == (tenant_key or "default")
    client_match = payload.get("client") == (client_key or "all")
    window_match = int(payload.get("window_days") or 30) == int(window_days or 30)
    if not (tenant_match and client_match and window_match):
        return None, None

    link_key = payload.get("link_key")
    if not link_key:
        return None, payload

    try:
        from .models import ContractBillingAccessLink
    except Exception:
        return None, payload

    link = ContractBillingAccessLink.objects.filter(
        link_key=link_key,
        tenant_key=tenant_key or "default",
        client_key=client_key or "all",
        window_days=int(window_days or 30),
    ).first()
    return link, payload


def _verify_billing_access_token(token, tenant_key, client_key, window_days=30, max_age=BILLING_ACCESS_MAX_AGE_SECONDS):
    if not token:
        return False
    link, payload = _billing_access_link_from_token(
        token,
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=window_days,
        max_age=max_age,
    )
    if payload is None:
        return False
    if link is None:
        return True
    if _billing_access_link_status(link) != "active":
        return False
    link.last_used_at = timezone.now()
    link.use_count = int(link.use_count or 0) + 1
    link.save(update_fields=["last_used_at", "use_count", "updated_at"])
    return True


def _billing_access_link_payload(link, token=""):
    if not link:
        return {}
    now = timezone.now()
    expires_in_days = None
    if link.expires_at:
        expires_in_days = int((link.expires_at - now).total_seconds() // 86400)
    status = _billing_access_link_status(link)
    if status == "revoked":
        expiry_badge_key = "red"
        expiry_badge_label = "Revoked"
    elif status == "expired":
        expiry_badge_key = "red"
        expiry_badge_label = "Expired"
    elif expires_in_days is None:
        expiry_badge_key = "blue"
        expiry_badge_label = "No expiry"
    elif expires_in_days <= 1:
        expiry_badge_key = "yellow"
        expiry_badge_label = "Under 24h"
    elif expires_in_days <= 3:
        expiry_badge_key = "yellow"
        expiry_badge_label = f"{expires_in_days}d left"
    else:
        expiry_badge_key = "green"
        expiry_badge_label = f"{expires_in_days}d left"

    if status == "active":
        status_badge_key = "green"
    elif status == "legacy":
        status_badge_key = "blue"
    else:
        status_badge_key = "red"

    signed_token = token or _create_signed_billing_access_token(
        link.link_key,
        link.tenant_key,
        link.client_key,
        window_days=link.window_days,
    )
    base_query = (
        f"tenant={link.tenant_key}&client={link.client_key}"
        f"&window_days={link.window_days}&access_token={signed_token}"
    )
    return {
        "id": link.id,
        "created_at": link.created_at.isoformat() if link.created_at else "",
        "label": link.label,
        "tenant_key": link.tenant_key,
        "client_key": link.client_key,
        "window_days": link.window_days,
        "recipient_email": link.recipient_email,
        "status": status,
        "status_badge_key": status_badge_key,
        "expires_at": link.expires_at.isoformat() if link.expires_at else "",
        "expires_in_days": expires_in_days,
        "expiry_badge_key": expiry_badge_key,
        "expiry_badge_label": expiry_badge_label,
        "revoked_at": link.revoked_at.isoformat() if link.revoked_at else "",
        "last_used_at": link.last_used_at.isoformat() if link.last_used_at else "",
        "use_count": int(link.use_count or 0),
        "token": signed_token,
        "customer_billing_url": f"/contracts/billing/?{base_query}",
        "invoice_center_url": f"/contracts/billing/invoices/?{base_query}",
        "invoice_pdf_url": f"/contracts/billing/invoice/?{base_query}&format=pdf",
        "revoke_url": f"/admin/insights-contract-billing-access-links/?action=revoke&link_id={link.id}",
    }


def _billing_access_links_payload(
    tenant_key="",
    client_key="",
    window_days=None,
    limit=12,
    status_filter="all",
    expires_filter="all",
    sort_by="newest",
):
    try:
        from .models import ContractBillingAccessLink
    except Exception:
        return []

    queryset = ContractBillingAccessLink.objects.all()
    if tenant_key:
        queryset = queryset.filter(tenant_key=tenant_key)
    if client_key:
        queryset = queryset.filter(client_key=client_key)
    if window_days:
        queryset = queryset.filter(window_days=window_days)
    links = [
        _billing_access_link_payload(link)
        for link in queryset.order_by("-created_at")[:limit]
    ]

    normalized_status = (status_filter or "all").strip().lower()
    if normalized_status in {"active", "revoked", "expired", "legacy"}:
        links = [row for row in links if (row.get("status") or "").lower() == normalized_status]

    normalized_expires = (expires_filter or "all").strip().lower()
    if normalized_expires == "soon":
        links = [
            row for row in links
            if isinstance(row.get("expires_in_days"), int) and 0 <= row.get("expires_in_days") <= 3
        ]
    elif normalized_expires == "expired":
        links = [
            row for row in links
            if isinstance(row.get("expires_in_days"), int) and row.get("expires_in_days") < 0
        ]
    elif normalized_expires == "no_expiry":
        links = [row for row in links if row.get("expires_in_days") is None]

    normalized_sort = (sort_by or "newest").strip().lower()
    if normalized_sort == "oldest":
        links.sort(key=lambda row: row.get("created_at") or "")
    elif normalized_sort == "expires_soonest":
        links.sort(
            key=lambda row: (
                row.get("expires_in_days") is None,
                row.get("expires_in_days") if isinstance(row.get("expires_in_days"), int) else 10**9,
                row.get("created_at") or "",
            )
        )
    elif normalized_sort == "expires_latest":
        links.sort(
            key=lambda row: (
                row.get("expires_in_days") is None,
                -row.get("expires_in_days") if isinstance(row.get("expires_in_days"), int) else -10**9,
                row.get("created_at") or "",
            )
        )
    elif normalized_sort == "most_used":
        links.sort(key=lambda row: (-int(row.get("use_count") or 0), row.get("created_at") or ""))
    elif normalized_sort == "least_used":
        links.sort(key=lambda row: (int(row.get("use_count") or 0), row.get("created_at") or ""))
    else:
        links.sort(key=lambda row: row.get("created_at") or "", reverse=True)

    return links


def _billing_access_link_analytics_payload(
    tenant_key="",
    client_key="",
    window_days=None,
    status_filter="all",
    expires_filter="all",
):
    links = _billing_access_links_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=window_days,
        limit=500,
        status_filter=status_filter,
        expires_filter=expires_filter,
        sort_by="newest",
    )
    total_links = len(links)
    status_counts = Counter((row.get("status") or "legacy") for row in links)
    total_uses = sum(int(row.get("use_count") or 0) for row in links)
    used_links = sum(1 for row in links if int(row.get("use_count") or 0) > 0)
    expiring_soon = sum(
        1
        for row in links
        if isinstance(row.get("expires_in_days"), int) and 0 <= row.get("expires_in_days") <= 3
    )
    tenant_counts = Counter((row.get("tenant_key") or "unknown") for row in links)
    client_counts = Counter((row.get("client_key") or "unknown") for row in links)
    last_activity = max(
        ((row.get("last_used_at") or row.get("created_at") or "") for row in links),
        default="",
    )

    top_tenant = ""
    if tenant_counts:
        top_tenant = tenant_counts.most_common(1)[0][0]
    top_client = ""
    if client_counts:
        top_client = client_counts.most_common(1)[0][0]

    return {
        "total_links": total_links,
        "active_links": int(status_counts.get("active", 0)),
        "revoked_links": int(status_counts.get("revoked", 0)),
        "expired_links": int(status_counts.get("expired", 0)),
        "legacy_links": int(status_counts.get("legacy", 0)),
        "expiring_soon": expiring_soon,
        "total_uses": total_uses,
        "used_links": used_links,
        "never_used_links": max(total_links - used_links, 0),
        "avg_uses": round((total_uses / total_links), 2) if total_links else 0,
        "top_tenant": top_tenant,
        "top_client": top_client,
        "last_activity_at": last_activity,
    }


def _invoice_number_for(tenant_key, client_key, period_end):
    stamp = period_end.strftime("%Y%m")
    client_token = hashlib.sha1(f"{tenant_key}:{client_key}".encode("utf-8")).hexdigest()[:8].upper()
    return f"INV-{stamp}-{client_token}"


def _invoice_signature_for(invoice_payload):
    return signing.dumps(invoice_payload, salt="platform_core.invoice_artifact")


def _client_billing_profile(tenant_key="default", client_key=""):
    default_profile = {
        "billing_plan": "standard",
        "monthly_event_allowance": 1000,
        "overage_rate": Decimal("0.0100"),
    }
    if not client_key:
        return default_profile

    try:
        from .models import ClientContractProfile
    except Exception:
        return default_profile

    profile = ClientContractProfile.objects.filter(
        tenant_key=tenant_key or "default",
        client_key=client_key,
        is_active=True,
    ).first()
    if not profile:
        return default_profile

    return {
        "billing_contact_email": profile.billing_contact_email or "",
        "billing_plan": profile.billing_plan or "standard",
        "monthly_event_allowance": int(profile.monthly_event_allowance or 0),
        "overage_rate": profile.overage_rate,
    }


def _billing_dimensions(
    endpoint,
    output_format="",
    strict_negotiation=False,
    strict_payload_shape=False,
    selected_schema_version="",
):
    units = 1
    if endpoint == "export":
        units = 2 if output_format == "json" else 1
    elif endpoint == "negotiate":
        units = 1
    elif endpoint == "schema":
        units = 1
    elif endpoint == "usage_analytics":
        units = 1
    elif endpoint == "billing_summary":
        units = 0

    if strict_negotiation:
        units += 1
    if strict_payload_shape:
        units += 1
    if selected_schema_version and _version_key(selected_schema_version) >= _version_key("2.0.0"):
        units += 1

    category = "contract_api"
    if endpoint in {"usage_analytics", "billing_summary"}:
        category = "control_plane"
    return {
        "billable_units": max(units, 0),
        "billable_category": category,
    }


def _record_contract_usage(
    endpoint,
    tenant_key="default",
    client_key="",
    requested_schema_version="",
    selected_schema_version="",
    negotiation_source="",
    strict_negotiation=False,
    strict_payload_shape=False,
    period="",
    output_format="",
    status_code=200,
):
    try:
        from .models import ContractUsageEvent

        billing_profile = _client_billing_profile(tenant_key=tenant_key, client_key=client_key)
        billing = _billing_dimensions(
            endpoint=endpoint,
            output_format=output_format,
            strict_negotiation=strict_negotiation,
            strict_payload_shape=strict_payload_shape,
            selected_schema_version=selected_schema_version,
        )
        billable_units = billing["billable_units"]
        billable_amount = Decimal(billable_units) * billing_profile["overage_rate"]

        ContractUsageEvent.objects.create(
            tenant_key=(tenant_key or "default"),
            client_key=(client_key or "anonymous"),
            endpoint=endpoint,
            billable_category=billing["billable_category"],
            billable_units=billable_units,
            billable_amount=billable_amount,
            requested_schema_version=requested_schema_version,
            selected_schema_version=selected_schema_version,
            negotiation_source=negotiation_source,
            strict_negotiation=bool(strict_negotiation),
            strict_payload_shape=bool(strict_payload_shape),
            period=period,
            output_format=output_format,
            status_code=int(status_code),
        )
    except Exception:
        return


def _contract_usage_analytics_payload(window_days=30, tenant_key=""):
    try:
        from .models import ContractUsageEvent
    except Exception:
        return {
            "window_days": window_days,
            "total_events": 0,
            "status_breakdown": {},
            "top_clients": [],
            "endpoint_breakdown": [],
            "notes": "Usage analytics model unavailable.",
        }

    since = timezone.now() - timedelta(days=window_days)
    qs = ContractUsageEvent.objects.filter(created_at__gte=since)
    if tenant_key:
        qs = qs.filter(tenant_key=tenant_key)

    status_breakdown = {
        "success_2xx": qs.filter(status_code__gte=200, status_code__lt=300).count(),
        "client_error_4xx": qs.filter(status_code__gte=400, status_code__lt=500).count(),
        "server_error_5xx": qs.filter(status_code__gte=500, status_code__lt=600).count(),
    }

    top_clients = list(
        qs.values("client_key")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    endpoint_breakdown = list(
        qs.values("endpoint")
        .annotate(count=Count("id"), units=Sum("billable_units"))
        .order_by("-count")
    )

    billable_units_total = sum(event.billable_units for event in qs.only("billable_units"))
    billable_amount_total = sum((event.billable_amount for event in qs.only("billable_amount")), Decimal("0.0000"))

    return {
        "window_days": window_days,
        "tenant_key": tenant_key or "all",
        "since": since.isoformat(),
        "total_events": qs.count(),
        "status_breakdown": status_breakdown,
        "billable_units_total": billable_units_total,
        "billable_amount_total": str(billable_amount_total),
        "top_clients": top_clients,
        "endpoint_breakdown": endpoint_breakdown,
    }


def _contract_billing_summary_payload(window_days=30, tenant_key="", client_key=""):
    try:
        from .models import ClientContractProfile, ContractUsageEvent
    except Exception:
        return {
            "window_days": window_days,
            "tenant_key": tenant_key or "all",
            "client_key": client_key or "all",
            "summary": [],
            "notes": "Billing models unavailable.",
        }

    since = timezone.now() - timedelta(days=window_days)
    events = ContractUsageEvent.objects.filter(created_at__gte=since)
    profiles = ClientContractProfile.objects.filter(is_active=True)
    if tenant_key:
        events = events.filter(tenant_key=tenant_key)
        profiles = profiles.filter(tenant_key=tenant_key)
    if client_key:
        events = events.filter(client_key=client_key)
        profiles = profiles.filter(client_key=client_key)

    profile_map = {
        (profile.tenant_key, profile.client_key): profile
        for profile in profiles
    }
    grouped = {}
    for event in events:
        key = (event.tenant_key, event.client_key)
        bucket = grouped.setdefault(
            key,
            {
                "tenant_key": event.tenant_key,
                "client_key": event.client_key,
                "event_count": 0,
                "billable_units": 0,
                "estimated_amount": Decimal("0.0000"),
            },
        )
        bucket["event_count"] += 1
        bucket["billable_units"] += event.billable_units
        bucket["estimated_amount"] += event.billable_amount

    summary = []
    billing_plan_base_fees = {
        "standard": Decimal("99.00"),
        "pro": Decimal("249.00"),
        "enterprise": Decimal("799.00"),
    }
    period_end = timezone.now()
    for key, bucket in grouped.items():
        profile = profile_map.get(key)
        allowance = int(profile.monthly_event_allowance) if profile else 1000
        rate = profile.overage_rate if profile else Decimal("0.0100")
        contact_email = profile.billing_contact_email if profile else ""
        overage_units = max(bucket["billable_units"] - allowance, 0)
        overage_amount = Decimal(overage_units) * rate
        usage_pct = round((bucket["billable_units"] / allowance) * 100, 1) if allowance else 0.0
        if usage_pct >= 120:
            enforcement_state = "exceeded"
            threshold_key = "red"
            enforcement_action = "Throttle non-critical contract traffic or move tenant to a higher plan immediately."
            enforcement_mode = "hard"
        elif usage_pct >= 90:
            enforcement_state = "warning"
            threshold_key = "yellow"
            enforcement_action = "Notify the client and prepare overage or plan-upgrade workflow."
            enforcement_mode = "soft"
        else:
            enforcement_state = "healthy"
            threshold_key = "green"
            enforcement_action = "No enforcement action required."
            enforcement_mode = "none"

        hard_action_url = ""
        hard_action_label = ""
        if enforcement_mode == "hard":
            hard_action_label = "Enforce Strict Contract Mode"
            hard_action_url = (
                f"/admin/insights-contract-enforcement/?tenant={bucket['tenant_key']}"
                f"&client={bucket['client_key']}&action=enforce_strict_mode"
            )
        elif enforcement_mode == "soft":
            hard_action_label = "Prepare Plan Upgrade"
            hard_action_url = (
                f"/admin/insights-contract-enforcement/?tenant={bucket['tenant_key']}"
                f"&client={bucket['client_key']}&action=prepare_upgrade"
            )

        access_token = _billing_access_token(
            bucket["tenant_key"],
            bucket["client_key"],
            window_days=window_days,
            label="Customer billing portal",
            recipient_email=contact_email,
        )
        access_link, _ = _billing_access_link_from_token(
            access_token,
            tenant_key=bucket["tenant_key"],
            client_key=bucket["client_key"],
            window_days=window_days,
            max_age=BILLING_ACCESS_MAX_AGE_SECONDS,
        )
        access_link_payload = _billing_access_link_payload(access_link, token=access_token) if access_link else {}
        invoice_number = _invoice_number_for(bucket["tenant_key"], bucket["client_key"], period_end)
        billing_plan = profile.billing_plan if profile else "standard"
        plan_fee = billing_plan_base_fees.get((billing_plan or "standard").lower(), Decimal("99.00"))
        usage_amount = bucket["estimated_amount"]
        subtotal = plan_fee + usage_amount + overage_amount
        tax_amount = (subtotal * Decimal("0.08")).quantize(Decimal("0.01"))
        total_due = (subtotal + tax_amount).quantize(Decimal("0.01"))
        invoice_line_items = [
            {
                "description": f"{billing_plan.title()} plan base fee",
                "quantity": 1,
                "unit_price": str(plan_fee),
                "amount": str(plan_fee),
                "category": "subscription",
            },
            {
                "description": "Contract API usage",
                "quantity": int(bucket["billable_units"]),
                "unit_price": str(rate),
                "amount": str(usage_amount),
                "category": "usage",
            },
            {
                "description": "Overage adjustment",
                "quantity": int(overage_units),
                "unit_price": str(rate),
                "amount": str(overage_amount),
                "category": "overage",
            },
            {
                "description": "Sales tax (8%)",
                "quantity": 1,
                "unit_price": str(tax_amount),
                "amount": str(tax_amount),
                "category": "tax",
            },
        ]
        invoice_signature = _invoice_signature_for(
            {
                "invoice_number": invoice_number,
                "tenant_key": bucket["tenant_key"],
                "client_key": bucket["client_key"],
                "window_days": window_days,
                "billable_units": bucket["billable_units"],
                "estimated_amount": str(bucket["estimated_amount"]),
                "total_due": str(total_due),
            }
        )
        invoice_export_base = access_link_payload.get("invoice_pdf_url", "")
        if invoice_export_base:
            invoice_export_base = invoice_export_base.rsplit("&format=pdf", 1)[0]
        else:
            invoice_export_base = (
                f"/contracts/billing/invoice/?tenant={bucket['tenant_key']}"
                f"&client={bucket['client_key']}&window_days={window_days}&access_token={access_token}"
            )
        customer_billing_url = access_link_payload.get("customer_billing_url") or (
            f"/contracts/billing/?tenant={bucket['tenant_key']}&client={bucket['client_key']}"
            f"&window_days={window_days}&access_token={access_token}"
        )
        summary.append(
            {
                "tenant_key": bucket["tenant_key"],
                "client_key": bucket["client_key"],
                "billing_plan": billing_plan,
                "event_count": bucket["event_count"],
                "billable_units": bucket["billable_units"],
                "monthly_event_allowance": allowance,
                "usage_pct": usage_pct,
                "threshold_key": threshold_key,
                "enforcement_state": enforcement_state,
                "enforcement_mode": enforcement_mode,
                "enforcement_action": enforcement_action,
                "hard_action_label": hard_action_label,
                "hard_action_url": hard_action_url,
                "billing_contact_email": contact_email,
                "overage_units": overage_units,
                "overage_rate": str(rate),
                "estimated_amount": str(bucket["estimated_amount"]),
                "overage_amount": str(overage_amount),
                "subtotal_amount": str(subtotal.quantize(Decimal("0.01"))),
                "tax_amount": str(tax_amount),
                "total_due": str(total_due),
                "invoice_line_items": invoice_line_items,
                "invoice_number": invoice_number,
                "invoice_signature": invoice_signature,
                "customer_billing_url": customer_billing_url,
                "customer_invoice_center_url": access_link_payload.get("invoice_center_url", ""),
                "invoice_export_csv": invoice_export_base + "&format=csv",
                "invoice_export_json": invoice_export_base + "&format=json",
                "invoice_export_txt": invoice_export_base + "&format=txt",
                "invoice_export_pdf": invoice_export_base + "&format=pdf",
                "access_link": access_link_payload,
                "access_link_issue_url": (
                    f"/admin/insights-contract-billing-access-links/?action=issue&tenant={bucket['tenant_key']}"
                    f"&client={bucket['client_key']}&window_days={window_days}"
                ),
            }
        )

    summary.sort(key=lambda row: (row["tenant_key"], -row["billable_units"], row["client_key"]))
    return {
        "window_days": window_days,
        "tenant_key": tenant_key or "all",
        "client_key": client_key or "all",
        "since": since.isoformat(),
        "period_end": period_end.isoformat(),
        "invoice_brand": {
            "company_name": "GrassRoots Systems",
            "tagline": "BaseTrue Contract Billing",
            "support_email": "billing@grassroots.local",
        },
        "summary": summary,
    }


def _persist_billing_snapshot(payload):
    try:
        from .models import ContractBillingSnapshot

        period_end = timezone.now()
        window_days = int(payload.get("window_days") or 30)
        period_start = period_end - timedelta(days=window_days)
        return ContractBillingSnapshot.objects.create(
            tenant_key=payload.get("tenant_key") or "all",
            client_key=payload.get("client_key") or "all",
            window_days=window_days,
            period_start=period_start,
            period_end=period_end,
            summary_payload=payload,
        )
    except Exception:
        return None


def _billing_snapshot_history_payload(tenant_key="", client_key="", limit=12):
    try:
        from .models import ContractBillingSnapshot
    except Exception:
        return []

    qs = ContractBillingSnapshot.objects.all()
    if tenant_key:
        qs = qs.filter(tenant_key=tenant_key)
    if client_key:
        qs = qs.filter(client_key=client_key)
    rows = []
    for snapshot in qs.order_by("-created_at")[:limit]:
        rows.append(
            {
                "created_at": snapshot.created_at.isoformat(),
                "tenant_key": snapshot.tenant_key,
                "client_key": snapshot.client_key,
                "window_days": snapshot.window_days,
                "period_start": snapshot.period_start.isoformat(),
                "period_end": snapshot.period_end.isoformat(),
                "summary": snapshot.summary_payload.get("summary", []),
            }
        )
    return rows


def _enqueue_billing_job(job_type, tenant_key="default", client_key="all", payload=None, requested_by=None):
    try:
        from .models import ContractBillingJob
    except Exception:
        return None
    return ContractBillingJob.objects.create(
        tenant_key=tenant_key or "default",
        client_key=client_key or "all",
        job_type=job_type,
        payload=payload or {},
        requested_by=requested_by,
    )


def _queue_billing_notification(tenant_key, client_key, recipient, subject, body, related_job=None, channel="email"):
    try:
        from .models import ContractBillingNotification
    except Exception:
        return None
    return ContractBillingNotification.objects.create(
        tenant_key=tenant_key or "default",
        client_key=client_key or "all",
        channel=channel or "email",
        recipient=recipient or "",
        subject=subject,
        body=body,
        related_job=related_job,
    )


def _serialize_billing_notification(notification, include_actions=False):
    payload = {
        "id": notification.id,
        "created_at": notification.created_at.isoformat(),
        "channel": notification.channel,
        "tenant_key": notification.tenant_key,
        "client_key": notification.client_key,
        "recipient": notification.recipient,
        "subject": notification.subject,
        "status": notification.status,
        "retry_count": int(notification.retry_count or 0),
        "last_error": notification.last_error,
        "last_attempt_at": notification.last_attempt_at.isoformat() if notification.last_attempt_at else "",
        "next_retry_at": notification.next_retry_at.isoformat() if notification.next_retry_at else "",
        "sent_at": notification.sent_at.isoformat() if notification.sent_at else "",
        "can_retry": notification.status in {"failed", "skipped"},
    }
    if include_actions:
        payload["retry_url"] = (
            f"/admin/insights-contract-billing-notifications/?action=retry"
            f"&notification_id={notification.id}"
        )
    return payload


def _deliver_billing_notification(notification):
    notification.last_attempt_at = timezone.now()
    notification.next_retry_at = None
    update_fields = ["last_attempt_at", "next_retry_at"]

    if not notification.recipient:
        notification.status = "skipped"
        notification.last_error = "Missing recipient email"
        update_fields.extend(["status", "last_error"])
        notification.save(update_fields=update_fields)
        return notification

    try:
        delivered = send_mail(
            notification.subject,
            notification.body,
            None,
            [notification.recipient],
            fail_silently=False,
        )
        if delivered:
            notification.status = "sent"
            notification.sent_at = timezone.now()
            notification.last_error = ""
            update_fields.extend(["status", "sent_at", "last_error"])
        else:
            notification.status = "failed"
            notification.last_error = "Email backend reported zero deliveries"
            notification.next_retry_at = timezone.now() + timedelta(minutes=BILLING_NOTIFICATION_RETRY_DELAY_MINUTES)
            update_fields.extend(["status", "last_error", "next_retry_at"])
    except Exception as exc:
        notification.status = "failed"
        notification.last_error = str(exc)
        notification.next_retry_at = timezone.now() + timedelta(minutes=BILLING_NOTIFICATION_RETRY_DELAY_MINUTES)
        update_fields.extend(["status", "last_error", "next_retry_at"])

    notification.save(update_fields=update_fields)
    return notification


def _retry_billing_notification(notification_id, recipient_override=""):
    try:
        from .models import ContractBillingNotification
    except Exception:
        return {"ok": False, "error": "Notification model unavailable"}

    notification = ContractBillingNotification.objects.filter(id=notification_id).first()
    if not notification:
        return {"ok": False, "error": "Notification not found"}

    if recipient_override:
        notification.recipient = recipient_override.strip()
    notification.retry_count = int(notification.retry_count or 0) + 1
    notification.status = ContractBillingNotification.STATUS_QUEUED
    notification.last_error = ""
    notification.save(update_fields=["recipient", "retry_count", "status", "last_error"])
    notification = _deliver_billing_notification(notification)
    return {"ok": True, "notification": _serialize_billing_notification(notification, include_actions=True)}


def _auto_rotate_expiring_high_risk_links(tenant_key="", client_key="", max_rotations=20, created_by=None):
    try:
        from .models import ContractBillingAccessLink
    except Exception:
        return {"rotated": 0, "candidates": 0, "rows": []}

    now = timezone.now()
    cutoff = now + timedelta(days=1)
    qs = ContractBillingAccessLink.objects.filter(
        is_active=True,
        revoked_at__isnull=True,
        expires_at__isnull=False,
        expires_at__lte=cutoff,
    )
    if tenant_key:
        qs = qs.filter(tenant_key=tenant_key)
    if client_key:
        qs = qs.filter(client_key=client_key)

    candidates = []
    for link in qs.order_by("expires_at", "-use_count")[: max(10, max_rotations * 3)]:
        stale_never_used = int(link.use_count or 0) == 0 and (now - link.created_at).days >= 14
        high_use_near_expiry = int(link.use_count or 0) >= 25
        if stale_never_used or high_use_near_expiry:
            candidates.append(link)

    rotated_rows = []
    rotated = 0
    for link in candidates[:max_rotations]:
        replacement = _issue_billing_access_link(
            tenant_key=link.tenant_key,
            client_key=link.client_key,
            window_days=link.window_days,
            created_by=created_by,
            label=link.label or "Customer billing portal",
            recipient_email=link.recipient_email or "",
            ttl_days=BILLING_ACCESS_DEFAULT_TTL_DAYS,
            reuse_existing=False,
        )
        if replacement:
            link.is_active = False
            link.revoked_at = now
            link.save(update_fields=["is_active", "revoked_at", "updated_at"])
            rotated += 1
            rotated_rows.append(
                {
                    "tenant_key": link.tenant_key,
                    "client_key": link.client_key,
                    "old_link_id": link.id,
                    "new_link_id": replacement.id,
                }
            )

    return {
        "rotated": rotated,
        "candidates": len(candidates),
        "rows": rotated_rows,
    }


def _auto_retry_bounce_categories_with_safe_heuristics(tenant_key="", client_key="", max_retries=25):
    try:
        from .models import ContractBillingNotification
    except Exception:
        return {
            "retried": 0,
            "skipped_policy": 0,
            "skipped_cooldown": 0,
            "categories": [],
        }

    now = timezone.now()
    safe_categories = {"transient", "mailbox_full", "domain_mx"}
    category_counts = Counter()

    qs = ContractBillingNotification.objects.filter(
        channel="invoice_email",
        status__in=["failed", "skipped"],
        retry_count__lt=3,
    ).exclude(recipient="")
    if tenant_key:
        qs = qs.filter(tenant_key=tenant_key)
    if client_key:
        qs = qs.filter(client_key=client_key)

    retried = 0
    skipped_policy = 0
    skipped_cooldown = 0
    for notification in qs.order_by("created_at"):
        category = _invoice_email_category(notification.last_error)
        if category not in safe_categories:
            skipped_policy += 1
            continue
        if notification.last_attempt_at and (now - notification.last_attempt_at) < timedelta(minutes=30):
            skipped_cooldown += 1
            continue

        result = _retry_billing_notification(notification.id)
        if result.get("ok"):
            retried += 1
            category_counts[category] += 1
        if retried >= max_retries:
            break

    return {
        "retried": retried,
        "skipped_policy": skipped_policy,
        "skipped_cooldown": skipped_cooldown,
        "categories": [{"key": key, "count": int(value)} for key, value in category_counts.most_common()],
    }


def _send_billing_health_notifications(tenant_key="", client_key="", notify_if_score_le=70):
    try:
        from .models import ContractBillingNotification
    except Exception:
        return {"sent": 0, "health_score": 0, "reason": "notification_model_unavailable"}

    summary_payload = _contract_billing_summary_payload(
        window_days=30,
        tenant_key=tenant_key,
        client_key=client_key,
    )
    billing_rows = summary_payload.get("summary", [])

    scoped_links = _billing_access_links_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=30,
        limit=300,
        status_filter="all",
        expires_filter="all",
        sort_by="newest",
    )
    access_link_analytics = _billing_access_link_analytics_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=30,
        status_filter="all",
        expires_filter="all",
    )
    anomalies = _billing_access_link_anomalies_payload(scoped_links)
    invoice_notifications = _customer_billing_notifications_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        limit=200,
        channel="invoice_email",
    )
    email_diagnostics = _billing_invoice_email_diagnostics_payload(invoice_notifications)
    access_link_risk = _billing_access_link_risk_payload(scoped_links, anomalies, access_link_analytics)
    health_score = _billing_health_score_payload(
        billing_rows,
        access_link_analytics,
        anomalies,
        email_diagnostics,
        access_link_risk,
    )
    score = int(health_score.get("score") or 0)
    if score > int(notify_if_score_le):
        return {"sent": 0, "health_score": score, "reason": "above_threshold"}

    now = timezone.now()
    recent_exists = ContractBillingNotification.objects.filter(
        channel="billing_health",
        tenant_key=tenant_key or "default",
        client_key=client_key or "all",
        created_at__gte=now - timedelta(hours=24),
    ).exists()
    if recent_exists:
        return {"sent": 0, "health_score": score, "reason": "cooldown"}

    recipients = []
    seen = set()
    for row in billing_rows:
        recipient = (row.get("billing_contact_email") or "").strip()
        if recipient and recipient not in seen:
            seen.add(recipient)
            recipients.append(recipient)

    if not recipients:
        profile = _client_billing_profile(tenant_key=tenant_key or "default", client_key=client_key or "")
        fallback_recipient = (profile.get("billing_contact_email") or "").strip()
        if fallback_recipient:
            recipients.append(fallback_recipient)
        else:
            return {"sent": 0, "health_score": score, "reason": "no_recipient"}

    sent = 0
    subject = f"Billing Health Alert · score {score} ({health_score.get('label')})"
    body = (
        f"Current billing health score: {score}\n"
        f"Label: {health_score.get('label')}\n"
        f"Anomalies: {anomalies.get('total', 0)}\n"
        f"Invoice failures: {email_diagnostics.get('failed', 0)}\n"
        f"Bounce-like diagnostics: {email_diagnostics.get('bounce_like', 0)}\n"
        f"Review: /admin/basetrue-insights/?billing_tenant={tenant_key}&billing_client={client_key}#bt-ins-billing\n"
    )
    for recipient in recipients[:5]:
        notification = _queue_billing_notification(
            tenant_key=tenant_key or "default",
            client_key=client_key or "all",
            recipient=recipient,
            subject=subject,
            body=body,
            related_job=None,
            channel="billing_health",
        )
        if not notification:
            continue
        delivered = _deliver_billing_notification(notification)
        if delivered.status in {"sent", "queued", "skipped", "failed"}:
            sent += 1

    return {"sent": sent, "health_score": score, "reason": "sent" if sent else "queued_none"}


def _run_billing_operational_automation(tenant_key="", client_key="", created_by=None):
    rotate_result = _auto_rotate_expiring_high_risk_links(
        tenant_key=tenant_key,
        client_key=client_key,
        created_by=created_by,
    )
    retry_result = _auto_retry_bounce_categories_with_safe_heuristics(
        tenant_key=tenant_key,
        client_key=client_key,
    )
    health_result = _send_billing_health_notifications(
        tenant_key=tenant_key,
        client_key=client_key,
        notify_if_score_le=90,
    )
    return {
        "rotations": rotate_result,
        "retries": retry_result,
        "health_notifications": health_result,
    }


def _process_billing_job(job):
    job.status = "running"
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    payload = job.payload or {}
    tenant_key = payload.get("tenant") or job.tenant_key
    client_key = payload.get("client") or job.client_key
    window_days = int(payload.get("window_days") or 30)

    if job.job_type in {"billing_cycle", "invoice_export"}:
        summary = _contract_billing_summary_payload(window_days=window_days, tenant_key=tenant_key, client_key=client_key)
        _persist_billing_snapshot(summary)
        rows = summary.get("summary", [])
        if rows:
            row = rows[0]
            if row.get("billing_contact_email"):
                _queue_billing_notification(
                    tenant_key=tenant_key,
                    client_key=client_key,
                    recipient=row.get("billing_contact_email"),
                    subject=f"Invoice {row.get('invoice_number')}",
                    body=f"Estimated amount {row.get('estimated_amount')} with overage {row.get('overage_amount')}",
                    related_job=job,
                )
        job.result_payload = summary
        job.status = "completed"
    elif job.job_type == "automation":
        result = _run_billing_operational_automation(
            tenant_key=tenant_key,
            client_key=client_key,
            created_by=job.requested_by,
        )
        job.result_payload = result
        job.status = "completed"
    elif job.job_type == "notify":
        notifications = []
        try:
            from .models import ContractBillingNotification
            queued = ContractBillingNotification.objects.filter(related_job=job, status="queued")
            for notification in queued:
                _deliver_billing_notification(notification)
                if notification.recipient:
                    notifications.append(notification.recipient)
            job.result_payload = {"notifications": notifications}
            job.status = "completed"
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
    else:
        job.status = "failed"
        job.error_message = "Unsupported job type"

    job.completed_at = timezone.now()
    job.save(update_fields=["status", "result_payload", "error_message", "completed_at"])
    return job


def _process_pending_billing_jobs(limit=10):
    try:
        from .models import ContractBillingJob
    except Exception:
        return []
    jobs = list(ContractBillingJob.objects.filter(status="pending").order_by("created_at")[:limit])
    processed = []
    for job in jobs:
        processed.append(_process_billing_job(job))
    return processed


def _customer_membership_payload(user, tenant_key="", client_key=""):
    try:
        from .models import CustomerTenantMembership
    except Exception:
        return []

    if not getattr(user, "is_authenticated", False):
        return []

    qs = CustomerTenantMembership.objects.filter(user=user, is_active=True)
    if tenant_key:
        qs = qs.filter(tenant_key=tenant_key)
    if client_key:
        qs = qs.filter(client_key=client_key)
    return [
        {
            "tenant_key": row.tenant_key,
            "client_key": row.client_key,
            "role": row.role,
        }
        for row in qs.order_by("tenant_key", "client_key")
    ]


def _customer_billing_notifications_payload(tenant_key="", client_key="", limit=12, channel=""):
    try:
        from .models import ContractBillingNotification
    except Exception:
        return []

    qs = ContractBillingNotification.objects.all()
    if tenant_key:
        qs = qs.filter(tenant_key=tenant_key)
    if client_key:
        qs = qs.filter(client_key=client_key)
    if channel:
        qs = qs.filter(channel=channel)
    return [
        _serialize_billing_notification(row, include_actions=True)
        for row in qs.order_by("-created_at")[:limit]
    ]


def _billing_access_link_drilldowns_payload(links):
    status_counts = Counter((row.get("status") or "legacy") for row in links)
    tenant_counts = Counter((row.get("tenant_key") or "unknown") for row in links)
    client_counts = Counter((row.get("client_key") or "unknown") for row in links)

    status_rows = []
    for status in ["active", "revoked", "expired", "legacy"]:
        count = int(status_counts.get(status, 0))
        status_rows.append(
            {
                "label": status.title(),
                "count": count,
                "status": status,
                "url": f"?billing_link_status={status}#bt-ins-billing",
            }
        )

    top_tenants = []
    for tenant, count in tenant_counts.most_common(6):
        top_tenants.append(
            {
                "label": tenant,
                "count": int(count),
                "url": f"?billing_link_tenant={tenant}&billing_link_status=all#bt-ins-billing",
            }
        )

    top_clients = []
    for client, count in client_counts.most_common(6):
        top_clients.append(
            {
                "label": client,
                "count": int(count),
                "url": f"?billing_link_client={client}&billing_link_status=all#bt-ins-billing",
            }
        )

    return {
        "status_rows": status_rows,
        "top_tenants": top_tenants,
        "top_clients": top_clients,
    }


def _billing_access_link_lifecycle_timeline_payload(links, limit=40):
    timeline = []
    for row in links:
        label = row.get("label") or "Customer billing portal"
        ref = f"{row.get('tenant_key')}/{row.get('client_key')}"
        if row.get("created_at"):
            timeline.append(
                {
                    "timestamp": row.get("created_at"),
                    "event": "Created",
                    "detail": f"{label} for {ref}",
                    "tone": "blue",
                }
            )
        if row.get("last_used_at"):
            timeline.append(
                {
                    "timestamp": row.get("last_used_at"),
                    "event": "Used",
                    "detail": f"{ref} · uses {row.get('use_count')}",
                    "tone": "green",
                }
            )
        if row.get("revoked_at"):
            timeline.append(
                {
                    "timestamp": row.get("revoked_at"),
                    "event": "Revoked",
                    "detail": ref,
                    "tone": "red",
                }
            )
        elif row.get("expires_at") and (row.get("status") == "expired"):
            timeline.append(
                {
                    "timestamp": row.get("expires_at"),
                    "event": "Expired",
                    "detail": ref,
                    "tone": "yellow",
                }
            )

    timeline.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return timeline[:limit]


def _bulk_issue_presets_payload(summary_rows, limit=8):
    presets = []
    seen = set()
    for row in summary_rows:
        tenant_key = row.get("tenant_key") or "default"
        client_key = row.get("client_key") or "all"
        key = (tenant_key, client_key)
        if key in seen:
            continue
        seen.add(key)
        presets.append(
            {
                "tenant_key": tenant_key,
                "client_key": client_key,
                "label": f"{tenant_key} / {client_key}",
                "window_days": 30,
                "ttl_days": BILLING_ACCESS_DEFAULT_TTL_DAYS,
            }
        )
        if len(presets) >= limit:
            break
    return presets


def _billing_micro_trends_payload(tenant_key="", client_key="", days=7):
    window_days = max(3, min(30, int(days or 7)))
    today = timezone.now().date()
    date_list = [today - timedelta(days=offset) for offset in range(window_days - 1, -1, -1)]

    link_activity_rows = []
    invoice_email_rows = []
    peak_link_activity = 1

    try:
        from .models import ContractBillingAccessLink, ContractBillingNotification
    except Exception:
        return {
            "link_activity_rows": [],
            "invoice_email_rows": [],
            "window_days": window_days,
        }

    links_qs = ContractBillingAccessLink.objects.all()
    if tenant_key:
        links_qs = links_qs.filter(tenant_key=tenant_key)
    if client_key:
        links_qs = links_qs.filter(client_key=client_key)

    invoice_qs = ContractBillingNotification.objects.filter(channel="invoice_email")
    if tenant_key:
        invoice_qs = invoice_qs.filter(tenant_key=tenant_key)
    if client_key:
        invoice_qs = invoice_qs.filter(client_key=client_key)

    for day in date_list:
        created_count = links_qs.filter(created_at__date=day).count()
        used_count = links_qs.filter(last_used_at__date=day).count()
        link_activity = int(created_count + used_count)
        peak_link_activity = max(peak_link_activity, link_activity)
        link_activity_rows.append(
            {
                "day": day.strftime("%a"),
                "date": day.isoformat(),
                "count": link_activity,
                "created": int(created_count),
                "used": int(used_count),
                "pct": 0,
            }
        )

        email_total = invoice_qs.filter(created_at__date=day).count()
        email_sent = invoice_qs.filter(created_at__date=day, status="sent").count()
        success_rate = int(round((email_sent / email_total) * 100)) if email_total else 0
        invoice_email_rows.append(
            {
                "day": day.strftime("%a"),
                "date": day.isoformat(),
                "total": int(email_total),
                "sent": int(email_sent),
                "success_rate": success_rate,
                "pct": max(success_rate, 4) if email_total else 0,
            }
        )

    for row in link_activity_rows:
        row["pct"] = int((row["count"] / peak_link_activity) * 100) if peak_link_activity else 0

    total_link_activity = sum(int(row.get("count") or 0) for row in link_activity_rows)
    email_rows_with_volume = [row for row in invoice_email_rows if int(row.get("total") or 0) > 0]
    if email_rows_with_volume:
        avg_invoice_success_rate = round(
            sum(int(row.get("success_rate") or 0) for row in email_rows_with_volume) / len(email_rows_with_volume),
            1,
        )
    else:
        avg_invoice_success_rate = 0.0

    return {
        "link_activity_rows": link_activity_rows,
        "invoice_email_rows": invoice_email_rows,
        "window_days": window_days,
        "total_link_activity": total_link_activity,
        "avg_invoice_success_rate": avg_invoice_success_rate,
    }


def _billing_access_link_anomalies_payload(links, max_rows=12):
    now = timezone.now()
    anomaly_rows = []
    anomaly_counts = Counter()
    severity_rank = {"red": 3, "yellow": 2, "blue": 1}

    def _parse_iso(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None

    for row in links:
        status = (row.get("status") or "").lower()
        use_count = int(row.get("use_count") or 0)
        expires_in_days = row.get("expires_in_days")
        created_at = _parse_iso(row.get("created_at"))
        revoked_at = _parse_iso(row.get("revoked_at"))
        last_used_at = _parse_iso(row.get("last_used_at"))
        scope = f"{row.get('tenant_key')}/{row.get('client_key')}"

        if status == "active" and use_count == 0 and isinstance(expires_in_days, int) and expires_in_days <= 1:
            anomaly_counts["expiring_unused"] += 1
            anomaly_rows.append(
                {
                    "type": "expiring_unused",
                    "label": "Unused link near expiry",
                    "detail": f"{scope} expires in {expires_in_days}d with no usage",
                    "severity": "yellow",
                    "risk_score": 58,
                    "explanation": "This link is close to expiry and has never been used, which often indicates stale customer distribution.",
                    "link_id": row.get("id"),
                    "tenant_key": row.get("tenant_key"),
                    "client_key": row.get("client_key"),
                    "suggested_action": "revoke",
                    "suggested_action_label": "Revoke Link",
                }
            )

        if status == "active" and use_count >= 25 and isinstance(expires_in_days, int) and expires_in_days <= 1:
            anomaly_counts["high_use_near_expiry"] += 1
            anomaly_rows.append(
                {
                    "type": "high_use_near_expiry",
                    "label": "High usage near expiry",
                    "detail": f"{scope} has {use_count} uses and expires in {expires_in_days}d",
                    "severity": "red",
                    "risk_score": 82,
                    "explanation": "High repeated usage close to expiration can cause access disruption and often requires rotation planning.",
                    "link_id": row.get("id"),
                    "tenant_key": row.get("tenant_key"),
                    "client_key": row.get("client_key"),
                    "suggested_action": "revoke",
                    "suggested_action_label": "Revoke Link",
                }
            )

        if status == "revoked" and revoked_at and last_used_at and last_used_at > revoked_at:
            anomaly_counts["used_after_revoke"] += 1
            anomaly_rows.append(
                {
                    "type": "used_after_revoke",
                    "label": "Usage after revoke timestamp",
                    "detail": f"{scope} shows use after revoke",
                    "severity": "red",
                    "risk_score": 91,
                    "explanation": "Post-revocation usage indicates token leakage or delayed revocation propagation and needs immediate rotation.",
                    "link_id": row.get("id"),
                    "tenant_key": row.get("tenant_key"),
                    "client_key": row.get("client_key"),
                    "suggested_action": "rotate",
                    "suggested_action_label": "Issue Replacement Link",
                }
            )

        if status == "active" and use_count == 0 and created_at and (now - created_at).days >= 14:
            anomaly_counts["stale_never_used"] += 1
            anomaly_rows.append(
                {
                    "type": "stale_never_used",
                    "label": "Stale active link",
                    "detail": f"{scope} has been active {(now - created_at).days}d with no usage",
                    "severity": "yellow",
                    "risk_score": 52,
                    "explanation": "Long-lived unused links expand exposure without business value and should be retired.",
                    "link_id": row.get("id"),
                    "tenant_key": row.get("tenant_key"),
                    "client_key": row.get("client_key"),
                    "suggested_action": "revoke",
                    "suggested_action_label": "Revoke Link",
                }
            )

    highest_severity = "blue"
    if anomaly_rows:
        highest_severity = max(anomaly_rows, key=lambda item: severity_rank.get(item.get("severity"), 0)).get("severity", "blue")

    return {
        "total": len(anomaly_rows),
        "counts": {
            "expiring_unused": int(anomaly_counts.get("expiring_unused", 0)),
            "high_use_near_expiry": int(anomaly_counts.get("high_use_near_expiry", 0)),
            "used_after_revoke": int(anomaly_counts.get("used_after_revoke", 0)),
            "stale_never_used": int(anomaly_counts.get("stale_never_used", 0)),
        },
        "highest_severity": highest_severity,
        "rows": anomaly_rows[:max_rows],
    }


def _invoice_email_category(error_text):
    category_rules = [
        ("recipient_invalid", ("invalid", "recipient", "address", "unknown user", "mailbox unavailable")),
        ("domain_mx", ("domain", "mx", "dns", "host not found")),
        ("policy_block", ("blocked", "policy", "blacklist", "spam", "rejected")),
        ("mailbox_full", ("full", "quota", "over quota", "mailbox full")),
        ("transient", ("timeout", "temporar", "deferred", "try again", "rate limit")),
    ]
    lowered = (error_text or "").lower()
    for category, tokens in category_rules:
        if any(token in lowered for token in tokens):
            return category
    if lowered:
        return "uncategorized"
    return "none"


def _invoice_email_retry_guidance(category):
    guidance_by_category = {
        "recipient_invalid": "Verify recipient address and update billing contact before retrying.",
        "domain_mx": "Validate recipient domain DNS/MX records and retry after correction.",
        "policy_block": "Review sending policy/authentication and request allowlisting if needed.",
        "mailbox_full": "Retry later or ask the recipient to free mailbox storage.",
        "transient": "Retry with backoff; this is usually temporary infrastructure pressure.",
        "uncategorized": "Inspect SMTP provider logs, then retry with corrected routing.",
        "none": "No retry guidance needed.",
    }
    return guidance_by_category.get(category or "uncategorized", guidance_by_category["uncategorized"])


def _billing_invoice_email_diagnostics_payload(invoice_notifications):

    total = len(invoice_notifications)
    sent = 0
    failed = 0
    skipped = 0
    bounce_like = 0
    categories = Counter()
    diagnostic_rows = []

    for row in invoice_notifications:
        status = (row.get("status") or "").lower()
        error_text = row.get("last_error") or ""
        category = _invoice_email_category(error_text)
        is_bounce = category != "none"
        if status == "sent":
            sent += 1
        elif status == "failed":
            failed += 1
        elif status == "skipped":
            skipped += 1
        if is_bounce:
            bounce_like += 1
            categories[category] += 1

        if status in {"failed", "skipped"} or is_bounce:
            diagnostic_rows.append(
                {
                    "id": row.get("id"),
                    "recipient": row.get("recipient") or "unassigned",
                    "status": status or "unknown",
                    "error": row.get("last_error") or "No error message",
                    "severity": "red" if status == "failed" or is_bounce else "yellow",
                    "category": category,
                    "retry_guidance": _invoice_email_retry_guidance(category),
                    "created_at": row.get("created_at") or "",
                }
            )

    success_rate = round((sent / total) * 100, 1) if total else 0.0
    category_rows = [
        {
            "key": key,
            "label": key.replace("_", " ").title(),
            "count": int(value),
            "guidance": _invoice_email_retry_guidance(key),
        }
        for key, value in categories.most_common()
    ]
    return {
        "total": total,
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
        "bounce_like": bounce_like,
        "success_rate": success_rate,
        "categories": category_rows,
        "rows": diagnostic_rows[:12],
    }


def _billing_access_link_risk_payload(links, anomalies, access_link_analytics):
    total_links = max(1, len(links))
    anomaly_count = int(anomalies.get("total") or 0)
    expiring_soon = int(access_link_analytics.get("expiring_soon") or 0)
    expired_links = int(access_link_analytics.get("expired_links") or 0)
    never_used = int(access_link_analytics.get("never_used_links") or 0)
    revoked_links = int(access_link_analytics.get("revoked_links") or 0)

    score = 0
    score += min(45, anomaly_count * 9)
    score += min(18, expiring_soon * 3)
    score += min(18, expired_links * 3)
    score += min(12, never_used * 2)
    score += min(7, max(0, revoked_links - (total_links // 4)))
    score = max(0, min(100, int(score)))

    if score >= 80:
        label = "High"
        threshold_key = "red"
        severity_label = "Critical"
    elif score >= 55:
        label = "Moderate"
        threshold_key = "yellow"
        severity_label = "Elevated"
    elif score >= 35:
        label = "Guarded"
        threshold_key = "yellow"
        severity_label = "Watch"
    else:
        label = "Low"
        threshold_key = "green"
        severity_label = "Stable"

    drivers = [
        {"label": "Anomaly load", "value": anomaly_count},
        {"label": "Expiring links", "value": expiring_soon},
        {"label": "Expired links", "value": expired_links},
        {"label": "Never used links", "value": never_used},
    ]
    return {
        "score": score,
        "label": label,
        "threshold_key": threshold_key,
        "severity_label": severity_label,
        "threshold_bands": [
            {"label": "Critical", "min": 80, "max": 100, "key": "red"},
            {"label": "Elevated", "min": 55, "max": 79, "key": "yellow"},
            {"label": "Watch", "min": 35, "max": 54, "key": "yellow"},
            {"label": "Stable", "min": 0, "max": 34, "key": "green"},
        ],
        "drivers": drivers,
    }


def _billing_health_score_change_payload(health_score, access_link_risk_trend, anomalies, email_diagnostics):
    current_score = int(health_score.get("score") or 0)
    trend_rows = access_link_risk_trend.get("rows") or []
    previous_risk = int(trend_rows[-2].get("score") or 0) if len(trend_rows) >= 2 else int(trend_rows[-1].get("score") or 0) if trend_rows else 0
    current_risk = int(trend_rows[-1].get("score") or 0) if trend_rows else previous_risk
    risk_delta = current_risk - previous_risk

    estimated_score_delta = int(round(-risk_delta * 0.25))
    estimated_previous_score = max(0, min(100, current_score - estimated_score_delta))
    delta = current_score - estimated_previous_score
    if delta > 0:
        direction = "up"
    elif delta < 0:
        direction = "down"
    else:
        direction = "flat"

    reasons = []
    if risk_delta > 0:
        reasons.append(f"Access-link risk rose by {risk_delta} points, reducing score stability.")
    elif risk_delta < 0:
        reasons.append(f"Access-link risk improved by {abs(risk_delta)} points, supporting score recovery.")

    anomaly_total = int(anomalies.get("total") or 0)
    if anomaly_total:
        reasons.append(f"{anomaly_total} anomaly signal(s) added downward pressure to billing health.")

    failed = int(email_diagnostics.get("failed") or 0)
    bounce_like = int(email_diagnostics.get("bounce_like") or 0)
    if failed or bounce_like:
        reasons.append(
            f"Deliverability impact: {failed} failed and {bounce_like} bounce-like email diagnostics."
        )

    if not reasons:
        reasons.append("No major changes detected; score remained stable.")

    return {
        "current_score": current_score,
        "estimated_previous_score": estimated_previous_score,
        "delta": delta,
        "direction": direction,
        "reasons": reasons,
    }


def _billing_access_link_risk_trend_payload(tenant_key="", client_key="", days=30):
    window_days = max(7, min(60, int(days or 30)))
    try:
        from .models import ContractBillingAccessLink
    except Exception:
        return {
            "window_days": window_days,
            "rows": [],
            "avg_score": 0.0,
        }

    qs = ContractBillingAccessLink.objects.all()
    if tenant_key:
        qs = qs.filter(tenant_key=tenant_key)
    if client_key:
        qs = qs.filter(client_key=client_key)

    today = timezone.now().date()
    rows = []
    peak_score = 1

    for offset in range(window_days - 1, -1, -1):
        day = today - timedelta(days=offset)
        next_day = day + timedelta(days=1)
        stale_cutoff = day - timedelta(days=14)

        expiring_soon = qs.filter(
            is_active=True,
            revoked_at__isnull=True,
            expires_at__date__gte=day,
            expires_at__date__lte=day + timedelta(days=3),
        ).count()
        stale_active = qs.filter(
            is_active=True,
            revoked_at__isnull=True,
            use_count=0,
            created_at__date__lte=stale_cutoff,
        ).count()
        used_after_revoke = qs.filter(
            revoked_at__isnull=False,
            revoked_at__date__lte=day,
            last_used_at__isnull=False,
            last_used_at__date__gte=next_day,
        ).count()
        revoked_today = qs.filter(revoked_at__date=day).count()

        score = 0
        score += min(45, expiring_soon * 6)
        score += min(30, stale_active * 3)
        score += min(20, used_after_revoke * 10)
        score += min(10, revoked_today * 2)
        score = max(0, min(100, int(score)))
        peak_score = max(peak_score, score)

        rows.append(
            {
                "day": day.strftime("%a"),
                "date": day.isoformat(),
                "score": score,
                "pct": 0,
            }
        )

    for row in rows:
        row["pct"] = int((row["score"] / peak_score) * 100) if peak_score else 0

    avg_score = round(sum(row.get("score", 0) for row in rows) / len(rows), 1) if rows else 0.0
    return {
        "window_days": window_days,
        "rows": rows,
        "avg_score": avg_score,
    }


def _billing_health_score_payload(
    billing_rows,
    access_link_analytics,
    anomalies,
    email_diagnostics,
    access_link_risk=None,
):
    score = 100
    enforcement_pressure = sum(1 for row in billing_rows if row.get("enforcement_state") in {"warning", "exceeded"})
    anomaly_total = int(anomalies.get("total") or 0)
    failed_emails = int(email_diagnostics.get("failed") or 0)
    bounce_like = int(email_diagnostics.get("bounce_like") or 0)
    expiring_soon = int(access_link_analytics.get("expiring_soon") or 0)
    risk_score = int((access_link_risk or {}).get("score") or 0)

    score -= min(30, enforcement_pressure * 7)
    score -= min(25, anomaly_total * 4)
    score -= min(20, failed_emails * 5)
    score -= min(15, bounce_like * 3)
    score -= min(10, expiring_soon * 2)
    score -= min(12, int(risk_score * 0.12))
    score = max(0, int(score))

    if score >= 85:
        label = "Healthy"
        threshold_key = "green"
    elif score >= 65:
        label = "Watch"
        threshold_key = "yellow"
    elif score >= 45:
        label = "Elevated"
        threshold_key = "red"
    else:
        label = "Critical"
        threshold_key = "red"

    components = [
        {"label": "Enforcement pressure", "value": enforcement_pressure},
        {"label": "Link anomalies", "value": anomaly_total},
        {"label": "Invoice email failures", "value": failed_emails},
        {"label": "Bounce-like diagnostics", "value": bounce_like},
        {"label": "Expiring links soon", "value": expiring_soon},
        {"label": "Access-link risk score", "value": risk_score},
    ]
    explainers = []
    if enforcement_pressure:
        explainers.append("Enforcement pressure is pulling the score down due to warning/exceeded clients.")
    if anomaly_total:
        explainers.append("Access-link anomalies are reducing health and may require revoke/rotate actions.")
    if failed_emails or bounce_like:
        explainers.append("Invoice email delivery issues are suppressing customer communication reliability.")
    if not explainers:
        explainers.append("No major billing risk signals detected in this window.")
    return {
        "score": score,
        "label": label,
        "threshold_key": threshold_key,
        "tuned_model": "v2",
        "components": components,
        "explainers": explainers,
    }


def _billing_health_explainer_payload(health_score, anomalies, email_diagnostics, access_link_risk):
    score = int(health_score.get("score") or 0)
    anomaly_total = int(anomalies.get("total") or 0)
    bounce_like = int(email_diagnostics.get("bounce_like") or 0)
    risk_score = int(access_link_risk.get("score") or 0)

    if score >= 85:
        summary = "Billing health is stable with low operational friction."
    elif score >= 65:
        summary = "Billing health is watch-level and trending toward intervention if unresolved."
    elif score >= 45:
        summary = "Billing health is elevated risk and should be actively managed."
    else:
        summary = "Billing health is critical and requires immediate stabilization steps."

    actions = []
    if anomaly_total:
        actions.append("Resolve access-link anomalies to reduce access disruption risk.")
    if bounce_like:
        actions.append("Review bounce categories and retry with corrected recipient routes.")
    if risk_score >= 55:
        actions.append("Rotate high-risk links and tighten expiry windows for active cohorts.")
    if not actions:
        actions.append("Continue monitoring trends and keep current delivery posture.")

    return {
        "summary": summary,
        "actions": actions,
        "risk_label": access_link_risk.get("label") or "Low",
    }


def _billing_anomaly_resolution_history_payload(tenant_key="", client_key="", limit=18):
    try:
        from .models import ContractBillingAccessLink, ContractBillingNotification
    except Exception:
        return []

    events = []
    revoked_qs = ContractBillingAccessLink.objects.filter(revoked_at__isnull=False)
    if tenant_key:
        revoked_qs = revoked_qs.filter(tenant_key=tenant_key)
    if client_key:
        revoked_qs = revoked_qs.filter(client_key=client_key)
    for link in revoked_qs.order_by("-revoked_at")[:limit]:
        events.append(
            {
                "timestamp": link.revoked_at.isoformat() if link.revoked_at else "",
                "action": "Link Revoked",
                "detail": f"{link.tenant_key}/{link.client_key} · {link.label or 'Customer billing portal'}",
                "outcome": "Risk reduced",
                "tone": "yellow",
            }
        )

    link_qs = ContractBillingAccessLink.objects.all()
    if tenant_key:
        link_qs = link_qs.filter(tenant_key=tenant_key)
    if client_key:
        link_qs = link_qs.filter(client_key=client_key)
    for link in link_qs.order_by("-created_at")[: max(limit * 2, 20)]:
        prior_exists = ContractBillingAccessLink.objects.filter(
            tenant_key=link.tenant_key,
            client_key=link.client_key,
            label=link.label,
            created_at__lt=link.created_at,
        ).exists()
        if prior_exists:
            events.append(
                {
                    "timestamp": link.created_at.isoformat() if link.created_at else "",
                    "action": "Link Rotated",
                    "detail": f"{link.tenant_key}/{link.client_key} · replacement issued",
                    "outcome": "Continuity preserved",
                    "tone": "green",
                }
            )

    notification_qs = ContractBillingNotification.objects.filter(channel="invoice_email", retry_count__gt=0)
    if tenant_key:
        notification_qs = notification_qs.filter(tenant_key=tenant_key)
    if client_key:
        notification_qs = notification_qs.filter(client_key=client_key)
    for notification in notification_qs.order_by("-last_attempt_at", "-created_at")[:limit]:
        events.append(
            {
                "timestamp": (
                    (notification.last_attempt_at or notification.created_at).isoformat()
                    if (notification.last_attempt_at or notification.created_at)
                    else ""
                ),
                "action": "Invoice Retry",
                "detail": f"{notification.tenant_key}/{notification.client_key} · {notification.recipient or 'unassigned'}",
                "outcome": notification.status.title(),
                "tone": "green" if notification.status == "sent" else "yellow",
            }
        )

    events.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return events[:limit]


def _billing_link_rotation_analytics_payload(tenant_key="", client_key="", days=30):
    try:
        from .models import ContractBillingAccessLink
    except Exception:
        return {
            "total_issued": 0,
            "estimated_rotations": 0,
            "rotation_rate": 0.0,
            "recent_rotations": [],
        }

    cutoff = timezone.now() - timedelta(days=max(1, int(days or 30)))
    links_qs = ContractBillingAccessLink.objects.all()
    if tenant_key:
        links_qs = links_qs.filter(tenant_key=tenant_key)
    if client_key:
        links_qs = links_qs.filter(client_key=client_key)

    total_issued = links_qs.count()
    recent_links = links_qs.filter(created_at__gte=cutoff).order_by("-created_at")
    estimated_rotations = 0
    rotation_rows = []

    for link in recent_links[:120]:
        had_prior = links_qs.filter(
            tenant_key=link.tenant_key,
            client_key=link.client_key,
            label=link.label,
            created_at__lt=link.created_at,
        ).exists()
        if had_prior:
            estimated_rotations += 1
            rotation_rows.append(
                {
                    "timestamp": link.created_at.isoformat() if link.created_at else "",
                    "scope": f"{link.tenant_key}/{link.client_key}",
                    "label": link.label or "Customer billing portal",
                }
            )

    rotation_rate = round((estimated_rotations / max(1, total_issued)) * 100, 1)
    return {
        "total_issued": int(total_issued),
        "estimated_rotations": int(estimated_rotations),
        "rotation_rate": rotation_rate,
        "recent_rotations": rotation_rows[:8],
    }


def _billing_anomaly_grouping_payload(anomalies):
    grouped = {}
    severity_rank = {"red": 3, "yellow": 2, "blue": 1, "green": 0}
    for row in anomalies.get("rows", []):
        tenant_key = row.get("tenant_key") or "unknown"
        client_key = row.get("client_key") or "unknown"
        scope = f"{tenant_key}/{client_key}"
        item = grouped.setdefault(
            scope,
            {
                "scope": scope,
                "tenant_key": tenant_key,
                "client_key": client_key,
                "count": 0,
                "highest_severity": "green",
                "highest_risk_score": 0,
            },
        )
        item["count"] += 1
        item["highest_risk_score"] = max(item["highest_risk_score"], int(row.get("risk_score") or 0))
        if severity_rank.get(row.get("severity"), 0) > severity_rank.get(item["highest_severity"], 0):
            item["highest_severity"] = row.get("severity") or "green"

    rows = sorted(
        grouped.values(),
        key=lambda item: (-int(item.get("highest_risk_score") or 0), -int(item.get("count") or 0), item.get("scope") or ""),
    )
    return rows[:12]


def _billing_deliverability_heatmap_payload(invoice_notifications, days=7):
    window_days = max(3, min(14, int(days or 7)))
    today = timezone.now().date()
    buckets = [
        {"label": "00-05", "start": 0, "end": 5},
        {"label": "06-11", "start": 6, "end": 11},
        {"label": "12-17", "start": 12, "end": 17},
        {"label": "18-23", "start": 18, "end": 23},
    ]

    def _parse_iso(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None

    day_rows = []
    for offset in range(window_days - 1, -1, -1):
        day = today - timedelta(days=offset)
        cells = []
        for bucket in buckets:
            total = 0
            sent = 0
            for row in invoice_notifications:
                stamp = _parse_iso(row.get("created_at") or row.get("last_attempt_at") or row.get("sent_at"))
                if not stamp:
                    continue
                local_stamp = timezone.localtime(stamp) if timezone.is_aware(stamp) else stamp
                if local_stamp.date() != day:
                    continue
                if not (bucket["start"] <= local_stamp.hour <= bucket["end"]):
                    continue
                total += 1
                if (row.get("status") or "").lower() == "sent":
                    sent += 1

            rate = round((sent / total) * 100, 1) if total else 0.0
            if total == 0:
                tone = "blue"
            elif rate >= 95:
                tone = "green"
            elif rate >= 75:
                tone = "yellow"
            else:
                tone = "red"
            cells.append(
                {
                    "label": bucket["label"],
                    "total": total,
                    "sent": sent,
                    "rate": rate,
                    "tone": tone,
                }
            )
        day_rows.append({"day": day.strftime("%a"), "date": day.isoformat(), "cells": cells})

    return {
        "window_days": window_days,
        "bucket_labels": [bucket["label"] for bucket in buckets],
        "rows": day_rows,
    }


def _customer_billing_forecast_payload(summary_payload, history_rows):
    summary_rows = summary_payload.get("summary", []) or []

    def _to_float(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    current_amount = sum(
        _to_float(row.get("estimated_amount")) + _to_float(row.get("overage_amount"))
        for row in summary_rows
    )
    current_units = sum(int(row.get("billable_units") or 0) for row in summary_rows)

    previous_amount = current_amount
    previous_units = current_units
    if history_rows:
        previous_summary = (history_rows[0].get("summary") or [])
        previous_amount = sum(
            _to_float(row.get("estimated_amount")) + _to_float(row.get("overage_amount"))
            for row in previous_summary
        )
        previous_units = sum(int(row.get("billable_units") or 0) for row in previous_summary)

    amount_delta = current_amount - previous_amount
    unit_delta = current_units - previous_units
    projected_amount = round(max(0.0, current_amount + (amount_delta * 0.6)), 2)
    projected_units = max(0, int(round(current_units + (unit_delta * 0.6))))

    if len(history_rows) >= 3:
        confidence = "high"
    elif len(history_rows) >= 1:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "current_amount": round(current_amount, 2),
        "projected_amount": projected_amount,
        "amount_delta": round(amount_delta, 2),
        "current_units": current_units,
        "projected_units": projected_units,
        "unit_delta": unit_delta,
        "confidence": confidence,
    }


def _customer_link_usage_insights_payload(links, access_link_analytics):
    total_links = int(access_link_analytics.get("total_links") or 0)
    used_links = int(access_link_analytics.get("used_links") or 0)
    never_used_links = int(access_link_analytics.get("never_used_links") or 0)
    high_usage_links = [row for row in links if int(row.get("use_count") or 0) >= 10]
    top_links = sorted(
        links,
        key=lambda row: (-int(row.get("use_count") or 0), row.get("label") or ""),
    )[:5]
    utilization_rate = round((used_links / max(1, total_links)) * 100, 1)

    return {
        "utilization_rate": utilization_rate,
        "total_links": total_links,
        "used_links": used_links,
        "never_used_links": never_used_links,
        "high_usage_count": len(high_usage_links),
        "top_links": top_links,
    }


def _customer_invoice_timeline_payload(summary_payload, history_rows, invoice_notifications, limit=30):
    timeline = []
    for row in summary_payload.get("summary", []):
        timeline.append(
            {
                "timestamp": timezone.now().isoformat(),
                "event": "Invoice Available",
                "detail": f"{row.get('invoice_number')} · total due {row.get('total_due')}",
                "tone": "green",
                "event_type": "invoice",
            }
        )

    for row in history_rows:
        timeline.append(
            {
                "timestamp": row.get("created_at") or "",
                "event": "Snapshot Captured",
                "detail": f"{row.get('tenant_key')}/{row.get('client_key')} · {row.get('window_days')}d window",
                "tone": "blue",
                "event_type": "snapshot",
            }
        )

    for row in invoice_notifications:
        status = (row.get("status") or "").lower()
        if status == "sent":
            event = "Invoice Email Sent"
            tone = "green"
        elif status == "failed":
            event = "Invoice Email Failed"
            tone = "red"
        elif status == "skipped":
            event = "Invoice Email Skipped"
            tone = "yellow"
        else:
            event = "Invoice Email Queued"
            tone = "blue"
        timeline.append(
            {
                "timestamp": row.get("sent_at") or row.get("last_attempt_at") or row.get("created_at") or "",
                "event": event,
                "detail": f"{row.get('recipient') or 'unassigned'} · {row.get('subject') or 'Invoice email'}",
                "tone": tone,
                "event_type": "email",
            }
        )

    timeline.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return timeline[:limit]


def _customer_invoice_event_feed_payload(summary_payload, history_rows, invoice_notifications, limit=36):
    timeline = _customer_invoice_timeline_payload(
        summary_payload,
        history_rows,
        invoice_notifications,
        limit=max(limit, 20),
    )
    feed = []
    for item in timeline:
        event_type = item.get("event_type") or "event"
        feed.append(
            {
                "timestamp": item.get("timestamp") or "",
                "title": item.get("event") or "Billing event",
                "detail": item.get("detail") or "",
                "tone": item.get("tone") or "blue",
                "category": event_type,
            }
        )
    feed.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return feed[:limit]


def _render_invoice_pdf_response(payload, filename="customer-invoice.pdf"):
    rows = payload.get("summary", [])
    brand = payload.get("invoice_brand", {})
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 0.65 * inch
    y = height - margin
    brand_red = colors.HexColor("#c83d4d")
    brand_blue = colors.HexColor("#2e6fd8")
    brand_yellow = colors.HexColor("#d4a226")
    brand_green = colors.HexColor("#2f9b62")
    ink = colors.HexColor("#1f2530")
    muted = colors.HexColor("#5a6a80")
    panel_fill = colors.HexColor("#f7f9fc")

    def new_page():
        nonlocal y
        pdf.showPage()
        y = height - margin

    def ensure_space(required):
        nonlocal y
        if y - required <= margin:
            new_page()

    def draw_line(text, x, top, font_name="Helvetica", font_size=11, fill=ink):
        pdf.setFillColor(fill)
        pdf.setFont(font_name, font_size)
        pdf.drawString(x, top, text[:120])

    pdf.setFillColor(brand_blue)
    pdf.roundRect(margin, height - 1.65 * inch, width - (margin * 2), 1.05 * inch, 14, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(margin + 18, height - 0.95 * inch, brand.get("company_name") or "BaseTrue Billing Statement")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(margin + 18, height - 1.22 * inch, brand.get("tagline") or "Contract usage, invoicing, and customer access summary")

    pdf.setFillColor(brand_red)
    pdf.circle(width - margin - 28, height - 0.96 * inch, 9, stroke=0, fill=1)
    pdf.setFillColor(brand_yellow)
    pdf.circle(width - margin - 52, height - 0.96 * inch, 9, stroke=0, fill=1)
    pdf.setFillColor(brand_green)
    pdf.circle(width - margin - 76, height - 0.96 * inch, 9, stroke=0, fill=1)

    y = height - 1.95 * inch
    pdf.setFillColor(panel_fill)
    pdf.roundRect(margin, y - 50, width - (margin * 2), 50, 12, stroke=0, fill=1)
    draw_line(f"Tenant: {payload.get('tenant_key')}", margin + 16, y - 16, font_name="Helvetica-Bold")
    draw_line(f"Client: {payload.get('client_key')}", margin + 16, y - 34, fill=muted)
    draw_line(f"Billing Window: {payload.get('window_days')} days", width / 2, y - 16, font_name="Helvetica-Bold")
    draw_line(f"Invoices Included: {len(rows)}", width / 2, y - 34, fill=muted)
    y -= 78

    for row in rows:
        ensure_space(210)
        pdf.setFillColor(panel_fill)
        pdf.roundRect(margin, y - 196, width - (margin * 2), 192, 12, stroke=0, fill=1)
        pdf.setFillColor(brand_blue)
        pdf.rect(margin, y - 196, 8, 192, stroke=0, fill=1)

        draw_line(row.get("invoice_number") or "Invoice", margin + 20, y - 18, font_name="Helvetica-Bold", font_size=14)
        due_date = (timezone.now().date() + timedelta(days=15)).isoformat()
        draw_line(f"Plan {row.get('billing_plan')}  |  Units {row.get('billable_units')}  |  Usage {row.get('usage_pct')}%", margin + 20, y - 38, fill=muted)
        draw_line(f"Signature {row.get('invoice_signature')[:42]}", margin + 20, y - 56, font_size=9, fill=muted)
        draw_line(f"Due Date {due_date}", margin + 20, y - 72, font_name="Helvetica-Bold", font_size=10, fill=brand_red)

        table_x = margin + 20
        table_y = y - 90
        table_w = width - (margin * 2) - 34
        row_h = 18
        pdf.setFillColor(colors.HexColor("#eef3fb"))
        pdf.roundRect(table_x, table_y - row_h, table_w, row_h, 4, stroke=0, fill=1)
        draw_line("Line Item", table_x + 8, table_y - 12, font_name="Helvetica-Bold", font_size=9, fill=ink)
        draw_line("Qty", table_x + 230, table_y - 12, font_name="Helvetica-Bold", font_size=9, fill=ink)
        draw_line("Unit", table_x + 280, table_y - 12, font_name="Helvetica-Bold", font_size=9, fill=ink)
        draw_line("Amount", table_x + 355, table_y - 12, font_name="Helvetica-Bold", font_size=9, fill=ink)

        current_y = table_y - row_h - 2
        for item in row.get("invoice_line_items", []):
            pdf.setFillColor(colors.white)
            pdf.roundRect(table_x, current_y - row_h, table_w, row_h, 3, stroke=0, fill=1)
            draw_line(str(item.get("description", "")), table_x + 8, current_y - 12, font_size=9)
            draw_line(str(item.get("quantity", "")), table_x + 230, current_y - 12, font_size=9)
            draw_line(str(item.get("unit_price", "")), table_x + 280, current_y - 12, font_size=9)
            draw_line(str(item.get("amount", "")), table_x + 355, current_y - 12, font_size=9)
            current_y -= row_h + 2

        totals_y = current_y - 2
        draw_line(f"Subtotal {row.get('subtotal_amount')}", table_x + 240, totals_y - 12, font_name="Helvetica-Bold", font_size=10, fill=ink)
        draw_line(f"Tax {row.get('tax_amount')}", table_x + 240, totals_y - 28, font_name="Helvetica-Bold", font_size=10, fill=muted)
        draw_line(f"Total Due {row.get('total_due')}", table_x + 240, totals_y - 46, font_name="Helvetica-Bold", font_size=11, fill=brand_green)
        draw_line("Terms Net 15 · ACH preferred", table_x + 8, totals_y - 46, font_size=9, fill=muted)

        access_link = row.get("access_link", {})
        right_x = width - margin - 190
        draw_line(f"Allowance {row.get('monthly_event_allowance')}", right_x, y - 18, font_name="Helvetica-Bold")
        draw_line(f"Contact {row.get('billing_contact_email') or 'unassigned'}", right_x, y - 38, fill=muted)
        if access_link.get("expires_at"):
            draw_line(f"Link expires {access_link.get('expires_at')[:19]}", right_x, y - 58, fill=muted)
        draw_line(f"Portal uses {access_link.get('use_count', 0)}", right_x, y - 78, fill=muted)
        y -= 220

    ensure_space(42)
    draw_line("Generated by GrassRoots BaseTrue Insights", margin, y - 8, font_size=9, fill=muted)
    draw_line(f"Support {brand.get('support_email') or 'billing@grassroots.local'}", margin, y - 24, font_size=9, fill=muted)
    draw_line("Print-ready invoice artifact", width - margin - 165, y - 8, font_size=9, fill=muted)
    draw_line(timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z"), width - margin - 165, y - 24, font_size=9, fill=muted)

    pdf.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _execute_billing_enforcement_action(tenant_key="default", client_key="", action=""):
    try:
        from .models import ClientContractProfile
    except Exception:
        return {"ok": False, "error": "Profile model unavailable"}

    if not client_key:
        return {"ok": False, "error": "client is required"}

    profile = ClientContractProfile.objects.filter(
        tenant_key=tenant_key or "default",
        client_key=client_key,
        is_active=True,
    ).first()
    if not profile:
        return {"ok": False, "error": "Client profile not found"}

    if action == "enforce_strict_mode":
        profile.strict_negotiation = True
        profile.strict_payload_shape = True
        profile.notes = (profile.notes + "\nEnforced strict mode via billing action.").strip()
        profile.save(update_fields=["strict_negotiation", "strict_payload_shape", "notes", "updated_at"])
        return {"ok": True, "action": action, "client": profile.client_key, "tenant": profile.tenant_key}

    if action == "prepare_upgrade":
        profile.notes = (profile.notes + "\nPrepared plan upgrade via billing action.").strip()
        profile.save(update_fields=["notes", "updated_at"])
        return {"ok": True, "action": action, "client": profile.client_key, "tenant": profile.tenant_key}

    return {"ok": False, "error": "Unsupported action"}


def _schema_contract_catalog():
    required = [
        "schema_version",
        "export_format",
        "generated",
        "period",
        "snapshot_count",
        "snapshots",
    ]
    optional_v1 = [
        "title",
        "window_start",
        "avg_pressure",
        "avg_priority_score",
        "latest",
        "note",
        "schema_notes",
        "schema_hash",
    ]
    optional_v11 = optional_v1 + [
        "schema_roadmap_ref",
    ]
    optional_v20 = optional_v11 + [
        "schema_negotiation_hints",
        "contract_lifecycle",
    ]
    return {
        "0.9.0": {
            "status": "retired",
            "lifecycle_state": "sunset",
            "export_enabled": False,
            "required_fields": required,
            "optional_fields": optional_v1,
            "sunset_after": "2026-06-01",
        },
        "1.0.0": {
            "status": "supported",
            "lifecycle_state": "deprecated",
            "export_enabled": True,
            "required_fields": required,
            "optional_fields": optional_v1,
            "sunset_after": "2027-01-31",
        },
        "1.1.0": {
            "status": "supported",
            "lifecycle_state": "active",
            "export_enabled": True,
            "required_fields": required,
            "optional_fields": optional_v11,
        },
        "2.0.0": {
            "status": "preview",
            "lifecycle_state": "experimental",
            "export_enabled": True,
            "required_fields": required,
            "optional_fields": optional_v20,
        },
    }


def _schema_hash_for(contract):
    source = (
        "|".join(contract.get("required_fields", []))
        + "||"
        + "|".join(contract.get("optional_fields", []))
        + "||"
        + contract.get("version", "")
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def _schema_deprecation_policy():
    return {
        "policy_version": "1.0",
        "notice_period_days": CONTRACT_STABILITY_WINDOW_DAYS,
        "announcement_channels": [
            "schema endpoint",
            "schema_notes in export payload",
            "schema diff endpoint",
        ],
        "deprecated_fields": [
            {
                "field": "schema_version=1.0.0",
                "state": "deprecated",
                "sunset_after": "2027-01-31",
                "replacement": "1.1.0",
            }
        ],
        "renamed_fields": [],
    }


def _schema_evolution_roadmap():
    return [
        {
            "target_version": "1.1.0",
            "status": "released",
            "notes": "Add roadmap reference field and expanded anomaly payload metadata.",
            "breaking": False,
        },
        {
            "target_version": "2.0.0",
            "status": "proposed",
            "notes": "Potential major contract redesign if retrospective domains expand beyond current snapshots.",
            "breaking": True,
        },
    ]


def _schema_stability_window(now_date):
    stable_until = CONTRACT_RELEASE_DATE + timedelta(days=CONTRACT_STABILITY_WINDOW_DAYS)
    return {
        "release_date": CONTRACT_RELEASE_DATE.isoformat(),
        "stability_window_days": CONTRACT_STABILITY_WINDOW_DAYS,
        "breaking_change_free_until": stable_until.isoformat(),
        "within_window": now_date <= stable_until,
    }


def _schema_diff_payload(from_version, to_version, catalog):
    left = catalog.get(from_version)
    right = catalog.get(to_version)
    if not left or not right:
        return None

    left_required = set(left.get("required_fields", []))
    right_required = set(right.get("required_fields", []))
    left_optional = set(left.get("optional_fields", []))
    right_optional = set(right.get("optional_fields", []))

    return {
        "from_version": from_version,
        "to_version": to_version,
        "required_added": sorted(right_required - left_required),
        "required_removed": sorted(left_required - right_required),
        "optional_added": sorted(right_optional - left_optional),
        "optional_removed": sorted(left_optional - right_optional),
        "breaking_change_detected": bool((left_required - right_required) or (right_required - left_required)),
    }


def _dashboard_view(request):
    context = dict(admin.site.each_context(request))
    context.update(build_admin_metrics())
    return TemplateResponse(request, "admin/platform_dashboard.html", context)


def _score_sentiment(text):
    positive_words = {
        "good",
        "great",
        "excellent",
        "love",
        "clear",
        "helpful",
        "progress",
        "thanks",
        "positive",
        "win",
        "success",
        "awesome",
        "improve",
        "strong",
        "support",
    }
    negative_words = {
        "bad",
        "issue",
        "problem",
        "broken",
        "bug",
        "slow",
        "confusing",
        "delay",
        "negative",
        "risk",
        "complaint",
        "hard",
        "stale",
        "blocked",
        "urgent",
    }

    tokens = re.findall(r"[a-z']+", (text or "").lower())
    positive_hits = sum(1 for token in tokens if token in positive_words)
    negative_hits = sum(1 for token in tokens if token in negative_words)
    score = positive_hits - negative_hits

    if score >= 2:
        label = "Positive"
    elif score <= -2:
        label = "Negative"
    else:
        label = "Neutral"

    return {
        "score": score,
        "label": label,
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
    }


def _build_operator_automation(request, metrics):
    default_payload = {
        "task_status_counts": [],
        "flow_status_counts": [],
        "automation_rules": [],
        "rules_engine": [],
        "automation_queue": [],
        "automation_queue_count": 0,
        "automation_queue_ratio": 0,
        "automation_focus": {
            "title": "Workflow automation unavailable",
            "note": "Task and flow models could not be loaded.",
        },
        "auto_routing": {
            "label": "Unavailable",
            "routing_score": 0,
            "summary": "Auto-routing intelligence is unavailable.",
            "delta_basis": "7d activity vs prior 7d",
            "threshold_key": "red",
            "trend": "flat",
            "trend_symbol": "→",
            "delta": 0,
            "quadrant_key": "red",
            "quadrant_label": "Red Quadrant",
            "rules": [],
            "recommendations": [],
        },
    }

    try:
        homepage_task = apps.get_model("homepage_backend", "HomepageTask")
        homepage_flow = apps.get_model("homepage_backend", "HomepageFlow")
    except Exception:
        return default_payload

    task_qs = homepage_task.objects.all()
    flow_qs = homepage_flow.objects.all()

    task_status_counts = [
        {"label": label, "count": task_qs.filter(status=value).count()}
        for value, label in homepage_task.STATUS_CHOICES
    ]
    flow_status_counts = [
        {"label": label, "count": flow_qs.filter(status=value).count()}
        for value, label in homepage_flow.STATUS_CHOICES
    ]

    todo_count = task_qs.filter(status=homepage_task.STATUS_TODO).count()
    doing_count = task_qs.filter(status=homepage_task.STATUS_DOING).count()
    done_count = task_qs.filter(status=homepage_task.STATUS_DONE).count()
    blocked_flow_count = flow_qs.filter(status=homepage_flow.STATUS_BLOCKED).count()
    active_flow_count = flow_qs.filter(status=homepage_flow.STATUS_ACTIVE).count()

    automation_rules = [
        {
            "label": "Blocked flow escalation",
            "status": "ready" if blocked_flow_count else "idle",
            "trigger": f"{blocked_flow_count} blocked flows",
            "action": "Escalate blocked flows to the review queue",
            "url": "/admin/homepage_backend/homepageflow/?status__exact=blocked",
        },
        {
            "label": "Task queue balancing",
            "status": "ready" if todo_count > doing_count else "monitor",
            "trigger": f"{todo_count} todo / {doing_count} doing tasks",
            "action": "Rebalance the taskboard into active work",
            "url": "/admin/homepage_backend/homepagetask/?status__exact=todo",
        },
        {
            "label": "Completion sweep",
            "status": "ready" if done_count else "idle",
            "trigger": f"{done_count} completed tasks",
            "action": "Review finished work for archive or follow-up",
            "url": "/admin/homepage_backend/homepagetask/?status__exact=done",
        },
        {
            "label": "Active flow refresh",
            "status": "ready" if active_flow_count else "idle",
            "trigger": f"{active_flow_count} active flows",
            "action": "Keep active flows moving through the pipeline",
            "url": "/admin/homepage_backend/homepageflow/?status__exact=active",
        },
    ]

    rules_engine = [
        {
            "rule": "If blocked flows > 0",
            "priority": "high" if blocked_flow_count else "low",
            "condition": f"Blocked flows = {blocked_flow_count}",
            "action": "Escalate flow blockers before opening new work.",
        },
        {
            "rule": "If todo tasks exceed doing tasks",
            "priority": "high" if todo_count > doing_count else "medium",
            "condition": f"Todo {todo_count} vs Doing {doing_count}",
            "action": "Pull backlog items into active execution.",
        },
        {
            "rule": "If completed tasks exist",
            "priority": "medium" if done_count else "low",
            "condition": f"Completed tasks = {done_count}",
            "action": "Sweep completed work into archive or follow-up.",
        },
        {
            "rule": "If active flows are running",
            "priority": "medium" if active_flow_count else "low",
            "condition": f"Active flows = {active_flow_count}",
            "action": "Maintain forward movement and reduce idle time.",
        },
    ]

    automation_queue = []
    if blocked_flow_count:
        automation_queue.append(
            {
                "label": "Escalate blocked flows",
                "detail": "Review the blocked queue before starting new work.",
                "url": "/admin/homepage_backend/homepageflow/?status__exact=blocked",
            }
        )
    if todo_count > doing_count:
        automation_queue.append(
            {
                "label": "Triage todo tasks",
                "detail": "Move the backlog toward Doing to reduce queue pressure.",
                "url": "/admin/homepage_backend/homepagetask/?status__exact=todo",
            }
        )
    if done_count:
        automation_queue.append(
            {
                "label": "Sweep completed tasks",
                "detail": "Review finished items for archive or handoff.",
                "url": "/admin/homepage_backend/homepagetask/?status__exact=done",
            }
        )

    automation_focus = {
        "title": "Workflow automation readiness",
        "note": "Automation should begin with the highest queue friction.",
        "summary": f"{len(automation_queue)} immediate automation opportunities",
    }
    automation_queue_ratio = min(100, len(automation_queue) * 25)

    backlog_gap = max(0, todo_count - doing_count)
    completion_credit = min(20, done_count * 2)
    routing_score = max(
        0,
        min(
            100,
            55
            + min(20, active_flow_count * 4)
            + completion_credit
            - min(30, blocked_flow_count * 8)
            - min(25, backlog_gap * 3),
        ),
    )

    if routing_score >= 75:
        routing_label = "Optimized"
        routing_summary = "Auto-routing can prioritize throughput lanes with low operational friction."
    elif routing_score >= 50:
        routing_label = "Adaptive"
        routing_summary = "Auto-routing should rebalance backlog and unblock targeted flow lanes."
    else:
        routing_label = "Constrained"
        routing_summary = "Auto-routing should focus on blockers before expanding task intake."

    now = timezone.now()
    current_7d_start = now - timedelta(days=7)
    previous_7d_start = now - timedelta(days=14)
    routing_activity_7d = LogEntry.objects.filter(
        content_type__app_label="homepage_backend",
        action_time__gte=current_7d_start,
    ).count()
    routing_activity_prev_7d = LogEntry.objects.filter(
        content_type__app_label="homepage_backend",
        action_time__gte=previous_7d_start,
        action_time__lt=current_7d_start,
    ).count()

    routing_delta = routing_activity_7d - routing_activity_prev_7d
    if routing_delta > 0:
        routing_trend = "up"
        routing_symbol = "↑"
    elif routing_delta < 0:
        routing_trend = "down"
        routing_symbol = "↓"
    else:
        routing_trend = "flat"
        routing_symbol = "→"

    if routing_score >= 75:
        threshold_key = "green"
    elif routing_score >= 50:
        threshold_key = "yellow"
    else:
        threshold_key = "red"

    if routing_score >= 75 and routing_trend == "up":
        quadrant_key = "green"
        quadrant_label = "Green Quadrant"
    elif routing_score >= 75:
        quadrant_key = "blue"
        quadrant_label = "Blue Quadrant"
    elif routing_score >= 50:
        quadrant_key = "yellow"
        quadrant_label = "Yellow Quadrant"
    else:
        quadrant_key = "red"
        quadrant_label = "Red Quadrant"

    routing_rules = [
        {
            "lane": "Flow Recovery Lane",
            "condition": f"Blocked flows = {blocked_flow_count}",
            "action": "Route blocked flows to the escalation lane and assign immediate review.",
            "priority": "high" if blocked_flow_count else "low",
            "url": "/admin/homepage_backend/homepageflow/?status__exact=blocked",
        },
        {
            "lane": "Activation Lane",
            "condition": f"Todo {todo_count} vs Doing {doing_count}",
            "action": "Route oldest todo tasks into active doing slots.",
            "priority": "high" if todo_count > doing_count else "medium",
            "url": "/admin/homepage_backend/homepagetask/?status__exact=todo",
        },
        {
            "lane": "Completion Lane",
            "condition": f"Done tasks = {done_count}",
            "action": "Route completed tasks into verification and archive workflows.",
            "priority": "medium" if done_count else "low",
            "url": "/admin/homepage_backend/homepagetask/?status__exact=done",
        },
    ]

    routing_recommendations = []
    if blocked_flow_count:
        routing_recommendations.append(
            {
                "label": "Clear blocked flow lane",
                "detail": f"{blocked_flow_count} blocked flows should be routed to rapid escalation.",
                "url": "/admin/homepage_backend/homepageflow/?status__exact=blocked",
            }
        )
    if todo_count > doing_count:
        routing_recommendations.append(
            {
                "label": "Promote backlog tasks",
                "detail": f"Backlog gap is {backlog_gap}; route priority todo tasks into active doing.",
                "url": "/admin/homepage_backend/homepagetask/?status__exact=todo",
            }
        )
    if done_count:
        routing_recommendations.append(
            {
                "label": "Finalize completed work",
                "detail": f"{done_count} completed tasks are ready for verification routing.",
                "url": "/admin/homepage_backend/homepagetask/?status__exact=done",
            }
        )
    if not routing_recommendations:
        routing_recommendations.append(
            {
                "label": "Maintain route cadence",
                "detail": "Routing lanes are balanced; continue monitoring active flow turnover.",
                "url": "/admin/homepage_backend/homepageflow/?status__exact=active",
            }
        )

    return {
        "task_status_counts": task_status_counts,
        "flow_status_counts": flow_status_counts,
        "automation_rules": automation_rules,
        "rules_engine": rules_engine,
        "automation_queue": automation_queue,
        "automation_queue_count": len(automation_queue),
        "automation_queue_ratio": automation_queue_ratio,
        "automation_focus": automation_focus,
        "auto_routing": {
            "label": routing_label,
            "routing_score": routing_score,
            "summary": routing_summary,
            "delta_basis": "7d activity vs prior 7d",
            "threshold_key": threshold_key,
            "trend": routing_trend,
            "trend_symbol": routing_symbol,
            "delta": routing_delta,
            "quadrant_key": quadrant_key,
            "quadrant_label": quadrant_label,
            "rules": routing_rules,
            "recommendations": routing_recommendations,
        },
    }


def _build_moderator_sentiment(request):
    default_payload = {
        "sentiment_totals": [],
        "sentiment_timeline": [],
        "sentiment_insights": [
            {
                "label": "Net sentiment score",
                "value": "0",
                "secondary": "Neutral fallback when forum analytics cannot be computed.",
            }
        ],
        "sentiment_focus": {
            "label": "Sentiment unavailable",
            "summary": "Forum sentiment could not be computed.",
        },
        "sentiment_posts": [],
        "sentiment_top_positive": None,
        "sentiment_top_negative": None,
        "escalation_workflows": [],
        "escalation_queue": [],
    }

    try:
        forum_post = apps.get_model("forums", "ForumPost")
    except Exception:
        return default_payload

    forum_qs = forum_post.objects.select_related("author")
    posts_30d = forum_qs.filter(created_at__gte=timezone.now() - timedelta(days=30))
    forum_posts_30d = posts_30d.count()
    unique_authors_30d = posts_30d.values("author_id").distinct().count()

    scored_posts = []
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    total_score = 0

    for post in posts_30d.order_by("-created_at")[:60]:
        sentiment = _score_sentiment(f"{post.title} {post.body}")
        total_score += sentiment["score"]
        bucket = sentiment["label"].lower()
        sentiment_counts[bucket] += 1
        scored_posts.append(
            {
                "id": post.id,
                "title": post.title,
                "author": post.author,
                "forum_type": post.get_forum_type_display(),
                "created_at": post.created_at,
                "score": sentiment["score"],
                "label": sentiment["label"],
                "url": f"/admin/forums/forumpost/{post.id}/change/",
            }
        )

    timeline = []
    peak = 1
    for index in range(13, -1, -1):
        day = timezone.now().date() - timedelta(days=index)
        day_posts = posts_30d.filter(created_at__date=day)
        day_score = 0
        count = 0
        for post in day_posts:
            sentiment = _score_sentiment(f"{post.title} {post.body}")
            day_score += sentiment["score"]
            count += 1
        peak = max(peak, abs(day_score), count)
        timeline.append(
            {
                "day": day.strftime("%a"),
                "count": count,
                "score": day_score,
                "url": f"/admin/forums/forumpost/?created_at__date__exact={day.isoformat()}",
            }
        )
    for row in timeline:
        row["pct"] = int((abs(row["score"]) / peak) * 100) if peak else 0

    top_positive = max(scored_posts, key=lambda row: row["score"], default=None)
    top_negative = min(scored_posts, key=lambda row: row["score"], default=None)

    if top_positive and top_positive["score"] > 0:
        focus_label = "Positive discussion"
        focus_summary = f"{top_positive['title']} is driving the strongest positive signal."
    elif top_negative and top_negative["score"] < 0:
        focus_label = "Negative discussion"
        focus_summary = f"{top_negative['title']} needs moderation attention."
    else:
        focus_label = "Balanced discussion"
        focus_summary = "Forum sentiment is currently close to neutral."

    sentiment_totals = [
        {"label": "Positive", "count": sentiment_counts["positive"], "pct": int((sentiment_counts["positive"] / max(len(scored_posts), 1)) * 100)},
        {"label": "Neutral", "count": sentiment_counts["neutral"], "pct": int((sentiment_counts["neutral"] / max(len(scored_posts), 1)) * 100)},
        {"label": "Negative", "count": sentiment_counts["negative"], "pct": int((sentiment_counts["negative"] / max(len(scored_posts), 1)) * 100)},
    ]

    sentiment_insights = [
        {
            "label": "Net sentiment score",
            "value": str(total_score),
            "secondary": "Higher is more positive.",
        },
        {
            "label": "Positive share",
            "value": f"{sentiment_totals[0]['pct']}%",
            "secondary": f"{sentiment_counts['positive']} positive posts in the last 30 days.",
        },
        {
            "label": "Negative share",
            "value": f"{sentiment_totals[2]['pct']}%",
            "secondary": f"{sentiment_counts['negative']} negative posts in the last 30 days.",
        },
    ]

    escalation_workflows = []
    escalation_queue = []
    if sentiment_counts["negative"] > sentiment_counts["positive"]:
        escalation_workflows.append(
            {
                "label": "Negative thread review",
                "priority": "high",
                "trigger": f"{sentiment_counts['negative']} negative posts",
                "action": "Review the most negative posts and reply with clarification or moderation.",
            }
        )
    if moderation_actions_7d := LogEntry.objects.filter(
        content_type__app_label="forums",
        action_time__gte=timezone.now() - timedelta(days=7),
    ).count():
        escalation_workflows.append(
            {
                "label": "Moderation follow-up",
                "priority": "medium",
                "trigger": f"{moderation_actions_7d} moderation actions",
                "action": "Audit recent moderator actions for consistency and coverage.",
            }
        )
    if unique_authors_30d <= 2 and forum_posts_30d >= 8:
        escalation_workflows.append(
            {
                "label": "Participation concentration",
                "priority": "high",
                "trigger": f"{unique_authors_30d} active authors in 30d",
                "action": "Escalate to community outreach and diversify participation.",
            }
        )

    for workflow in escalation_workflows:
        escalation_queue.append(
            {
                "label": workflow["label"],
                "detail": workflow["action"],
                "priority": workflow["priority"],
            }
        )

    return {
        "sentiment_totals": sentiment_totals,
        "sentiment_timeline": timeline,
        "sentiment_insights": sentiment_insights,
        "sentiment_focus": {
            "label": focus_label,
            "summary": focus_summary,
        },
        "sentiment_posts": scored_posts[:8],
        "sentiment_top_positive": top_positive,
        "sentiment_top_negative": top_negative,
        "escalation_workflows": escalation_workflows,
        "escalation_queue": escalation_queue,
    }


def _operator_dashboard_view(request):
    context = dict(admin.site.each_context(request))
    metrics = build_admin_metrics()
    context.update(metrics)

    operator_labels = {"homepage_backend", "center", "twist", "seeds"}
    operator_deep_links = {
        "homepage_backend": [
            {"label": "Flow List", "url": "/admin/homepage_backend/homepageflow/"},
            {"label": "Taskboard", "url": "/admin/homepage_backend/homepagetask/"},
            {"label": "Create Task", "url": "/admin/homepage_backend/homepagetask/add/"},
            {"label": "Create Flow", "url": "/admin/homepage_backend/homepageflow/add/"},
        ],
        "center": [
            {"label": "Work In Progress", "url": "/admin/center/corporationitem/?work_status__exact=in_progress"},
            {"label": "Pending Review", "url": "/admin/center/corporationitem/?status__exact=review"},
            {"label": "Overdue Queue", "url": "/admin/center/corporationitem/?status__in=draft%2Creview%2Capproved"},
            {"label": "Posted", "url": "/admin/center/corporationitem/?status__exact=posted"},
        ],
        "twist": [
            {"label": "Raw Ideas", "url": "/admin/twist/creativeidea/?status__exact=RAW"},
            {"label": "Seed Ideas", "url": "/admin/twist/creativeidea/?status__exact=SEED"},
            {"label": "Business Ideas", "url": "/admin/twist/creativeidea/?status__exact=BUSINESS"},
            {"label": "Create Idea", "url": "/admin/twist/creativeidea/add/"},
        ],
        "seeds": [
            {"label": "Ideas", "url": "/admin/seeds/idea/"},
            {"label": "Seeds", "url": "/admin/seeds/seed/"},
            {"label": "Businesses", "url": "/admin/seeds/business/"},
            {"label": "Cross References", "url": "/admin/seeds/crossreference/"},
        ],
    }
    operator_priority_by_app = {
        "homepage_backend": "/admin/homepage_backend/homepagetask/",
        "center": "/admin/center/corporationitem/?status__exact=review",
        "twist": "/admin/twist/creativeidea/?status__exact=RAW",
        "seeds": "/admin/seeds/idea/?status__exact=RAW",
    }
    operator_apps = [
        panel for panel in metrics.get("app_control_panels", [])
        if panel.get("app_label") in operator_labels
    ]
    for panel in operator_apps:
        panel["operator_links"] = operator_deep_links.get(panel.get("app_label"), [])
        default_priority_url = operator_priority_by_app.get(panel.get("app_label"), panel.get("route"))
        priority_label = "Priority Queue"
        flags = panel.get("health", {}).get("attention_flags", [])
        joined_flags = " ".join(flags).lower()
        if "stale" in joined_flags or "no activity" in joined_flags:
            priority_label = "Stale Queue"
        elif "trending down" in joined_flags:
            priority_label = "Declining Queue"
        elif "backlog" in joined_flags:
            priority_label = "Backlog Queue"

        panel["operator_priority_link"] = {
            "label": priority_label,
            "url": default_priority_url,
        }

    operator_alerts = []
    for panel in operator_apps:
        for flag in panel.get("health", {}).get("attention_flags", []):
            operator_alerts.append(
                {
                    "app": panel.get("title"),
                    "flag": flag,
                }
            )

    context.update(
        {
            "operator_apps": operator_apps,
            "operator_alerts": operator_alerts,
            "operator_automation": _build_operator_automation(request, metrics),
        }
    )
    return TemplateResponse(request, "admin/operator_dashboard.html", context)


def _moderator_dashboard_view(request):
    context = dict(admin.site.each_context(request))
    metrics = build_admin_metrics()
    context.update(metrics)

    forum_deep_links = [
        {"label": "All Posts", "url": "/admin/forums/forumpost/"},
        {"label": "City", "url": "/admin/forums/forumpost/?forum_type__exact=city"},
        {"label": "State", "url": "/admin/forums/forumpost/?forum_type__exact=state"},
        {"label": "National", "url": "/admin/forums/forumpost/?forum_type__exact=national"},
        {"label": "Global", "url": "/admin/forums/forumpost/?forum_type__exact=global"},
        {"label": "Create Post", "url": "/admin/forums/forumpost/add/"},
    ]

    default_payload = {
        "forum_total": 0,
        "forum_posts_7d": 0,
        "forum_posts_30d": 0,
        "forum_posts_per_week": 0.0,
        "unique_authors_30d": 0,
        "forum_mix": [],
        "top_authors": [],
        "recent_posts": [],
        "moderation_activity": [],
        "moderation_actions_7d": 0,
        "community_timeline": [],
        "moderator_alerts": [],
        "forum_deep_links": forum_deep_links,
        "moderator_community_health": {
            "score": 0,
            "label": "Unavailable",
            "note": "Community health scoring could not be computed.",
            "delta_basis": "Current scoring window vs prior matched window",
            "threshold_key": "red",
            "trend": "flat",
            "trend_symbol": "→",
            "delta": 0,
            "quadrant_key": "red",
            "quadrant_label": "Red Quadrant",
            "components": [],
            "watchlist": [],
        },
    }

    try:
        forum_post = apps.get_model("forums", "ForumPost")
        forum_qs = forum_post.objects.all()
    except Exception:
        context.update(default_payload)
        return TemplateResponse(request, "admin/moderator_dashboard.html", context)

    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    forum_total = forum_qs.count()
    forum_posts_7d = forum_qs.filter(created_at__gte=seven_days_ago).count()
    forum_posts_30d = forum_qs.filter(created_at__gte=thirty_days_ago).count()
    unique_authors_30d = (
        forum_qs.filter(created_at__gte=thirty_days_ago)
        .values("author_id")
        .distinct()
        .count()
    )

    forum_mix = []
    for value, label in forum_post.FORUM_CHOICES:
        count = forum_qs.filter(forum_type=value).count()
        pct = int((count / forum_total) * 100) if forum_total else 0
        forum_mix.append(
            {
                "label": label,
                "count": count,
                "pct": pct,
                "url": f"/admin/forums/forumpost/?forum_type__exact={value}",
            }
        )

    top_authors = [
        {
            "label": row["author__username"] or f"User {row['author_id']}",
            "count": row["total"],
            "url": f"/admin/forums/forumpost/?author__id__exact={row['author_id']}",
        }
        for row in (
            forum_qs.values("author_id", "author__username")
            .annotate(total=Count("id"))
            .order_by("-total")[:8]
        )
    ]

    recent_posts = list(forum_qs.select_related("author").order_by("-created_at")[:14])

    moderation_activity = list(
        LogEntry.objects.select_related("user", "content_type")
        .filter(content_type__app_label="forums")
        .order_by("-action_time")[:20]
    )
    moderation_actions_7d = LogEntry.objects.filter(
        content_type__app_label="forums",
        action_time__gte=seven_days_ago,
    ).count()

    community_timeline = []
    peak = 1
    for index in range(13, -1, -1):
        day = now.date() - timedelta(days=index)
        count = forum_qs.filter(created_at__date=day).count()
        peak = max(peak, count)
        community_timeline.append(
            {
                "day": day.strftime("%a"),
                "count": count,
                "url": f"/admin/forums/forumpost/?created_at__date__exact={day.isoformat()}",
            }
        )
    for row in community_timeline:
        row["pct"] = int((row["count"] / peak) * 100)

    moderator_alerts = []
    if forum_posts_7d == 0:
        moderator_alerts.append("No new forum posts in the last 7 days")
    if forum_total > 0 and moderation_actions_7d == 0:
        moderator_alerts.append("No moderation actions recorded in the last 7 days")
    if forum_posts_30d >= 8 and unique_authors_30d <= 2:
        moderator_alerts.append("Community participation is concentrated in very few authors")
    highest_mix = max(forum_mix, key=lambda item: item["pct"], default=None)
    if highest_mix and highest_mix["pct"] >= 70:
        moderator_alerts.append(f"Discussion is heavily concentrated in {highest_mix['label']}")

    moderator_sentiment = _build_moderator_sentiment(request)
    net_sentiment = int(moderator_sentiment.get("sentiment_insights", [{}])[0].get("value", "0") or 0)

    previous_seven_days_ago = now - timedelta(days=14)
    posts_prev_7d = forum_qs.filter(
        created_at__gte=previous_seven_days_ago,
        created_at__lt=seven_days_ago,
    ).count()
    unique_authors_prev_30d = (
        forum_qs.filter(created_at__gte=now - timedelta(days=60), created_at__lt=thirty_days_ago)
        .values("author_id")
        .distinct()
        .count()
    )
    moderation_actions_prev_7d = LogEntry.objects.filter(
        content_type__app_label="forums",
        action_time__gte=previous_seven_days_ago,
        action_time__lt=seven_days_ago,
    ).count()

    sentiment_timeline = moderator_sentiment.get("sentiment_timeline", [])
    sentiment_current_7d = sum(row.get("score", 0) for row in sentiment_timeline[-7:])
    sentiment_prev_7d = sum(row.get("score", 0) for row in sentiment_timeline[:7])

    engagement_score = min(25, forum_posts_7d * 3)
    diversity_score = min(25, unique_authors_30d * 2)
    sentiment_score = max(0, min(25, 12 + net_sentiment))
    moderation_ratio = (moderation_actions_7d / forum_posts_7d) if forum_posts_7d else 0
    governance_score = min(25, int(moderation_ratio * 35)) if moderation_actions_7d else 4
    total_health_score = engagement_score + diversity_score + sentiment_score + governance_score

    engagement_prev_score = min(25, posts_prev_7d * 3)
    diversity_prev_score = min(25, unique_authors_prev_30d * 2)
    sentiment_prev_score = max(0, min(25, 12 + sentiment_prev_7d))
    moderation_prev_ratio = (moderation_actions_prev_7d / posts_prev_7d) if posts_prev_7d else 0
    governance_prev_score = min(25, int(moderation_prev_ratio * 35)) if moderation_actions_prev_7d else 4
    total_prev_score = engagement_prev_score + diversity_prev_score + sentiment_prev_score + governance_prev_score

    def _trend(current, previous):
        delta = current - previous
        if delta > 0:
            return "up", "↑", delta
        if delta < 0:
            return "down", "↓", delta
        return "flat", "→", delta

    def _quadrant(score, max_score):
        pct = (score / max_score) * 100 if max_score else 0
        if pct >= 80:
            return "green", "Green Quadrant"
        if pct >= 65:
            return "blue", "Blue Quadrant"
        if pct >= 50:
            return "yellow", "Yellow Quadrant"
        return "red", "Red Quadrant"

    overall_trend, overall_symbol, overall_delta = _trend(total_health_score, total_prev_score)
    overall_quadrant_key, overall_quadrant_label = _quadrant(total_health_score, 100)

    if total_health_score >= 75:
        health_label = "Healthy"
        health_note = "Community dynamics are balanced and moderation coverage is strong."
        threshold_key = "green"
    elif total_health_score >= 55:
        health_label = "Watch"
        health_note = "Community is active but requires targeted moderation oversight."
        threshold_key = "yellow"
    else:
        health_label = "At Risk"
        health_note = "Community health signals indicate intervention is needed."
        threshold_key = "red"

    component_specs = [
        {
            "label": "Engagement",
            "score": engagement_score,
            "prev": engagement_prev_score,
            "detail": f"{forum_posts_7d} posts in 7 days",
        },
        {
            "label": "Diversity",
            "score": diversity_score,
            "prev": diversity_prev_score,
            "detail": f"{unique_authors_30d} unique authors in 30 days",
        },
        {
            "label": "Sentiment",
            "score": sentiment_score,
            "prev": sentiment_prev_score,
            "detail": f"Net sentiment {net_sentiment}",
        },
        {
            "label": "Governance",
            "score": governance_score,
            "prev": governance_prev_score,
            "detail": f"{moderation_actions_7d} moderation actions in 7 days",
        },
    ]

    components = []
    for component in component_specs:
        component_trend, component_symbol, component_delta = _trend(component["score"], component["prev"])
        component_quadrant_key, component_quadrant_label = _quadrant(component["score"], 25)
        components.append(
            {
                "label": component["label"],
                "score": component["score"],
                "detail": component["detail"],
                "delta_basis": "current window vs prior matched window",
                "trend": component_trend,
                "trend_symbol": component_symbol,
                "delta": component_delta,
                "quadrant_key": component_quadrant_key,
                "quadrant_label": component_quadrant_label,
            }
        )

    community_health = {
        "score": total_health_score,
        "label": health_label,
        "note": health_note,
        "delta_basis": "Current scoring window vs prior matched window",
        "threshold_key": threshold_key,
        "trend": overall_trend,
        "trend_symbol": overall_symbol,
        "delta": overall_delta,
        "quadrant_key": overall_quadrant_key,
        "quadrant_label": overall_quadrant_label,
        "components": components,
        "watchlist": moderator_alerts[:4],
    }

    context.update(
        {
            "forum_total": forum_total,
            "forum_posts_7d": forum_posts_7d,
            "forum_posts_30d": forum_posts_30d,
            "forum_posts_per_week": round((forum_posts_30d / 30.0) * 7.0, 1) if forum_posts_30d else 0.0,
            "unique_authors_30d": unique_authors_30d,
            "forum_mix": forum_mix,
            "top_authors": top_authors,
            "recent_posts": recent_posts,
            "moderation_activity": moderation_activity,
            "moderation_actions_7d": moderation_actions_7d,
            "community_timeline": community_timeline,
            "moderator_alerts": moderator_alerts,
            "forum_deep_links": forum_deep_links,
            "moderator_sentiment": moderator_sentiment,
            "moderator_community_health": community_health,
        }
    )
    return TemplateResponse(request, "admin/moderator_dashboard.html", context)


def _executive_dashboard_view(request):
    context = dict(admin.site.each_context(request))
    metrics = build_admin_metrics()
    context.update(metrics)

    app_panels = sorted(
        metrics.get("app_control_panels", []),
        key=lambda panel: panel.get("health", {}).get("score", 0),
        reverse=True,
    )
    executive_apps = app_panels[:6]
    executive_risks = sorted(
        metrics.get("app_control_panels", []),
        key=lambda panel: (
            len(panel.get("health", {}).get("attention_flags", [])),
            panel.get("health", {}).get("score", 0),
        ),
        reverse=True,
    )[:5]

    quadrant_rules = [
        ("green", "Green", lambda panel: panel.get("health", {}).get("score", 0) >= 75),
        ("blue", "Blue", lambda panel: 60 <= panel.get("health", {}).get("score", 0) < 75),
        ("yellow", "Yellow", lambda panel: 45 <= panel.get("health", {}).get("score", 0) < 60),
        ("red", "Red", lambda panel: panel.get("health", {}).get("score", 0) < 45),
    ]
    executive_quadrants = []
    for quadrant_key, quadrant_label, matcher in quadrant_rules:
        quadrant_panels = [panel for panel in app_panels if matcher(panel)]
        if quadrant_panels:
            avg_score = round(
                sum(panel.get("health", {}).get("score", 0) for panel in quadrant_panels) / len(quadrant_panels),
                1,
            )
            top_app = max(quadrant_panels, key=lambda panel: panel.get("health", {}).get("score", 0))
            top_app_name = top_app.get("title", "-")
        else:
            avg_score = 0
            top_app_name = "-"
        executive_quadrants.append(
            {
                "key": quadrant_key,
                "label": quadrant_label,
                "count": len(quadrant_panels),
                "avg_score": avg_score,
                "top_app": top_app_name,
            }
        )

    risk_matrix = []
    risk_buckets = [
        ("strong", "rising", "Strong / Rising", lambda panel: panel.get("health", {}).get("score", 0) >= 60 and panel.get("health", {}).get("trend") == "up"),
        ("strong", "cooling", "Strong / Cooling", lambda panel: panel.get("health", {}).get("score", 0) >= 60 and panel.get("health", {}).get("trend") != "up"),
        ("at-risk", "rising", "At Risk / Rising", lambda panel: panel.get("health", {}).get("score", 0) < 60 and panel.get("health", {}).get("trend") == "up"),
        ("at-risk", "cooling", "At Risk / Cooling", lambda panel: panel.get("health", {}).get("score", 0) < 60 and panel.get("health", {}).get("trend") != "up"),
    ]
    for health_bucket, momentum_bucket, label, matcher in risk_buckets:
        bucket_panels = [panel for panel in app_panels if matcher(panel)]
        if bucket_panels:
            top_panel = max(
                bucket_panels,
                key=lambda panel: (
                    len(panel.get("health", {}).get("attention_flags", [])),
                    100 - panel.get("health", {}).get("score", 0),
                ),
            )
            top_label = top_panel.get("title", "-")
            avg_score = round(
                sum(panel.get("health", {}).get("score", 0) for panel in bucket_panels) / len(bucket_panels),
                1,
            )
        else:
            top_label = "-"
            avg_score = 0
        risk_matrix.append(
            {
                "health_bucket": health_bucket,
                "momentum_bucket": momentum_bucket,
                "label": label,
                "count": len(bucket_panels),
                "top_app": top_label,
                "avg_score": avg_score,
            }
        )

    trend_max = max((row.get("count", 0) for row in metrics.get("activity_rows", [])), default=0)
    executive_trend_chart = []
    for row in metrics.get("activity_rows", []):
        count = row.get("count", 0)
        height_pct = 22
        if trend_max:
            height_pct = max(22, round((count / trend_max) * 100))
        executive_trend_chart.append(
            {
                "day": row.get("day", ""),
                "count": count,
                "pct": row.get("pct", 0),
                "height_pct": height_pct,
            }
        )
    trend_peak = max(executive_trend_chart, key=lambda row: row["count"], default={"day": "-", "count": 0})

    average_health_score = 0
    if app_panels:
        average_health_score = sum(
            panel.get("health", {}).get("score", 0) for panel in app_panels
        ) / len(app_panels)

    risk_flag_count = sum(
        len(panel.get("health", {}).get("attention_flags", [])) for panel in app_panels
    )
    bottleneck = metrics.get("semantic_cross_app_analytics", {}).get("bottleneck", {})
    bottleneck_dropoff = bottleneck.get("dropoff_pct", 0)

    forecast_pressure_index = round(
        max(
            0,
            min(
                100,
                (100 - average_health_score) * 0.45
                + risk_flag_count * 4
                + bottleneck_dropoff * 0.35,
            ),
        ),
        1,
    )

    if forecast_pressure_index < 20:
        forecast_label = "Stable"
        forecast_direction = "Leadership outlook is steady with low immediate pressure."
    elif forecast_pressure_index < 40:
        forecast_label = "Watch"
        forecast_direction = "Leadership should monitor the weakest app and the bottleneck stage."
    elif forecast_pressure_index < 65:
        forecast_label = "Elevated"
        forecast_direction = "Portfolio pressure is building and attention is needed on the flagged apps."
    else:
        forecast_label = "Critical"
        forecast_direction = "Near-term execution risk is elevated across the portfolio."

    forecast_focus = bottleneck.get("label") or "the current pipeline bottleneck"
    forecast_top_app = executive_risks[0]["title"] if executive_risks else "the portfolio"

    forecast_horizons = [
        {
            "label": "7 Days",
            "value": round(min(100, forecast_pressure_index + risk_flag_count * 2), 1),
            "note": "Immediate leadership attention window.",
        },
        {
            "label": "30 Days",
            "value": round(min(100, forecast_pressure_index + bottleneck_dropoff * 0.5), 1),
            "note": "Medium-term execution risk outlook.",
        },
        {
            "label": "90 Days",
            "value": round(min(100, forecast_pressure_index + (100 - average_health_score) * 0.3), 1),
            "note": "Long-range recovery or strain outlook.",
        },
    ]

    risk_forecast = {
        "label": forecast_label,
        "summary": forecast_direction,
        "horizons": forecast_horizons,
        "watch_item": forecast_top_app,
        "trigger": forecast_focus,
        "pressure_index": forecast_pressure_index,
        "confidence": round(max(35, 100 - risk_flag_count * 6 - bottleneck_dropoff * 0.4), 1),
    }

    pressure_baseline = metrics.get("cross_dashboard_insights", {}).get("pressure_proxy", forecast_pressure_index)
    pressure_delta = round(forecast_pressure_index - pressure_baseline, 1)
    if pressure_delta > 0:
        pressure_trend = "up"
        pressure_symbol = "↑"
    elif pressure_delta < 0:
        pressure_trend = "down"
        pressure_symbol = "↓"
    else:
        pressure_trend = "flat"
        pressure_symbol = "→"

    if forecast_pressure_index < 40:
        forecast_threshold_key = "green"
    elif forecast_pressure_index < 65:
        forecast_threshold_key = "yellow"
    else:
        forecast_threshold_key = "red"

    if forecast_pressure_index < 40 and pressure_trend == "down":
        forecast_quadrant_key = "green"
        forecast_quadrant_label = "Green Quadrant"
    elif forecast_pressure_index < 40:
        forecast_quadrant_key = "blue"
        forecast_quadrant_label = "Blue Quadrant"
    elif forecast_pressure_index < 65:
        forecast_quadrant_key = "yellow"
        forecast_quadrant_label = "Yellow Quadrant"
    else:
        forecast_quadrant_key = "red"
        forecast_quadrant_label = "Red Quadrant"

    risk_forecast.update(
        {
            "delta_basis": "Current pressure index vs cross-dashboard pressure proxy",
            "threshold_key": forecast_threshold_key,
            "trend": pressure_trend,
            "trend_symbol": pressure_symbol,
            "delta": pressure_delta,
            "quadrant_key": forecast_quadrant_key,
            "quadrant_label": forecast_quadrant_label,
        }
    )

    activity_rows_14d = metrics.get("activity_rows_14d", [])
    activity_last_7 = sum(row.get("count", 0) for row in activity_rows_14d[-7:])
    activity_prev_7 = sum(row.get("count", 0) for row in activity_rows_14d[:7])
    activity_growth_rate = round(((activity_last_7 - activity_prev_7) / activity_prev_7) * 100, 1) if activity_prev_7 else 0.0
    projected_monthly_actions = round(max(activity_last_7, 0) * 4 * (1 + max(activity_growth_rate, 0) / 100), 0)

    user_growth_rows = metrics.get("user_growth_rows", [])
    user_last_7 = sum(row.get("count", 0) for row in user_growth_rows[-7:])
    user_prev_7 = sum(row.get("count", 0) for row in user_growth_rows[:7])
    user_growth_rate = round(((user_last_7 - user_prev_7) / user_prev_7) * 100, 1) if user_prev_7 else 0.0
    projected_monthly_users = round(max(user_last_7, 0) * 4 * (1 + max(user_growth_rate, 0) / 100), 0)

    if activity_growth_rate >= 15 and user_growth_rate >= 10:
        growth_label = "Accelerating"
    elif activity_growth_rate >= 5 or user_growth_rate >= 5:
        growth_label = "Growing"
    else:
        growth_label = "Steady"

    growth_projection = {
        "label": growth_label,
        "activity_growth_rate": activity_growth_rate,
        "user_growth_rate": user_growth_rate,
        "projected_monthly_actions": int(projected_monthly_actions),
        "projected_monthly_users": int(projected_monthly_users),
        "activity_last_7": activity_last_7,
        "activity_prev_7": activity_prev_7,
        "user_last_7": user_last_7,
        "user_prev_7": user_prev_7,
    }

    strategic_scenarios = [
        {
            "label": "Stabilize",
            "pressure": round(max(0, forecast_pressure_index - 12), 1),
            "actions": int(max(activity_last_7, 0) * 3.8),
            "users": int(max(user_last_7, 0) * 3.6),
            "note": "Focus on reducing risk flags and bottleneck drop-off.",
        },
        {
            "label": "Base Plan",
            "pressure": forecast_pressure_index,
            "actions": int(projected_monthly_actions),
            "users": int(projected_monthly_users),
            "note": "Maintain current momentum with active risk monitoring.",
        },
        {
            "label": "Expansion",
            "pressure": round(min(100, forecast_pressure_index + 8), 1),
            "actions": int(projected_monthly_actions * 1.15),
            "users": int(projected_monthly_users * 1.2),
            "note": "Increase throughput while protecting semantic conversion continuity.",
        },
    ]

    strategic_pillars = [
        {
            "label": "Risk Containment",
            "status": "Priority" if risk_flag_count >= 6 else "On Track",
            "value": risk_flag_count,
            "detail": "Open attention flags across app portfolio.",
            "url": "#bt-exec-risks",
        },
        {
            "label": "Pipeline Continuity",
            "status": "Priority" if bottleneck_dropoff >= 45 else "On Track",
            "value": f"{bottleneck_dropoff}%",
            "detail": f"Drop-off around {forecast_focus} stage transition.",
            "url": "#bt-exec-semantic",
        },
        {
            "label": "Growth Cadence",
            "status": "Accelerate" if growth_label != "Steady" else "Maintain",
            "value": f"{growth_projection['activity_growth_rate']}%",
            "detail": "Weekly activity growth trajectory.",
            "url": "#bt-exec-growth",
        },
    ]

    strategic_initiatives = []
    for panel in executive_risks[:3]:
        flags = panel.get("health", {}).get("attention_flags", [])
        strategic_initiatives.append(
            {
                "app": panel.get("title", "Unknown"),
                "priority": "High" if panel.get("health", {}).get("score", 0) < 50 else "Medium",
                "objective": flags[0] if flags else "Sustain current healthy operating trend.",
                "owner": "Operator" if panel.get("health", {}).get("trend") != "up" else "Executive",
                "url": panel.get("route", "#"),
            }
        )

    planning_cycle = [
        {
            "label": "0-30 Days",
            "objective": "Reduce immediate pressure and clear high-risk queue items.",
            "target": max(0, round(forecast_pressure_index - 8, 1)),
        },
        {
            "label": "31-60 Days",
            "objective": "Improve cross-stage conversion and stabilize app health.",
            "target": max(0, round(forecast_pressure_index - 14, 1)),
        },
        {
            "label": "61-90 Days",
            "objective": "Scale growth while keeping risk indicators in watch range.",
            "target": max(0, round(forecast_pressure_index - 20, 1)),
        },
    ]

    user_growth_chart = []
    user_growth_max = max((row.get("count", 0) for row in user_growth_rows), default=0)
    for row in user_growth_rows:
        count = row.get("count", 0)
        height_pct = 18
        if user_growth_max:
            height_pct = max(18, round((count / user_growth_max) * 100))
        user_growth_chart.append(
            {
                "day": row.get("day", ""),
                "count": count,
                "pct": row.get("pct", 0),
                "height_pct": height_pct,
            }
        )

    semantic_data = metrics.get("semantic_cross_app_analytics", {})
    semantic_stage_rows = []
    stage_list = semantic_data.get("stages", [])
    link_list = semantic_data.get("links", [])
    user_link_list = semantic_data.get("user_links", [])
    for index, stage in enumerate(stage_list):
        next_link = link_list[index] if index < len(link_list) else {}
        semantic_stage_rows.append(
            {
                "label": stage.get("label", "-"),
                "count": stage.get("count", 0),
                "last_30_days": stage.get("last_30_days", 0),
                "conversion_pct": next_link.get("conversion_pct", 0),
                "url": stage.get("url", "#"),
            }
        )
    semantic_insight_rows = [
        {
            "label": link.get("from") + " -> " + link.get("to"),
            "value": f"{link.get('conversion_pct', 0)}% conversion",
            "secondary": f"{link.get('dropoff_pct', 0)}% drop-off",
        }
        for link in link_list
    ]
    if user_link_list:
        best_user_link = max(user_link_list, key=lambda row: row.get("overlap_pct", 0))
        semantic_insight_rows.append(
            {
                "label": f"Strongest user continuity: {best_user_link.get('from')} -> {best_user_link.get('to')}",
                "value": f"{best_user_link.get('overlap_pct', 0)}% overlap",
                "secondary": f"{best_user_link.get('overlap', 0)} shared users",
            }
        )
    semantic_insight_rows.append(
        {
            "label": f"Bottleneck: {semantic_data.get('bottleneck', {}).get('label', 'N/A')}",
            "value": f"{semantic_data.get('bottleneck', {}).get('dropoff_pct', 0)}% drop-off",
            "secondary": f"Overall conversion {semantic_data.get('overall_conversion_rate', 0)}%",
        }
    )

    trend_summary = {
        "health_legend": metrics.get("health_legend", {}),
        "pipeline": semantic_data,
        "activity_rows": metrics.get("activity_rows", []),
    }

    context.update(
        {
            "executive_apps": executive_apps,
            "executive_risks": executive_risks,
            "executive_trend_chart": executive_trend_chart,
            "trend_peak": trend_peak,
            "executive_quadrants": executive_quadrants,
            "risk_matrix": risk_matrix,
            "growth_projection": growth_projection,
            "user_growth_chart": user_growth_chart,
            "user_growth_max": user_growth_max,
            "semantic_stage_rows": semantic_stage_rows,
            "semantic_insight_rows": semantic_insight_rows,
            "trend_summary": trend_summary,
            "executive_forecast": {
                "label": forecast_label,
                "pressure_index": forecast_pressure_index,
                "direction": forecast_direction,
                "focus": forecast_focus,
                "top_app": forecast_top_app,
                "average_health_score": round(average_health_score, 1),
                "risk_flag_count": risk_flag_count,
                "bottleneck_dropoff": bottleneck_dropoff,
            },
            "risk_forecast": risk_forecast,
            "executive_strategic_plan": {
                "scenarios": strategic_scenarios,
                "pillars": strategic_pillars,
                "initiatives": strategic_initiatives,
                "cycle": planning_cycle,
            },
        }
    )
    return TemplateResponse(request, "admin/executive_dashboard.html", context)


def _basetrue_insights_view(request):
    if request.method == "POST":
        action = (request.POST.get("billing_console_action") or "").strip()
        billing_tenant = (request.POST.get("billing_tenant") or "").strip()
        billing_client = (request.POST.get("billing_client") or "").strip()
        billing_link_tenant = (request.POST.get("billing_link_tenant") or "").strip()
        billing_link_client = (request.POST.get("billing_link_client") or "").strip()
        billing_link_status = (request.POST.get("billing_link_status") or "").strip().lower()
        billing_link_expires = (request.POST.get("billing_link_expires") or "").strip().lower()
        billing_link_sort = (request.POST.get("billing_link_sort") or "").strip().lower()

        if action == "issue_access_link":
            link = _issue_billing_access_link(
                tenant_key=billing_tenant or "default",
                client_key=billing_client or "all",
                window_days=max(1, _int_param(request.POST.get("window_days"), 30)),
                created_by=request.user if getattr(request.user, "is_authenticated", False) else None,
                label=(request.POST.get("label") or "Customer billing portal").strip(),
                recipient_email=(request.POST.get("recipient_email") or "").strip(),
                ttl_days=max(1, _int_param(request.POST.get("ttl_days"), BILLING_ACCESS_DEFAULT_TTL_DAYS)),
                reuse_existing=False,
            )
            if link:
                messages.success(request, f"Issued billing access link for {link.tenant_key} / {link.client_key}.")
            else:
                messages.error(request, "Unable to issue billing access link.")
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "revoke_access_link":
            try:
                from .models import ContractBillingAccessLink
            except Exception:
                messages.error(request, "Access link model unavailable.")
                return _billing_console_redirect(
                    billing_tenant,
                    billing_client,
                    link_tenant=billing_link_tenant,
                    link_client=billing_link_client,
                    link_status=billing_link_status,
                    link_expires=billing_link_expires,
                    link_sort=billing_link_sort,
                )

            link = ContractBillingAccessLink.objects.filter(id=request.POST.get("link_id")).first()
            if not link:
                messages.error(request, "Access link not found.")
            else:
                link.is_active = False
                link.revoked_at = timezone.now()
                link.save(update_fields=["is_active", "revoked_at", "updated_at"])
                messages.success(request, f"Revoked access link for {link.tenant_key} / {link.client_key}.")
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "bulk_revoke_filtered_access_links":
            try:
                from .models import ContractBillingAccessLink
            except Exception:
                messages.error(request, "Access link model unavailable.")
                return _billing_console_redirect(
                    billing_tenant,
                    billing_client,
                    link_tenant=billing_link_tenant,
                    link_client=billing_link_client,
                    link_status=billing_link_status,
                    link_expires=billing_link_expires,
                    link_sort=billing_link_sort,
                )

            revoke_confirmed = _parse_bool(request.POST.get("bulk_revoke_confirm"))
            if not revoke_confirmed:
                messages.error(request, "Bulk revoke requires confirmation. Tick the confirmation checkbox and retry.")
                return _billing_console_redirect(
                    billing_tenant,
                    billing_client,
                    link_tenant=billing_link_tenant,
                    link_client=billing_link_client,
                    link_status=billing_link_status,
                    link_expires=billing_link_expires,
                    link_sort=billing_link_sort,
                )

            resolved_link_tenant = billing_link_tenant or billing_tenant
            resolved_link_client = billing_link_client or billing_client
            filtered_links = _billing_access_links_payload(
                tenant_key=resolved_link_tenant,
                client_key=resolved_link_client,
                window_days=30,
                limit=500,
                status_filter=billing_link_status or "all",
                expires_filter=billing_link_expires or "all",
                sort_by=billing_link_sort or "newest",
            )
            link_ids = [row.get("id") for row in filtered_links if row.get("id")]
            queryset = ContractBillingAccessLink.objects.filter(id__in=link_ids, is_active=True, revoked_at__isnull=True)
            revoked_count = 0
            now = timezone.now()
            for link in queryset:
                link.is_active = False
                link.revoked_at = now
                link.save(update_fields=["is_active", "revoked_at", "updated_at"])
                revoked_count += 1

            if revoked_count:
                messages.success(request, f"Revoked {revoked_count} access links from the filtered set.")
            else:
                messages.warning(request, "No active access links matched the current filtered set.")
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "bulk_issue_access_links":
            bulk_limit = max(1, min(100, _int_param(request.POST.get("bulk_issue_limit"), 20)))
            window_days = max(1, _int_param(request.POST.get("window_days"), 30))
            ttl_days = max(1, _int_param(request.POST.get("ttl_days"), BILLING_ACCESS_DEFAULT_TTL_DAYS))
            label = (request.POST.get("label") or "Customer billing portal").strip() or "Customer billing portal"
            recipient_email = (request.POST.get("recipient_email") or "").strip()

            summary_payload = _contract_billing_summary_payload(
                window_days=30,
                tenant_key=billing_tenant,
                client_key=billing_client,
            )
            summary_rows = summary_payload.get("summary", [])[:bulk_limit]

            issued_count = 0
            for row in summary_rows:
                link = _issue_billing_access_link(
                    tenant_key=row.get("tenant_key") or "default",
                    client_key=row.get("client_key") or "all",
                    window_days=window_days,
                    created_by=request.user if getattr(request.user, "is_authenticated", False) else None,
                    label=label,
                    recipient_email=recipient_email,
                    ttl_days=ttl_days,
                    reuse_existing=False,
                )
                if link:
                    issued_count += 1

            if issued_count:
                messages.success(request, f"Issued {issued_count} access links from filtered billing rows.")
            else:
                messages.warning(request, "No billing rows available for bulk issue with current filters.")
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "bulk_issue_preset_batch":
            preset_batch_size = max(1, min(20, _int_param(request.POST.get("preset_batch_size"), 5)))
            preset_window_days = max(1, _int_param(request.POST.get("window_days"), 30))
            preset_ttl_days = max(1, _int_param(request.POST.get("ttl_days"), BILLING_ACCESS_DEFAULT_TTL_DAYS))
            preset_label = (request.POST.get("label") or "Customer billing portal").strip() or "Customer billing portal"

            summary_payload = _contract_billing_summary_payload(
                window_days=30,
                tenant_key=billing_tenant,
                client_key=billing_client,
            )
            presets = _bulk_issue_presets_payload(summary_payload.get("summary", []), limit=preset_batch_size)
            issued_count = 0
            for preset in presets:
                link = _issue_billing_access_link(
                    tenant_key=preset.get("tenant_key") or "default",
                    client_key=preset.get("client_key") or "all",
                    window_days=preset_window_days,
                    created_by=request.user if getattr(request.user, "is_authenticated", False) else None,
                    label=preset_label,
                    recipient_email="",
                    ttl_days=preset_ttl_days,
                    reuse_existing=False,
                )
                if link:
                    issued_count += 1

            if issued_count:
                messages.success(request, f"Issued {issued_count} links using tenant/client presets.")
            else:
                messages.warning(request, "No preset tenant/client pairs available for bulk issue.")
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "send_invoice_email":
            invoice_tenant = (request.POST.get("invoice_tenant") or billing_tenant or "default").strip() or "default"
            invoice_client = (request.POST.get("invoice_client") or billing_client or "all").strip() or "all"
            recipient_email = (request.POST.get("recipient_email") or "").strip()

            summary_payload = _contract_billing_summary_payload(
                window_days=30,
                tenant_key=invoice_tenant,
                client_key=invoice_client,
            )
            rows = summary_payload.get("summary", [])
            if not rows:
                messages.error(request, "No invoice data available for this tenant/client.")
                return _billing_console_redirect(
                    billing_tenant,
                    billing_client,
                    link_tenant=billing_link_tenant,
                    link_client=billing_link_client,
                    link_status=billing_link_status,
                    link_expires=billing_link_expires,
                    link_sort=billing_link_sort,
                )

            invoice_row = rows[0]
            recipient = recipient_email or invoice_row.get("billing_contact_email") or ""
            access_token = _billing_access_token(invoice_tenant, invoice_client, window_days=30)
            invoice_url = (
                f"/contracts/billing/invoice/?tenant={invoice_tenant}&client={invoice_client}"
                f"&window_days=30&access_token={access_token}&format=pdf"
            )
            subject = f"Invoice {invoice_row.get('invoice_number')} · {invoice_tenant}/{invoice_client}"
            body = (
                f"Invoice number: {invoice_row.get('invoice_number')}\n"
                f"Total due: {invoice_row.get('total_due')}\n"
                f"Plan: {invoice_row.get('billing_plan')}\n"
                f"Invoice PDF: {invoice_url}\n"
            )
            notification = _queue_billing_notification(
                tenant_key=invoice_tenant,
                client_key=invoice_client,
                recipient=recipient,
                subject=subject,
                body=body,
                related_job=None,
                channel="invoice_email",
            )
            if not notification:
                messages.error(request, "Unable to queue invoice email notification.")
                return _billing_console_redirect(
                    billing_tenant,
                    billing_client,
                    link_tenant=billing_link_tenant,
                    link_client=billing_link_client,
                    link_status=billing_link_status,
                    link_expires=billing_link_expires,
                    link_sort=billing_link_sort,
                )

            notification = _deliver_billing_notification(notification)
            messages.success(request, f"Invoice email delivery status: {notification.status} ({invoice_tenant}/{invoice_client}).")
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "run_billing_operational_automation":
            result = _run_billing_operational_automation(
                tenant_key=billing_tenant,
                client_key=billing_client,
                created_by=request.user if getattr(request.user, "is_authenticated", False) else None,
            )
            rotations = result.get("rotations", {})
            retries = result.get("retries", {})
            health = result.get("health_notifications", {})
            messages.success(
                request,
                (
                    "Operational automation completed: "
                    f"rotated {rotations.get('rotated', 0)}/{rotations.get('candidates', 0)} links; "
                    f"retried {retries.get('retried', 0)} bounce notifications; "
                    f"billing health notifications {health.get('sent', 0)} (score {health.get('health_score', 0)})."
                ),
            )
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "queue_billing_operational_automation":
            job = _enqueue_billing_job(
                job_type="automation",
                tenant_key=billing_tenant or "default",
                client_key=billing_client or "all",
                payload={
                    "tenant": billing_tenant or "default",
                    "client": billing_client or "all",
                    "window_days": 30,
                    "schedule_hint": "hourly",
                },
                requested_by=request.user if getattr(request.user, "is_authenticated", False) else None,
            )
            if job:
                messages.success(
                    request,
                    f"Queued operational automation job #{job.id} for hourly execution pipeline.",
                )
            else:
                messages.error(request, "Unable to queue operational automation job.")
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "resolve_access_link_anomaly":
            try:
                from .models import ContractBillingAccessLink
            except Exception:
                messages.error(request, "Access link model unavailable.")
                return _billing_console_redirect(
                    billing_tenant,
                    billing_client,
                    link_tenant=billing_link_tenant,
                    link_client=billing_link_client,
                    link_status=billing_link_status,
                    link_expires=billing_link_expires,
                    link_sort=billing_link_sort,
                )

            resolve_mode = (request.POST.get("resolve_mode") or "revoke").strip().lower()
            link_id = request.POST.get("link_id")
            link = ContractBillingAccessLink.objects.filter(id=link_id).first()
            if not link:
                messages.error(request, "Anomaly target link not found.")
                return _billing_console_redirect(
                    billing_tenant,
                    billing_client,
                    link_tenant=billing_link_tenant,
                    link_client=billing_link_client,
                    link_status=billing_link_status,
                    link_expires=billing_link_expires,
                    link_sort=billing_link_sort,
                )

            if resolve_mode == "rotate":
                replacement = _issue_billing_access_link(
                    tenant_key=link.tenant_key,
                    client_key=link.client_key,
                    window_days=link.window_days,
                    created_by=request.user if getattr(request.user, "is_authenticated", False) else None,
                    label=link.label or "Customer billing portal",
                    recipient_email=link.recipient_email or "",
                    ttl_days=BILLING_ACCESS_DEFAULT_TTL_DAYS,
                    reuse_existing=False,
                )
                if replacement:
                    link.is_active = False
                    link.revoked_at = timezone.now()
                    link.save(update_fields=["is_active", "revoked_at", "updated_at"])
                    messages.success(request, f"Issued replacement link for {link.tenant_key} / {link.client_key}.")
                else:
                    messages.error(request, "Unable to issue replacement link.")
            else:
                if link.is_active:
                    link.is_active = False
                    link.revoked_at = timezone.now()
                    link.save(update_fields=["is_active", "revoked_at", "updated_at"])
                    messages.success(request, f"Resolved anomaly by revoking link {link.id}.")
                else:
                    messages.info(request, "Link was already inactive.")

            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "retry_invoice_bounce":
            result = _retry_billing_notification(
                notification_id=request.POST.get("notification_id"),
                recipient_override=(request.POST.get("recipient_email") or "").strip(),
            )
            if result.get("ok"):
                messages.success(request, "Retried invoice email diagnostic notification.")
            else:
                messages.error(request, result.get("error", "Unable to retry invoice email diagnostic notification."))
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

        if action == "retry_notification":
            result = _retry_billing_notification(
                notification_id=request.POST.get("notification_id"),
                recipient_override=(request.POST.get("recipient_email") or "").strip(),
            )
            if result.get("ok"):
                notification = result.get("notification", {})
                messages.success(request, f"Retried notification to {notification.get('recipient') or 'unassigned recipient' }.")
            else:
                messages.error(request, result.get("error", "Unable to retry notification."))
            return _billing_console_redirect(
                billing_tenant,
                billing_client,
                link_tenant=billing_link_tenant,
                link_client=billing_link_client,
                link_status=billing_link_status,
                link_expires=billing_link_expires,
                link_sort=billing_link_sort,
            )

    context = dict(admin.site.each_context(request))
    metrics = build_admin_metrics()
    context.update(metrics)

    app_panels = metrics.get("app_control_panels", [])
    executive_risks = sorted(
        app_panels,
        key=lambda panel: (
            len(panel.get("health", {}).get("attention_flags", [])),
            panel.get("health", {}).get("score", 0),
        ),
        reverse=True,
    )[:6]

    average_health_score = 0.0
    if app_panels:
        average_health_score = sum(
            panel.get("health", {}).get("score", 0) for panel in app_panels
        ) / len(app_panels)

    risk_flag_count = sum(
        len(panel.get("health", {}).get("attention_flags", [])) for panel in app_panels
    )
    semantic_data = metrics.get("semantic_cross_app_analytics", {})
    bottleneck = semantic_data.get("bottleneck", {})
    bottleneck_dropoff = bottleneck.get("dropoff_pct", 0)
    pressure_index = round(
        max(
            0,
            min(
                100,
                (100 - average_health_score) * 0.45
                + risk_flag_count * 4
                + bottleneck_dropoff * 0.35,
            ),
        ),
        1,
    )

    if pressure_index < 20:
        insight_label = "Stable"
    elif pressure_index < 40:
        insight_label = "Watch"
    elif pressure_index < 65:
        insight_label = "Elevated"
    else:
        insight_label = "Critical"

    operator_automation = _build_operator_automation(request, metrics)
    moderator_sentiment = _build_moderator_sentiment(request)

    def _day_delta(rows):
        if not rows:
            return {"current": 0, "previous": 0, "delta": 0, "trend": "flat"}
        if len(rows) == 1:
            current = rows[-1].get("count", 0)
            previous = 0
        else:
            current = rows[-1].get("count", 0)
            previous = rows[-2].get("count", 0)

        delta = current - previous
        if delta > 0:
            trend = "up"
        elif delta < 0:
            trend = "down"
        else:
            trend = "flat"
        return {
            "current": current,
            "previous": previous,
            "delta": delta,
            "trend": trend,
        }

    def _split_window_delta(rows):
        if not rows:
            return {
                "recent": 0,
                "previous": 0,
                "delta": 0,
                "delta_pct": 0.0,
                "trend": "flat",
            }

        midpoint = max(1, len(rows) // 2)
        previous_rows = rows[:midpoint]
        recent_rows = rows[midpoint:]
        previous_total = sum(row.get("count", 0) for row in previous_rows)
        recent_total = sum(row.get("count", 0) for row in recent_rows)
        delta = recent_total - previous_total

        if previous_total == 0:
            delta_pct = 100.0 if recent_total > 0 else 0.0
        else:
            delta_pct = round((delta / previous_total) * 100, 1)

        if delta > 0:
            trend = "up"
        elif delta < 0:
            trend = "down"
        else:
            trend = "flat"

        return {
            "recent": recent_total,
            "previous": previous_total,
            "delta": delta,
            "delta_pct": delta_pct,
            "trend": trend,
        }

    activity_delta = _split_window_delta(metrics.get("activity_rows_14d", []))
    user_delta = _split_window_delta(metrics.get("user_growth_rows", []))
    activity_day_delta = _day_delta(metrics.get("activity_rows_14d", []))
    user_day_delta = _day_delta(metrics.get("user_growth_rows", []))

    pressure_delta_value = 0.0
    pressure_trend = "flat"
    try:
        from .models import InsightsDailySnapshot

        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        yesterday_snapshot = InsightsDailySnapshot.objects.filter(snapshot_date=yesterday).first()
        if yesterday_snapshot:
            pressure_delta_value = round(pressure_index - yesterday_snapshot.pressure_index, 1)

        if pressure_delta_value > 0:
            pressure_trend = "up"
        elif pressure_delta_value < 0:
            pressure_trend = "down"

        InsightsDailySnapshot.objects.update_or_create(
            snapshot_date=today,
            defaults={
                "pressure_index": pressure_index,
                "average_health_score": round(average_health_score, 1),
                "risk_flag_count": risk_flag_count,
                "activity_count": activity_day_delta["current"],
                "user_growth_count": user_day_delta["current"],
            },
        )
    except Exception:
        pass

    trend_symbol = {
        "up": "↑",
        "down": "↓",
        "flat": "→",
    }

    pressure_drivers = [
        {
            "label": "Health drag",
            "value": round((100 - average_health_score) * 0.45, 1),
            "note": "Lower portfolio health raises pressure.",
        },
        {
            "label": "Flag load",
            "value": round(risk_flag_count * 4, 1),
            "note": "Open attention flags add operational drag.",
        },
        {
            "label": "Semantic bottleneck",
            "value": round(bottleneck_dropoff * 0.35, 1),
            "note": "Drop-off in semantic stages increases cross-flow risk.",
        },
    ]

    recommendations = []
    if activity_delta["trend"] == "down":
        recommendations.append("Admin activity is down versus the prior window; rebalance operator queue assignments.")
    if risk_flag_count >= 6:
        recommendations.append("Attention flags are elevated; run an executive triage pass on the risk queue.")
    if bottleneck_dropoff >= 45:
        recommendations.append("Semantic bottleneck is high; prioritize transition fixes in the weakest stage handoff.")
    if not recommendations:
        recommendations.append("No acute pressure accelerators detected; maintain current pacing and monitor momentum daily.")

    health_legend = metrics.get("health_legend", {})
    low_count = health_legend.get("red", 0)
    med_count = health_legend.get("yellow", 0)
    high_count = health_legend.get("green", 0)

    if low_count >= max(med_count, high_count):
        quadrant_priority = "Red"
    elif med_count >= high_count:
        quadrant_priority = "Yellow"
    else:
        quadrant_priority = "Green"

    if activity_delta["delta_pct"] >= 8 and user_delta["delta_pct"] >= 5:
        growth_direction = "Accelerating"
    elif activity_delta["delta_pct"] < 0 and user_delta["delta_pct"] < 0:
        growth_direction = "Cooling"
    else:
        growth_direction = "Mixed"

    recommended_action = recommendations[0] if recommendations else "Maintain current execution cadence."
    single_source_truth = {
        "state_label": insight_label,
        "pressure_index": pressure_index,
        "growth_direction": growth_direction,
        "quadrant_priority": quadrant_priority,
        "pipeline_bottleneck": bottleneck.get("label", "N/A"),
        "recommended_action": recommended_action,
    }

    top_fix = executive_risks[0] if executive_risks else None
    top_watch = max(app_panels, key=lambda panel: panel.get("current_7d", 0), default=None)
    top_grow = max(
        app_panels,
        key=lambda panel: (
            panel.get("health", {}).get("trend") == "up",
            panel.get("health", {}).get("score", 0),
        ),
        default=None,
    )
    top_stabilize = operator_automation.get("automation_queue", [{}])[0] if operator_automation.get("automation_queue") else None

    leadership_action_console = {
        "fix": {
            "label": top_fix.get("title", "None") if top_fix else "None",
            "detail": top_fix.get("health", {}).get("attention_flags", ["No critical fix item identified"])[0] if top_fix else "No critical fix item identified",
            "url": top_fix.get("route", "#") if top_fix else "#",
        },
        "watch": {
            "label": top_watch.get("title", "None") if top_watch else "None",
            "detail": "Highest recent activity concentration.",
            "url": top_watch.get("route", "#") if top_watch else "#",
        },
        "grow": {
            "label": top_grow.get("title", "None") if top_grow else "None",
            "detail": "Strongest app health and upward momentum.",
            "url": top_grow.get("route", "#") if top_grow else "#",
        },
        "stabilize": {
            "label": top_stabilize.get("label", "None") if top_stabilize else "None",
            "detail": top_stabilize.get("detail", "No stabilization action queued") if top_stabilize else "No stabilization action queued",
            "url": top_stabilize.get("url", "#") if top_stabilize else "#",
        },
        "quadrant": quadrant_priority,
        "pipeline_stage": bottleneck.get("label", "N/A"),
    }

    net_sentiment_value = 0
    try:
        net_sentiment_value = int(moderator_sentiment.get("sentiment_insights", [{}])[0].get("value", "0") or 0)
    except Exception:
        net_sentiment_value = 0

    health_drag_weight = round((100 - average_health_score) * 0.3, 1)
    flag_load_weight = round(min(20, risk_flag_count * 2.5), 1)
    bottleneck_weight = round(min(20, bottleneck_dropoff * 0.28), 1)
    user_growth_weight = round(min(15, max(0, -user_delta.get("delta_pct", 0)) * 0.4), 1)
    routing_delta = abs(operator_automation.get("auto_routing", {}).get("delta", 0))
    routing_volatility_weight = round(min(12, routing_delta * 2), 1)
    sentiment_drift_weight = round(min(12, max(0, -net_sentiment_value) * 0.6), 1)

    weighted_priority_score = round(
        min(
            100,
            health_drag_weight
            + flag_load_weight
            + bottleneck_weight
            + user_growth_weight
            + routing_volatility_weight
            + sentiment_drift_weight,
        ),
        1,
    )

    weighting_rows = [
        {"label": "Health drag", "value": health_drag_weight},
        {"label": "Flag load", "value": flag_load_weight},
        {"label": "Semantic bottleneck severity", "value": bottleneck_weight},
        {"label": "User growth acceleration drag", "value": user_growth_weight},
        {"label": "Routing score volatility", "value": routing_volatility_weight},
        {"label": "Sentiment drift", "value": sentiment_drift_weight},
    ]

    allocation_raw = {
        "Stabilize": 25 + health_drag_weight + flag_load_weight * 0.4,
        "Pipeline": 20 + bottleneck_weight,
        "Growth": 30 + max(0, activity_delta.get("delta_pct", 0)) * 0.2,
        "Community": 15 + sentiment_drift_weight,
    }
    allocation_total = sum(allocation_raw.values()) or 1
    resource_allocation = [
        {
            "label": label,
            "pct": round((value / allocation_total) * 100, 1),
        }
        for label, value in allocation_raw.items()
    ]

    scenario_baseline_growth = round((activity_delta.get("delta_pct", 0) + user_delta.get("delta_pct", 0)) / 2, 1)
    scenario_simulator = {
        "baseline": {
            "pressure": pressure_index,
            "growth": scenario_baseline_growth,
            "risk": insight_label,
        },
        "scenarios": [
            {
                "label": "Twist Doubles",
                "pressure": round(max(0, pressure_index - 4), 1),
                "growth": round(scenario_baseline_growth + 12, 1),
                "risk": "Watch",
                "action": "Scale operator routing capacity before backlog expands.",
            },
            {
                "label": "Seeds Drop",
                "pressure": round(min(100, pressure_index + 8), 1),
                "growth": round(scenario_baseline_growth - 6, 1),
                "risk": "Elevated",
                "action": "Prioritize seed conversion recovery and escalation handling.",
            },
            {
                "label": "Flow Bottlenecks",
                "pressure": round(min(100, pressure_index + 14), 1),
                "growth": round(scenario_baseline_growth - 9, 1),
                "risk": "Critical",
                "action": "Route blocked flows to recovery lanes and suppress new intake.",
            },
            {
                "label": "Career Spikes",
                "pressure": round(max(0, pressure_index - 2), 1),
                "growth": round(scenario_baseline_growth + 9, 1),
                "risk": "Watch",
                "action": "Reallocate growth resources to career pathways and onboarding.",
            },
            {
                "label": "Forums Sentiment Dips",
                "pressure": round(min(100, pressure_index + 6), 1),
                "growth": round(scenario_baseline_growth - 3, 1),
                "risk": "Elevated",
                "action": "Trigger moderator escalation workflow and community outreach.",
            },
        ],
    }

    horizon_planner = [
        {
            "horizon": "0-7 Days",
            "priority": leadership_action_console["fix"]["label"],
            "focus": "Fix",
            "plan": leadership_action_console["fix"]["detail"],
        },
        {
            "horizon": "8-30 Days",
            "priority": leadership_action_console["stabilize"]["label"],
            "focus": "Stabilize",
            "plan": leadership_action_console["stabilize"]["detail"],
        },
        {
            "horizon": "31-90 Days",
            "priority": leadership_action_console["grow"]["label"],
            "focus": "Grow",
            "plan": "Scale capacity around the strongest momentum app while protecting bottleneck continuity.",
        },
    ]

    narratives = {
        "daily": f"Daily brief: {insight_label} state with pressure {pressure_index}. Priority action is {leadership_action_console['fix']['label']}.",
        "weekly": f"Weekly strategic summary: growth is {growth_direction.lower()}, quadrant priority is {quadrant_priority}, and bottleneck remains at {bottleneck.get('label', 'N/A')}.",
        "monthly": f"Monthly outlook: weighted priority score is {weighted_priority_score}, with focus on stabilization and pipeline continuity.",
        "quadrant": f"Quadrant narrative: {quadrant_priority} quadrant needs immediate focus before scaling opportunities.",
        "pipeline": f"Pipeline narrative: bottleneck {bottleneck.get('label', 'N/A')} is driving {bottleneck_dropoff}% drop-off pressure.",
        "risk": f"Risk narrative: {risk_flag_count} open flags and pressure trend {trend_symbol[pressure_trend]} indicate {insight_label.lower()} conditions.",
        "community": f"Community narrative: net sentiment is {net_sentiment_value}, requiring {'proactive' if net_sentiment_value < 0 else 'steady'} moderation posture.",
    }

    insights_layer_v2 = {
        "single_source_truth": single_source_truth,
        "weighted_priority_score": weighted_priority_score,
        "weighting_rows": weighting_rows,
    }

    strategy_snapshot_history = []
    snapshot_trends = {
        "pressure": [],
        "priority": [],
        "growth": [],
    }
    quadrant_drift = {
        "counts": [],
        "transitions": [],
        "current": "N/A",
        "streak": 0,
    }
    pipeline_drift = {
        "counts": [],
        "transitions": [],
        "current": "N/A",
        "streak": 0,
    }
    narrative_evolution = []
    strategic_anomalies = []
    executive_retrospective = {
        "monthly": {
            "label": "Monthly",
            "snapshot_count": 0,
            "avg_pressure": 0,
            "avg_priority": 0,
            "top_quadrant": "N/A",
            "top_bottleneck": "N/A",
            "headline": "Not enough data yet.",
        },
        "quarterly": {
            "label": "Quarterly",
            "snapshot_count": 0,
            "avg_pressure": 0,
            "avg_priority": 0,
            "top_quadrant": "N/A",
            "top_bottleneck": "N/A",
            "headline": "Not enough data yet.",
        },
    }
    retrospective_export_links = {
        "monthly": "/admin/insights-retrospective-export/?period=monthly",
        "quarterly": "/admin/insights-retrospective-export/?period=quarterly",
        "monthly_json": "/admin/insights-retrospective-export/?period=monthly&format=json",
        "quarterly_json": "/admin/insights-retrospective-export/?period=quarterly&format=json",
        "monthly_json_v100": "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=1.0.0",
        "quarterly_json_v100": "/admin/insights-retrospective-export/?period=quarterly&format=json&schema_version=1.0.0",
        "monthly_json_v110": "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=1.1.0",
        "quarterly_json_v110": "/admin/insights-retrospective-export/?period=quarterly&format=json&schema_version=1.1.0",
        "schema": "/admin/insights-retrospective-export-schema/",
        "schema_diff": "/admin/insights-retrospective-export-schema-diff/?from=1.0.0&to=1.1.0",
        "selftest": "/admin/insights-retrospective-contract-selftest/",
        "negotiate": "/admin/insights-retrospective-negotiate/",
        "negotiate_stable": "/admin/insights-retrospective-negotiate/?schema_version=stable&capabilities=stable_only&strict_payload_shape=1",
        "negotiate_legacy": "/admin/insights-retrospective-negotiate/?client=legacy_csv_bridge&capabilities=legacy_only&strict_payload_shape=1",
        "negotiate_experimental": "/admin/insights-retrospective-negotiate/?schema_version=latest&capabilities=experimental_fields&strict_payload_shape=1",
        "negotiate_strict": "/admin/insights-retrospective-negotiate/?client=executive_dashboard_widgets&capabilities=roadmap_ref,stable_only&strict_negotiation=1&strict_payload_shape=1",
        "negotiate_migration": "/admin/insights-retrospective-negotiate/?client=migration_tooling_bundle_export&from_version=1.0.0&strict_negotiation=1&strict_payload_shape=1",
        "usage_analytics": "/admin/insights-contract-usage-analytics/",
        "usage_analytics_7d": "/admin/insights-contract-usage-analytics/?window_days=7",
        "usage_analytics_30d": "/admin/insights-contract-usage-analytics/?window_days=30",
        "billing_summary": "/admin/insights-contract-billing-summary/",
        "billing_summary_30d": "/admin/insights-contract-billing-summary/?window_days=30",
    }
    contract_onboarding = {
        "version_guide": [
            {
                "step": "Start stable first",
                "detail": "Use stable or active contracts unless your client explicitly needs legacy or experimental fields.",
            },
            {
                "step": "Declare capabilities",
                "detail": "Set capabilities such as roadmap_ref, legacy_only, or stable_only so negotiation can pick the safest compatible version.",
            },
            {
                "step": "Enable strict mode for production",
                "detail": "Use strict_negotiation=1 and strict_payload_shape=1 to avoid drift and prevent field leakage across versions.",
            },
            {
                "step": "Review upgrade path before switching",
                "detail": "Check schema diff and negotiate from your current version to preview required and optional changes.",
            },
        ],
        "capability_explainer": [
            {
                "capability": "stable_only",
                "effect": "Limits selection to stable/deprecated export-enabled versions and excludes experimental or sunset contracts.",
            },
            {
                "capability": "legacy_only",
                "effect": "Pins negotiation to v1.0.0 legacy-compatible payloads.",
            },
            {
                "capability": "roadmap_ref",
                "effect": "Requires v1.1.0+ so roadmap reference metadata is available.",
            },
            {
                "capability": "experimental_fields",
                "effect": "Allows negotiation into v2.0.0 experimental contracts when enabled.",
            },
        ],
        "quick_start": [
            {
                "label": "Open Version Negotiation Assistant",
                "url": retrospective_export_links["negotiate"],
            },
            {
                "label": "Run Stable Client Profile",
                "url": retrospective_export_links["negotiate_stable"],
            },
            {
                "label": "Run Legacy Client Profile",
                "url": retrospective_export_links["negotiate_legacy"],
            },
            {
                "label": "Run Strict Client Profile",
                "url": retrospective_export_links["negotiate_strict"],
            },
            {
                "label": "Run Migration Client Profile",
                "url": retrospective_export_links["negotiate_migration"],
            },
            {
                "label": "View Schema Metadata",
                "url": retrospective_export_links["schema"],
            },
            {
                "label": "View Schema Diff (1.0.0 -> 1.1.0)",
                "url": retrospective_export_links["schema_diff"],
            },
            {
                "label": "View Usage Analytics (7d)",
                "url": retrospective_export_links["usage_analytics_7d"],
            },
            {
                "label": "View Usage Analytics (30d)",
                "url": retrospective_export_links["usage_analytics_30d"],
            },
            {
                "label": "View Billing Summary (30d)",
                "url": retrospective_export_links["billing_summary_30d"],
            },
        ],
    }
    schema_versions = sorted(_schema_contract_catalog().keys(), key=_version_key)
    diff_viewer = {
        "versions": schema_versions,
        "default_from": "1.0.0" if "1.0.0" in schema_versions else (schema_versions[0] if schema_versions else CURRENT_SCHEMA_VERSION),
        "default_to": "1.1.0" if "1.1.0" in schema_versions else (schema_versions[-1] if schema_versions else CURRENT_SCHEMA_VERSION),
    }
    diff_viewer["initial_diff"] = _schema_diff_payload(
        diff_viewer["default_from"],
        diff_viewer["default_to"],
        _schema_contract_catalog(),
    ) or {}
    billing_filter_tenant = (request.GET.get("billing_tenant") or "").strip()
    billing_filter_client = (request.GET.get("billing_client") or "").strip()
    billing_link_filter_tenant = (request.GET.get("billing_link_tenant") or "").strip()
    billing_link_filter_client = (request.GET.get("billing_link_client") or "").strip()
    billing_link_status = (request.GET.get("billing_link_status") or "all").strip().lower()
    billing_link_expires = (request.GET.get("billing_link_expires") or "all").strip().lower()
    billing_link_sort = (request.GET.get("billing_link_sort") or "newest").strip().lower()

    link_filter_tenant = billing_link_filter_tenant or billing_filter_tenant
    link_filter_client = billing_link_filter_client or billing_filter_client
    access_link_export_base = urlencode(
        {
            "tenant": link_filter_tenant,
            "client": link_filter_client,
            "window_days": 30,
            "status": billing_link_status,
            "expires": billing_link_expires,
            "sort": billing_link_sort,
        }
    )
    billing_summary = _contract_billing_summary_payload(
        window_days=30,
        tenant_key=billing_filter_tenant,
        client_key=billing_filter_client,
    )
    usage_analytics = _contract_usage_analytics_payload(window_days=30)
    billing_rows = billing_summary.get("summary", [])
    enforcement_priority = [row for row in billing_rows if row.get("enforcement_state") in {"warning", "exceeded"}]
    if not enforcement_priority:
        enforcement_priority = billing_rows[:5]
    access_links_history_rows = _billing_access_links_payload(
        tenant_key=link_filter_tenant,
        client_key=link_filter_client,
        window_days=30,
        limit=30,
        status_filter=billing_link_status,
        expires_filter=billing_link_expires,
        sort_by=billing_link_sort,
    )
    access_link_drilldowns = _billing_access_link_drilldowns_payload(access_links_history_rows)
    access_link_timeline = _billing_access_link_lifecycle_timeline_payload(access_links_history_rows, limit=24)
    bulk_issue_presets = _bulk_issue_presets_payload(billing_rows, limit=10)
    billing_micro_trends = _billing_micro_trends_payload(
        tenant_key=link_filter_tenant or billing_filter_tenant,
        client_key=link_filter_client or billing_filter_client,
        days=7,
    )
    access_link_analytics = _billing_access_link_analytics_payload(
        tenant_key=link_filter_tenant,
        client_key=link_filter_client,
        window_days=30,
        status_filter=billing_link_status,
        expires_filter=billing_link_expires,
    )
    access_link_anomalies = _billing_access_link_anomalies_payload(access_links_history_rows)
    access_link_anomaly_groups = _billing_anomaly_grouping_payload(access_link_anomalies)
    access_link_risk = _billing_access_link_risk_payload(
        access_links_history_rows,
        access_link_anomalies,
        access_link_analytics,
    )
    access_link_risk_trend = _billing_access_link_risk_trend_payload(
        tenant_key=link_filter_tenant or billing_filter_tenant,
        client_key=link_filter_client or billing_filter_client,
        days=30,
    )
    invoice_email_notifications = _customer_billing_notifications_payload(
        tenant_key=billing_filter_tenant,
        client_key=billing_filter_client,
        limit=10,
        channel="invoice_email",
    )
    invoice_email_diagnostics = _billing_invoice_email_diagnostics_payload(invoice_email_notifications)
    invoice_deliverability_heatmap = _billing_deliverability_heatmap_payload(invoice_email_notifications, days=7)
    anomaly_resolution_history = _billing_anomaly_resolution_history_payload(
        tenant_key=link_filter_tenant or billing_filter_tenant,
        client_key=link_filter_client or billing_filter_client,
        limit=18,
    )
    link_rotation_analytics = _billing_link_rotation_analytics_payload(
        tenant_key=link_filter_tenant or billing_filter_tenant,
        client_key=link_filter_client or billing_filter_client,
        days=30,
    )
    billing_health_score = _billing_health_score_payload(
        billing_rows,
        access_link_analytics,
        access_link_anomalies,
        invoice_email_diagnostics,
        access_link_risk,
    )
    billing_health_explainer = _billing_health_explainer_payload(
        billing_health_score,
        access_link_anomalies,
        invoice_email_diagnostics,
        access_link_risk,
    )
    billing_dashboard = {
        "summary": billing_summary,
        "usage": usage_analytics,
        "top_rows": billing_rows[:6],
        "enforcement_rows": enforcement_priority[:6],
        "access_links": _billing_access_links_payload(
            tenant_key=billing_filter_tenant,
            client_key=billing_filter_client,
            window_days=30,
            limit=6,
        ),
        "access_links_history": access_links_history_rows,
        "access_link_analytics": access_link_analytics,
        "access_link_risk": access_link_risk,
        "access_link_risk_trend": access_link_risk_trend,
        "access_link_anomalies": access_link_anomalies,
        "access_link_anomaly_groups": access_link_anomaly_groups,
        "anomaly_resolution_history": anomaly_resolution_history,
        "link_rotation_analytics": link_rotation_analytics,
        "access_link_drilldowns": access_link_drilldowns,
        "access_link_timeline": access_link_timeline,
        "bulk_issue_presets": bulk_issue_presets,
        "micro_trends": billing_micro_trends,
        "notifications": _customer_billing_notifications_payload(
            tenant_key=billing_filter_tenant,
            client_key=billing_filter_client,
            limit=6,
        ),
        "invoice_email_notifications": invoice_email_notifications,
        "invoice_email_diagnostics": invoice_email_diagnostics,
        "invoice_deliverability_heatmap": invoice_deliverability_heatmap,
        "health_score": billing_health_score,
        "health_explainer": billing_health_explainer,
        "headline": {
            "billable_units": usage_analytics.get("billable_units_total", 0),
            "billable_amount": usage_analytics.get("billable_amount_total", "0.0000"),
            "total_events": usage_analytics.get("total_events", 0),
        },
        "filter_state": {
            "tenant": billing_filter_tenant,
            "client": billing_filter_client,
        },
        "access_link_filter_state": {
            "tenant": billing_link_filter_tenant,
            "client": billing_link_filter_client,
            "status": billing_link_status,
            "expires": billing_link_expires,
            "sort": billing_link_sort,
            "resolved_tenant": link_filter_tenant,
            "resolved_client": link_filter_client,
        },
        "export_links": {
            "json": f"/admin/insights-contract-billing-summary/?window_days=30&tenant={billing_filter_tenant}&client={billing_filter_client}&format=json",
            "csv": f"/admin/insights-contract-billing-summary/?window_days=30&tenant={billing_filter_tenant}&client={billing_filter_client}&format=csv",
            "txt": f"/admin/insights-contract-billing-summary/?window_days=30&tenant={billing_filter_tenant}&client={billing_filter_client}&format=txt",
        },
        "access_link_export_links": {
            "json": f"/admin/insights-contract-billing-access-links-audit/?{access_link_export_base}&format=json",
            "csv": f"/admin/insights-contract-billing-access-links-audit/?{access_link_export_base}&format=csv",
        },
    }
    try:
        from .models import InsightsNarrativeSnapshot, InsightsDailySnapshot

        today = timezone.now().date()
        InsightsNarrativeSnapshot.objects.update_or_create(
            snapshot_date=today,
            defaults={
                "state_label": single_source_truth.get("state_label", "Stable"),
                "pressure_index": single_source_truth.get("pressure_index", 0.0),
                "weighted_priority_score": weighted_priority_score,
                "growth_direction": single_source_truth.get("growth_direction", "Mixed"),
                "quadrant_priority": single_source_truth.get("quadrant_priority", "Green"),
                "pipeline_bottleneck": single_source_truth.get("pipeline_bottleneck", "N/A"),
                "recommended_action": single_source_truth.get("recommended_action", ""),
                "daily_brief": narratives.get("daily", ""),
                "weekly_summary": narratives.get("weekly", ""),
                "monthly_outlook": narratives.get("monthly", ""),
            },
        )
        strategy_snapshot_history = list(InsightsNarrativeSnapshot.objects.order_by("-snapshot_date")[:7])

        trend_snapshots_desc = list(InsightsNarrativeSnapshot.objects.order_by("-snapshot_date")[:30])
        trend_snapshots = list(reversed(trend_snapshots_desc))
        trend_dates = [row.snapshot_date for row in trend_snapshots]
        daily_rows = {
            row.snapshot_date: row
            for row in InsightsDailySnapshot.objects.filter(snapshot_date__in=trend_dates)
        }

        max_pressure = max((row.pressure_index for row in trend_snapshots), default=1) or 1
        max_priority = max((row.weighted_priority_score for row in trend_snapshots), default=1) or 1
        max_growth = max((daily_rows.get(row.snapshot_date).user_growth_count if daily_rows.get(row.snapshot_date) else 0 for row in trend_snapshots), default=1) or 1

        pressure_series = []
        priority_series = []
        growth_series = []
        for row in trend_snapshots:
            growth_value = daily_rows.get(row.snapshot_date).user_growth_count if daily_rows.get(row.snapshot_date) else 0
            label = row.snapshot_date.strftime("%m-%d")
            pressure_series.append(
                {
                    "label": label,
                    "value": round(row.pressure_index, 1),
                    "pct": int((row.pressure_index / max_pressure) * 100) if max_pressure else 0,
                }
            )
            priority_series.append(
                {
                    "label": label,
                    "value": round(row.weighted_priority_score, 1),
                    "pct": int((row.weighted_priority_score / max_priority) * 100) if max_priority else 0,
                }
            )
            growth_series.append(
                {
                    "label": label,
                    "value": growth_value,
                    "pct": int((growth_value / max_growth) * 100) if max_growth else 0,
                }
            )
        snapshot_trends = {
            "pressure": pressure_series,
            "priority": priority_series,
            "growth": growth_series,
        }

        quadrant_counter = Counter(row.quadrant_priority for row in trend_snapshots if row.quadrant_priority)
        quadrant_counts = [
            {"label": label, "count": count}
            for label, count in quadrant_counter.most_common()
        ]
        quadrant_transitions = []
        for idx in range(1, len(trend_snapshots)):
            prev_q = trend_snapshots[idx - 1].quadrant_priority
            curr_q = trend_snapshots[idx].quadrant_priority
            if prev_q != curr_q:
                quadrant_transitions.append(
                    {
                        "date": trend_snapshots[idx].snapshot_date.strftime("%Y-%m-%d"),
                        "from": prev_q,
                        "to": curr_q,
                    }
                )
        latest_quadrant = trend_snapshots_desc[0].quadrant_priority if trend_snapshots_desc else "N/A"
        quadrant_streak = 0
        for row in trend_snapshots_desc:
            if row.quadrant_priority == latest_quadrant:
                quadrant_streak += 1
            else:
                break
        quadrant_drift = {
            "counts": quadrant_counts,
            "transitions": quadrant_transitions[-6:],
            "current": latest_quadrant,
            "streak": quadrant_streak,
        }

        pipeline_counter = Counter(row.pipeline_bottleneck for row in trend_snapshots if row.pipeline_bottleneck)
        pipeline_counts = [
            {"label": label, "count": count}
            for label, count in pipeline_counter.most_common()
        ]
        pipeline_transitions = []
        for idx in range(1, len(trend_snapshots)):
            prev_b = trend_snapshots[idx - 1].pipeline_bottleneck
            curr_b = trend_snapshots[idx].pipeline_bottleneck
            if prev_b != curr_b:
                pipeline_transitions.append(
                    {
                        "date": trend_snapshots[idx].snapshot_date.strftime("%Y-%m-%d"),
                        "from": prev_b,
                        "to": curr_b,
                    }
                )
        latest_bottleneck = trend_snapshots_desc[0].pipeline_bottleneck if trend_snapshots_desc else "N/A"
        bottleneck_streak = 0
        for row in trend_snapshots_desc:
            if row.pipeline_bottleneck == latest_bottleneck:
                bottleneck_streak += 1
            else:
                break
        pipeline_drift = {
            "counts": pipeline_counts,
            "transitions": pipeline_transitions[-6:],
            "current": latest_bottleneck,
            "streak": bottleneck_streak,
        }

        narrative_evolution = [
            {
                "date": row.snapshot_date.strftime("%Y-%m-%d"),
                "daily": row.daily_brief,
                "weekly": row.weekly_summary,
                "monthly": row.monthly_outlook,
            }
            for row in trend_snapshots_desc[:10]
        ]

        if len(trend_snapshots_desc) >= 2:
            latest = trend_snapshots_desc[0]
            previous = trend_snapshots_desc[1]
            pressure_jump = round(latest.pressure_index - previous.pressure_index, 1)
            priority_jump = round(latest.weighted_priority_score - previous.weighted_priority_score, 1)
            latest_growth = daily_rows.get(latest.snapshot_date).user_growth_count if daily_rows.get(latest.snapshot_date) else 0
            previous_growth = daily_rows.get(previous.snapshot_date).user_growth_count if daily_rows.get(previous.snapshot_date) else 0
            growth_jump = latest_growth - previous_growth

            if abs(pressure_jump) >= 8:
                strategic_anomalies.append(
                    {
                        "label": "Pressure anomaly",
                        "detail": f"Pressure changed by {pressure_jump} points day-over-day.",
                    }
                )
            if abs(priority_jump) >= 10:
                strategic_anomalies.append(
                    {
                        "label": "Priority-score anomaly",
                        "detail": f"Weighted priority changed by {priority_jump} points.",
                    }
                )
            if abs(growth_jump) >= 4:
                strategic_anomalies.append(
                    {
                        "label": "Growth anomaly",
                        "detail": f"User growth shifted by {growth_jump} in the latest snapshot window.",
                    }
                )

            sentiment_value = net_sentiment_value
            if sentiment_value <= -8 or sentiment_value >= 12:
                strategic_anomalies.append(
                    {
                        "label": "Sentiment anomaly",
                        "detail": f"Net sentiment reached {sentiment_value}, outside normal moderation band.",
                    }
                )

            routing_shift = abs(operator_automation.get("auto_routing", {}).get("delta", 0))
            if routing_shift >= 4:
                strategic_anomalies.append(
                    {
                        "label": "Routing anomaly",
                        "detail": f"Auto-routing shifted by {routing_shift} activity points.",
                    }
                )

        if not strategic_anomalies:
            strategic_anomalies.append(
                {
                    "label": "No major anomalies",
                    "detail": "Pressure, growth, sentiment, and routing remain inside expected bounds.",
                }
            )

        def _retrospective_payload(label, rows):
            if not rows:
                return {
                    "label": label,
                    "snapshot_count": 0,
                    "avg_pressure": 0,
                    "avg_priority": 0,
                    "top_quadrant": "N/A",
                    "top_bottleneck": "N/A",
                    "headline": "Not enough data yet.",
                }
            avg_pressure = round(sum(row.pressure_index for row in rows) / len(rows), 1)
            avg_priority = round(sum(row.weighted_priority_score for row in rows) / len(rows), 1)
            top_quadrant = Counter(row.quadrant_priority for row in rows if row.quadrant_priority).most_common(1)
            top_bottleneck = Counter(row.pipeline_bottleneck for row in rows if row.pipeline_bottleneck).most_common(1)
            top_quadrant_value = top_quadrant[0][0] if top_quadrant else "N/A"
            top_bottleneck_value = top_bottleneck[0][0] if top_bottleneck else "N/A"
            headline = (
                f"{label} retrospective: avg pressure {avg_pressure}, avg priority {avg_priority}, "
                f"dominant quadrant {top_quadrant_value}, recurring bottleneck {top_bottleneck_value}."
            )
            return {
                "label": label,
                "snapshot_count": len(rows),
                "avg_pressure": avg_pressure,
                "avg_priority": avg_priority,
                "top_quadrant": top_quadrant_value,
                "top_bottleneck": top_bottleneck_value,
                "headline": headline,
            }

        month_start = today.replace(day=1)
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        quarter_start = today.replace(month=quarter_month, day=1)

        monthly_rows = [row for row in trend_snapshots_desc if row.snapshot_date >= month_start]
        quarterly_rows = [row for row in trend_snapshots_desc if row.snapshot_date >= quarter_start]
        executive_retrospective = {
            "monthly": _retrospective_payload("Monthly", monthly_rows),
            "quarterly": _retrospective_payload("Quarterly", quarterly_rows),
        }
    except Exception:
        strategy_snapshot_history = []

    context.update(
        {
            "basetrue_insights": {
                "label": insight_label,
                "pressure_index": pressure_index,
                "average_health_score": round(average_health_score, 1),
                "risk_flag_count": risk_flag_count,
                "bottleneck_label": bottleneck.get("label", "N/A"),
                "bottleneck_dropoff": bottleneck_dropoff,
            },
            "insight_risk_queue": executive_risks,
            "insight_operator": operator_automation,
            "insight_moderator": moderator_sentiment,
            "insight_semantic": semantic_data,
            "insight_change_explainer": {
                "activity": activity_delta,
                "users": user_delta,
                "activity_rows": metrics.get("activity_rows_14d", []),
                "user_rows": metrics.get("user_growth_rows", []),
                "drivers": pressure_drivers,
                "signals": metrics.get("cross_dashboard_insights", {}).get("signals", []),
                "recommendations": recommendations,
            },
            "insight_change_badges": [
                {
                    "label": "Pressure",
                    "value": pressure_index,
                    "delta": pressure_delta_value,
                    "trend": pressure_trend,
                    "symbol": trend_symbol[pressure_trend],
                    "note": "today vs yesterday",
                },
                {
                    "label": "Activity",
                    "value": activity_day_delta["current"],
                    "delta": activity_day_delta["delta"],
                    "trend": activity_day_delta["trend"],
                    "symbol": trend_symbol[activity_day_delta["trend"]],
                    "note": "today vs yesterday",
                },
                {
                    "label": "User Growth",
                    "value": user_day_delta["current"],
                    "delta": user_day_delta["delta"],
                    "trend": user_day_delta["trend"],
                    "symbol": trend_symbol[user_day_delta["trend"]],
                    "note": "today vs yesterday",
                },
            ],
            "leadership_action_console": leadership_action_console,
            "insights_layer_v2": insights_layer_v2,
            "strategic_narratives": narratives,
            "resource_allocation_engine": resource_allocation,
            "scenario_simulator": scenario_simulator,
            "horizon_planner": horizon_planner,
            "strategy_snapshot_history": strategy_snapshot_history,
            "snapshot_trends": snapshot_trends,
            "quadrant_drift": quadrant_drift,
            "pipeline_drift": pipeline_drift,
            "narrative_evolution": narrative_evolution,
            "strategic_anomalies": strategic_anomalies,
            "executive_retrospective": executive_retrospective,
            "retrospective_export_links": retrospective_export_links,
            "contract_onboarding": contract_onboarding,
            "contract_diff_viewer": diff_viewer,
            "contract_billing_dashboard": billing_dashboard,
        }
    )
    return TemplateResponse(request, "admin/basetrue_insights.html", context)


def _insights_retrospective_export_view(request):
    tenant_key = (request.GET.get("tenant") or "default").strip() or "default"
    period = (request.GET.get("period") or "monthly").strip().lower()
    if period not in {"monthly", "quarterly"}:
        period = "monthly"
    output_format = (request.GET.get("format") or "txt").strip().lower()
    if output_format not in {"txt", "json"}:
        output_format = "txt"
    requested_schema_version = (request.GET.get("schema_version") or "").strip()
    requested_default_schema_version = (request.GET.get("default_schema_version") or "").strip()
    requested_schema_versions_raw = _parse_schema_versions(request.GET.get("schema_versions"))
    client_name = (request.GET.get("client") or "").strip()
    capability_tokens = _parse_capability_tokens(request.GET.get("capabilities"))
    strict_negotiation = _parse_bool(request.GET.get("strict_negotiation"))
    strict_payload_shape = _parse_bool(request.GET.get("strict_payload_shape"))

    merged = _merge_profile_defaults(
        request,
        tenant_key,
        client_name,
        requested_default_schema_version,
        capability_tokens,
        strict_negotiation,
        strict_payload_shape,
    )
    requested_default_schema_version = merged["default_schema_version"]
    capability_tokens = merged["capability_tokens"]
    strict_negotiation = merged["strict_negotiation"]
    strict_payload_shape = merged["strict_payload_shape"]

    today = timezone.now().date()
    if period == "monthly":
        start_date = today.replace(day=1)
        label = "Monthly"
    else:
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_month, day=1)
        label = "Quarterly"

    try:
        from .models import InsightsNarrativeSnapshot

        rows = list(
            InsightsNarrativeSnapshot.objects.filter(snapshot_date__gte=start_date).order_by("snapshot_date")
        )
    except Exception:
        rows = []

    catalog = _schema_contract_catalog()

    resolved_default = _resolve_default_schema_version(catalog, requested_default_schema_version)
    if requested_default_schema_version and not resolved_default:
        _record_contract_usage(
            endpoint="export",
            tenant_key=tenant_key,
            client_key=client_name,
            requested_schema_version=requested_schema_version,
            strict_negotiation=strict_negotiation,
            strict_payload_shape=strict_payload_shape,
            period=period,
            output_format=output_format,
            status_code=400,
            negotiation_source="validation-error",
        )
        return JsonResponse(
            {
                "error": "Unsupported default_schema_version",
                "requested": requested_default_schema_version,
                "current": CURRENT_SCHEMA_VERSION,
                "available_versions": sorted(catalog.keys()),
            },
            status=400,
        )

    if requested_schema_versions_raw == ["migration_bundle"]:
        requested_schema_versions_raw = ["1.0.0", "1.1.0"]

    requested_schema_versions = [
        _resolve_schema_version_alias(version, catalog) for version in requested_schema_versions_raw
    ]

    version_selection = _select_schema_version(
        catalog,
        requested_schema_version=requested_schema_version,
        preferred_default=resolved_default or "",
        client=client_name,
        capabilities=capability_tokens,
        strict=strict_negotiation,
    )
    if not version_selection["ok"]:
        _record_contract_usage(
            endpoint="export",
            tenant_key=tenant_key,
            client_key=client_name,
            requested_schema_version=requested_schema_version,
            strict_negotiation=strict_negotiation,
            strict_payload_shape=strict_payload_shape,
            period=period,
            output_format=output_format,
            status_code=400,
            negotiation_source="selection-error",
        )
        return JsonResponse(
            {
                "error": version_selection["error"],
                "requested": version_selection.get("requested", requested_schema_version),
                "current": CURRENT_SCHEMA_VERSION,
                "available_versions": version_selection.get("available_versions", sorted(catalog.keys())),
            },
            status=400,
        )
    target_schema_version = version_selection["selected_version"]
    schema_negotiation = version_selection["negotiation"]

    if requested_schema_versions:
        if output_format != "json":
            _record_contract_usage(
                endpoint="export",
                tenant_key=tenant_key,
                client_key=client_name,
                requested_schema_version=requested_schema_version,
                selected_schema_version=target_schema_version,
                negotiation_source=version_selection.get("source", ""),
                strict_negotiation=strict_negotiation,
                strict_payload_shape=strict_payload_shape,
                period=period,
                output_format=output_format,
                status_code=400,
            )
            return JsonResponse(
                {
                    "error": "schema_versions is supported only with format=json",
                    "requested_format": output_format,
                },
                status=400,
            )

        unknown_versions = [version for version in requested_schema_versions if version not in catalog]
        if unknown_versions:
            _record_contract_usage(
                endpoint="export",
                tenant_key=tenant_key,
                client_key=client_name,
                requested_schema_version=requested_schema_version,
                selected_schema_version=target_schema_version,
                negotiation_source=version_selection.get("source", ""),
                strict_negotiation=strict_negotiation,
                strict_payload_shape=strict_payload_shape,
                period=period,
                output_format=output_format,
                status_code=400,
            )
            return JsonResponse(
                {
                    "error": "Unsupported schema_version(s)",
                    "requested": unknown_versions,
                    "available_versions": sorted(catalog.keys()),
                },
                status=400,
            )

        lifecycle = {
            version: {
                "state": catalog.get(version, {}).get("lifecycle_state", "unknown"),
                "export_enabled": bool(catalog.get(version, {}).get("export_enabled", True)),
            }
            for version in requested_schema_versions
        }

        if any(not info["export_enabled"] for info in lifecycle.values()):
            blocked = [version for version, info in lifecycle.items() if not info["export_enabled"]]
            _record_contract_usage(
                endpoint="export",
                tenant_key=tenant_key,
                client_key=client_name,
                requested_schema_version=requested_schema_version,
                selected_schema_version=target_schema_version,
                negotiation_source=version_selection.get("source", ""),
                strict_negotiation=strict_negotiation,
                strict_payload_shape=strict_payload_shape,
                period=period,
                output_format=output_format,
                status_code=400,
            )
            return JsonResponse(
                {
                    "error": "Requested schema_version is not export-enabled",
                    "requested": blocked,
                },
                status=400,
            )

        payload_versions = {}
        for schema_version in requested_schema_versions:
            contract = dict(catalog.get(schema_version, {}))
            contract["version"] = schema_version
            required_fields = contract.get("required_fields", [])
            optional_fields = contract.get("optional_fields", [])
            schema_hash = _schema_hash_for(contract)

            if rows:
                avg_pressure = round(sum(row.pressure_index for row in rows) / len(rows), 1)
                avg_priority = round(sum(row.weighted_priority_score for row in rows) / len(rows), 1)
                snapshot_rows = [
                    {
                        "snapshot_date": row.snapshot_date.isoformat(),
                        "state_label": row.state_label,
                        "pressure_index": row.pressure_index,
                        "weighted_priority_score": row.weighted_priority_score,
                        "growth_direction": row.growth_direction,
                        "quadrant_priority": row.quadrant_priority,
                        "pipeline_bottleneck": row.pipeline_bottleneck,
                        "recommended_action": row.recommended_action,
                        "daily_brief": row.daily_brief,
                        "weekly_summary": row.weekly_summary,
                        "monthly_outlook": row.monthly_outlook,
                    }
                    for row in rows
                ]
                version_payload = {
                    "schema_version": schema_version,
                    "export_format": "basetrue-retrospective-json",
                    "schema_hash": schema_hash,
                    "schema_notes": {
                        "compatibility": "Backward-compatible additive changes only within major version 1.",
                        "required_fields": required_fields,
                        "optional_fields": optional_fields,
                        "stability_window": _schema_stability_window(today),
                        "deprecation_policy": _schema_deprecation_policy(),
                        "evolution_roadmap": _schema_evolution_roadmap(),
                        "changelog": [
                            {
                                "version": schema_version,
                                "date": today.isoformat(),
                                "notes": "Versioned retrospective JSON export contract.",
                            }
                        ],
                    },
                    "title": f"BaseTrue Insights {label} Retrospective",
                    "generated": today.isoformat(),
                    "window_start": start_date.isoformat(),
                    "period": period,
                    "snapshot_count": len(rows),
                    "avg_pressure": avg_pressure,
                    "avg_priority_score": avg_priority,
                    "latest": snapshot_rows[-1],
                    "snapshots": snapshot_rows,
                }
            else:
                version_payload = {
                    "schema_version": schema_version,
                    "export_format": "basetrue-retrospective-json",
                    "schema_hash": schema_hash,
                    "schema_notes": {
                        "compatibility": "Backward-compatible additive changes only within major version 1.",
                        "required_fields": required_fields,
                        "optional_fields": optional_fields,
                        "stability_window": _schema_stability_window(today),
                        "deprecation_policy": _schema_deprecation_policy(),
                        "evolution_roadmap": _schema_evolution_roadmap(),
                        "changelog": [
                            {
                                "version": schema_version,
                                "date": today.isoformat(),
                                "notes": "Versioned retrospective JSON export contract.",
                            }
                        ],
                    },
                    "title": f"BaseTrue Insights {label} Retrospective",
                    "generated": today.isoformat(),
                    "window_start": start_date.isoformat(),
                    "period": period,
                    "snapshot_count": 0,
                    "avg_pressure": 0,
                    "avg_priority_score": 0,
                    "latest": None,
                    "snapshots": [],
                    "note": "No narrative snapshots available for this period.",
                }

            if _version_key(schema_version) >= _version_key("1.1.0"):
                version_payload["schema_roadmap_ref"] = f"roadmap:v{schema_version}"
            if _version_key(schema_version) >= _version_key("2.0.0"):
                version_payload["schema_negotiation_hints"] = _schema_negotiation_hint(
                    catalog,
                    client=client_name,
                    capabilities=capability_tokens,
                    preferred_default=resolved_default or "",
                )
                version_payload["contract_lifecycle"] = {
                    "state": catalog.get(schema_version, {}).get("lifecycle_state", "unknown"),
                }

            version_payload = _shape_payload_for_contract(
                version_payload,
                contract,
                strict_payload_shape=strict_payload_shape,
            )

            payload_versions[schema_version] = version_payload

        bundle = {
            "export_format": "basetrue-retrospective-json-multi",
            "generated": today.isoformat(),
            "period": period,
            "window_start": start_date.isoformat(),
            "requested_versions": requested_schema_versions,
            "default_schema_version": resolved_default or CURRENT_SCHEMA_VERSION,
            "strict_negotiation": strict_negotiation,
            "strict_payload_shape": strict_payload_shape,
            "versions": payload_versions,
            "lifecycle": lifecycle,
            "schema_negotiation": schema_negotiation,
            "schema_selection_source": version_selection["source"],
        }

        response = JsonResponse(bundle)
        response["Content-Disposition"] = f'attachment; filename="basetrue-{period}-retrospective-multi.json"'
        _record_contract_usage(
            endpoint="export",
            tenant_key=tenant_key,
            client_key=client_name,
            requested_schema_version=requested_schema_version,
            selected_schema_version=target_schema_version,
            negotiation_source=version_selection.get("source", ""),
            strict_negotiation=strict_negotiation,
            strict_payload_shape=strict_payload_shape,
            period=period,
            output_format=output_format,
            status_code=200,
        )
        return response

    contract = dict(catalog.get(target_schema_version, {}))
    contract["version"] = target_schema_version
    lifecycle_state = contract.get("lifecycle_state", "unknown")
    if not contract.get("export_enabled", True):
        _record_contract_usage(
            endpoint="export",
            tenant_key=tenant_key,
            client_key=client_name,
            requested_schema_version=requested_schema_version,
            selected_schema_version=target_schema_version,
            negotiation_source=version_selection.get("source", ""),
            strict_negotiation=strict_negotiation,
            strict_payload_shape=strict_payload_shape,
            period=period,
            output_format=output_format,
            status_code=400,
        )
        return JsonResponse(
            {
                "error": "Requested schema_version is not export-enabled",
                "requested": target_schema_version,
                "lifecycle_state": lifecycle_state,
            },
            status=400,
        )

    required_fields = contract.get("required_fields", [])
    optional_fields = contract.get("optional_fields", [])
    schema_hash = _schema_hash_for(contract)
    stability = _schema_stability_window(today)
    deprecation_policy = _schema_deprecation_policy()
    roadmap = _schema_evolution_roadmap()

    if rows:
        avg_pressure = round(sum(row.pressure_index for row in rows) / len(rows), 1)
        avg_priority = round(sum(row.weighted_priority_score for row in rows) / len(rows), 1)
        latest = rows[-1]
        snapshot_rows = [
            {
                "snapshot_date": row.snapshot_date.isoformat(),
                "state_label": row.state_label,
                "pressure_index": row.pressure_index,
                "weighted_priority_score": row.weighted_priority_score,
                "growth_direction": row.growth_direction,
                "quadrant_priority": row.quadrant_priority,
                "pipeline_bottleneck": row.pipeline_bottleneck,
                "recommended_action": row.recommended_action,
                "daily_brief": row.daily_brief,
                "weekly_summary": row.weekly_summary,
                "monthly_outlook": row.monthly_outlook,
            }
            for row in rows
        ]
        payload = {
            "schema_version": target_schema_version,
            "default_schema_version": resolved_default or CURRENT_SCHEMA_VERSION,
            "strict_negotiation": strict_negotiation,
            "strict_payload_shape": strict_payload_shape,
            "export_format": "basetrue-retrospective-json",
            "schema_hash": schema_hash,
            "schema_notes": {
                "compatibility": "Backward-compatible additive changes only within major version 1.",
                "required_fields": required_fields,
                "optional_fields": optional_fields,
                "lifecycle_state": lifecycle_state,
                "stability_window": stability,
                "deprecation_policy": deprecation_policy,
                "evolution_roadmap": roadmap,
                "changelog": [
                    {
                        "version": target_schema_version,
                        "date": today.isoformat(),
                        "notes": "Versioned retrospective JSON export contract.",
                    }
                ],
            },
            "title": f"BaseTrue Insights {label} Retrospective",
            "generated": today.isoformat(),
            "window_start": start_date.isoformat(),
            "period": period,
            "snapshot_count": len(rows),
            "avg_pressure": avg_pressure,
            "avg_priority_score": avg_priority,
            "latest": snapshot_rows[-1],
            "snapshots": snapshot_rows,
            "schema_negotiation": schema_negotiation,
            "schema_selection_source": version_selection["source"],
        }
        if _version_key(target_schema_version) >= _version_key("1.1.0"):
            payload["schema_roadmap_ref"] = f"roadmap:v{target_schema_version}"
        if _version_key(target_schema_version) >= _version_key("2.0.0"):
            payload["schema_negotiation_hints"] = payload["schema_negotiation"]
            payload["contract_lifecycle"] = {"state": lifecycle_state}

        payload = _shape_payload_for_contract(
            payload,
            contract,
            strict_payload_shape=strict_payload_shape,
        )
        lines = [
            f"BaseTrue Insights {label} Retrospective",
            f"Generated: {today.isoformat()}",
            f"Window start: {start_date.isoformat()}",
            "",
            f"Snapshots: {len(rows)}",
            f"Average Pressure: {avg_pressure}",
            f"Average Priority Score: {avg_priority}",
            f"Latest State: {latest.state_label}",
            f"Latest Growth Direction: {latest.growth_direction}",
            f"Latest Quadrant Priority: {latest.quadrant_priority}",
            f"Latest Pipeline Bottleneck: {latest.pipeline_bottleneck}",
            "",
            "Recommended Action:",
            latest.recommended_action or "No recommended action recorded.",
            "",
            "Daily Brief:",
            latest.daily_brief or "No daily brief recorded.",
            "",
            "Weekly Summary:",
            latest.weekly_summary or "No weekly summary recorded.",
            "",
            "Monthly Outlook:",
            latest.monthly_outlook or "No monthly outlook recorded.",
        ]
    else:
        payload = {
            "schema_version": target_schema_version,
            "default_schema_version": resolved_default or CURRENT_SCHEMA_VERSION,
            "strict_negotiation": strict_negotiation,
            "strict_payload_shape": strict_payload_shape,
            "export_format": "basetrue-retrospective-json",
            "schema_hash": schema_hash,
            "schema_notes": {
                "compatibility": "Backward-compatible additive changes only within major version 1.",
                "required_fields": required_fields,
                "optional_fields": optional_fields,
                "lifecycle_state": lifecycle_state,
                "stability_window": stability,
                "deprecation_policy": deprecation_policy,
                "evolution_roadmap": roadmap,
                "changelog": [
                    {
                        "version": target_schema_version,
                        "date": today.isoformat(),
                        "notes": "Versioned retrospective JSON export contract.",
                    }
                ],
            },
            "title": f"BaseTrue Insights {label} Retrospective",
            "generated": today.isoformat(),
            "window_start": start_date.isoformat(),
            "period": period,
            "snapshot_count": 0,
            "avg_pressure": 0,
            "avg_priority_score": 0,
            "latest": None,
            "snapshots": [],
            "note": "No narrative snapshots available for this period.",
            "schema_negotiation": schema_negotiation,
            "schema_selection_source": version_selection["source"],
        }
        if _version_key(target_schema_version) >= _version_key("1.1.0"):
            payload["schema_roadmap_ref"] = f"roadmap:v{target_schema_version}"
        if _version_key(target_schema_version) >= _version_key("2.0.0"):
            payload["schema_negotiation_hints"] = payload["schema_negotiation"]
            payload["contract_lifecycle"] = {"state": lifecycle_state}

        payload = _shape_payload_for_contract(
            payload,
            contract,
            strict_payload_shape=strict_payload_shape,
        )
        lines = [
            f"BaseTrue Insights {label} Retrospective",
            f"Generated: {today.isoformat()}",
            "",
            "No narrative snapshots available for this period.",
        ]

    if output_format == "json":
        response = JsonResponse(payload)
        response["Content-Disposition"] = f'attachment; filename="basetrue-{period}-retrospective.json"'
        _record_contract_usage(
            endpoint="export",
            tenant_key=tenant_key,
            client_key=client_name,
            requested_schema_version=requested_schema_version,
            selected_schema_version=target_schema_version,
            negotiation_source=version_selection.get("source", ""),
            strict_negotiation=strict_negotiation,
            strict_payload_shape=strict_payload_shape,
            period=period,
            output_format=output_format,
            status_code=200,
        )
        return response

    body = "\n".join(lines) + "\n"
    response = HttpResponse(body, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="basetrue-{period}-retrospective.txt"'
    _record_contract_usage(
        endpoint="export",
        client_key=client_name,
        requested_schema_version=requested_schema_version,
        selected_schema_version=target_schema_version,
        negotiation_source=version_selection.get("source", ""),
        strict_negotiation=strict_negotiation,
        strict_payload_shape=strict_payload_shape,
        period=period,
        output_format=output_format,
        status_code=200,
    )
    return response


def _insights_retrospective_export_schema_view(request):
    today = timezone.now().date()
    tenant_key = (request.GET.get("tenant") or "default").strip() or "default"
    client_name = (request.GET.get("client") or "").strip()
    capability_tokens = _parse_capability_tokens(request.GET.get("capabilities"))
    requested_default_schema_version = (request.GET.get("default_schema_version") or "").strip()
    strict_negotiation = _parse_bool(request.GET.get("strict_negotiation"))
    merged = _merge_profile_defaults(
        request,
        tenant_key,
        client_name,
        requested_default_schema_version,
        capability_tokens,
        strict_negotiation,
        False,
    )
    requested_default_schema_version = merged["default_schema_version"]
    capability_tokens = merged["capability_tokens"]
    strict_negotiation = merged["strict_negotiation"]
    catalog = _schema_contract_catalog()
    contract = dict(catalog.get(CURRENT_SCHEMA_VERSION, {}))
    contract["version"] = CURRENT_SCHEMA_VERSION
    required_fields = contract.get("required_fields", [])
    optional_fields = contract.get("optional_fields", [])
    schema_hash = _schema_hash_for(contract)
    resolved_default = _resolve_default_schema_version(catalog, requested_default_schema_version)

    if requested_default_schema_version and not resolved_default:
        _record_contract_usage(
            endpoint="schema",
            tenant_key=tenant_key,
            client_key=client_name,
            requested_schema_version="",
            strict_negotiation=strict_negotiation,
            strict_payload_shape=False,
            status_code=400,
            negotiation_source="validation-error",
        )
        return JsonResponse(
            {
                "error": "Unsupported default_schema_version",
                "requested": requested_default_schema_version,
                "available_versions": sorted(catalog.keys()),
            },
            status=400,
        )

    compatibility_matrix = _schema_compatibility_matrix()
    version_aliases = _schema_version_aliases(catalog)
    lifecycle_states = {
        version: {
            "status": info.get("status", "unknown"),
            "lifecycle_state": info.get("lifecycle_state", "unknown"),
            "export_enabled": bool(info.get("export_enabled", True)),
            "sunset_after": info.get("sunset_after"),
        }
        for version, info in catalog.items()
    }
    negotiation_hint = _schema_negotiation_hint(
        catalog,
        client=client_name,
        capabilities=capability_tokens,
        preferred_default=resolved_default or "",
    )
    strict_selection = _select_schema_version(
        catalog,
        requested_schema_version="",
        preferred_default=resolved_default or "",
        client=client_name,
        capabilities=capability_tokens,
        strict=strict_negotiation,
    )

    payload = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "default_schema_version": resolved_default or CURRENT_SCHEMA_VERSION,
        "export_format": "basetrue-retrospective-json",
        "schema_hash": schema_hash,
        "description": "Schema metadata for BaseTrue retrospective JSON exports.",
        "compatibility": "Backward-compatible additive changes only within major version 1.",
        "compatibility_matrix": compatibility_matrix,
        "version_aliases": version_aliases,
        "contract_lifecycle_states": lifecycle_states,
        "schema_negotiation_hint": negotiation_hint,
        "strict_negotiation": {
            "supported": True,
            "enabled": strict_negotiation,
            "selection": strict_selection,
        },
        "stability_window": _schema_stability_window(today),
        "deprecation_policy": _schema_deprecation_policy(),
        "evolution_roadmap": _schema_evolution_roadmap(),
        "required_fields": required_fields,
        "optional_fields": optional_fields,
        "versions": {
            version: {
                "status": info.get("status", "unknown"),
                "required_fields": info.get("required_fields", []),
                "optional_fields": info.get("optional_fields", []),
                "schema_hash": _schema_hash_for({
                    "version": version,
                    "required_fields": info.get("required_fields", []),
                    "optional_fields": info.get("optional_fields", []),
                }),
            }
            for version, info in catalog.items()
        },
        "endpoints": {
            "monthly_json": "/admin/insights-retrospective-export/?period=monthly&format=json",
            "quarterly_json": "/admin/insights-retrospective-export/?period=quarterly&format=json",
            "monthly_json_default_pin": "/admin/insights-retrospective-export/?period=monthly&format=json&default_schema_version=1.0.0",
            "quarterly_json_default_pin": "/admin/insights-retrospective-export/?period=quarterly&format=json&default_schema_version=1.1.0",
            "monthly_json_multi": "/admin/insights-retrospective-export/?period=monthly&format=json&schema_versions=1.0.0,1.1.0",
            "monthly_json_migration_bundle": "/admin/insights-retrospective-export/?period=monthly&format=json&schema_versions=migration_bundle",
            "monthly_json_alias_stable": "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=stable",
            "monthly_json_alias_lts": "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=lts",
            "monthly_json_alias_latest": "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=latest",
            "monthly_json_capability_negotiated": "/admin/insights-retrospective-export/?period=monthly&format=json&client=legacy_csv_bridge&capabilities=legacy_only",
            "monthly_json_capability_negotiated_strict": "/admin/insights-retrospective-export/?period=monthly&format=json&client=legacy_csv_bridge&capabilities=legacy_only&strict_negotiation=1",
            "monthly_json_v11": "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=1.1.0",
            "quarterly_json_v11": "/admin/insights-retrospective-export/?period=quarterly&format=json&schema_version=1.1.0",
            "monthly_json_v20": "/admin/insights-retrospective-export/?period=monthly&format=json&schema_version=2.0.0&capabilities=experimental_fields",
            "monthly_txt": "/admin/insights-retrospective-export/?period=monthly",
            "quarterly_txt": "/admin/insights-retrospective-export/?period=quarterly",
            "schema_diff": "/admin/insights-retrospective-export-schema-diff/?from=1.0.0&to=1.1.0",
            "contract_selftest": "/admin/insights-retrospective-contract-selftest/",
        },
    }
    _record_contract_usage(
        endpoint="schema",
        tenant_key=tenant_key,
        client_key=client_name,
        requested_schema_version="",
        selected_schema_version=CURRENT_SCHEMA_VERSION,
        strict_negotiation=strict_negotiation,
        strict_payload_shape=False,
        status_code=200,
        negotiation_source=strict_selection.get("source", ""),
    )
    return JsonResponse(payload)


def _insights_retrospective_negotiate_view(request):
    catalog = _schema_contract_catalog()
    version_aliases = _schema_version_aliases(catalog)
    compatibility_matrix = _schema_compatibility_matrix()

    tenant_key = (request.GET.get("tenant") or "default").strip() or "default"
    requested_schema_version = (request.GET.get("schema_version") or "").strip()
    requested_default_schema_version = (request.GET.get("default_schema_version") or "").strip()
    requested_from_version = (request.GET.get("from_version") or "").strip()
    client_name = (request.GET.get("client") or "").strip()
    capability_tokens = _parse_capability_tokens(request.GET.get("capabilities"))
    strict_negotiation = _parse_bool(request.GET.get("strict_negotiation"))
    strict_payload_shape = _parse_bool(request.GET.get("strict_payload_shape"))

    merged = _merge_profile_defaults(
        request,
        tenant_key,
        client_name,
        requested_default_schema_version,
        capability_tokens,
        strict_negotiation,
        strict_payload_shape,
    )
    requested_default_schema_version = merged["default_schema_version"]
    capability_tokens = merged["capability_tokens"]
    strict_negotiation = merged["strict_negotiation"]
    strict_payload_shape = merged["strict_payload_shape"]
    applied_profile = merged["profile"]

    resolved_schema_version = _resolve_schema_version_alias(requested_schema_version, catalog)
    resolved_default_schema_version = _resolve_schema_version_alias(requested_default_schema_version, catalog)
    resolved_from_version = _resolve_schema_version_alias(requested_from_version, catalog)

    resolved_default = _resolve_default_schema_version(catalog, requested_default_schema_version)
    if requested_default_schema_version and not resolved_default:
        _record_contract_usage(
            endpoint="negotiate",
            tenant_key=tenant_key,
            client_key=client_name,
            requested_schema_version=requested_schema_version,
            strict_negotiation=strict_negotiation,
            strict_payload_shape=strict_payload_shape,
            status_code=400,
            negotiation_source="validation-error",
        )
        return JsonResponse(
            {
                "error": "Unsupported default_schema_version",
                "requested": requested_default_schema_version,
                "available_versions": sorted(catalog.keys()),
                "version_aliases": version_aliases,
            },
            status=400,
        )

    selection = _select_schema_version(
        catalog,
        requested_schema_version=requested_schema_version,
        preferred_default=resolved_default or "",
        client=client_name,
        capabilities=capability_tokens,
        strict=strict_negotiation,
    )
    if not selection.get("ok"):
        _record_contract_usage(
            endpoint="negotiate",
            tenant_key=tenant_key,
            client_key=client_name,
            requested_schema_version=requested_schema_version,
            strict_negotiation=strict_negotiation,
            strict_payload_shape=strict_payload_shape,
            status_code=400,
            negotiation_source="selection-error",
        )
        return JsonResponse(
            {
                "error": selection.get("error", "Negotiation failed"),
                "requested": selection.get("requested", requested_schema_version),
                "available_versions": selection.get("available_versions", sorted(catalog.keys())),
                "version_aliases": version_aliases,
                "compatibility_matrix": compatibility_matrix,
            },
            status=400,
        )

    selected_version = selection["selected_version"]
    selected_contract = dict(catalog.get(selected_version, {}))
    selected_contract["version"] = selected_version

    lifecycle_states = {
        version: {
            "status": info.get("status", "unknown"),
            "lifecycle_state": info.get("lifecycle_state", "unknown"),
            "export_enabled": bool(info.get("export_enabled", True)),
            "sunset_after": info.get("sunset_after"),
        }
        for version, info in catalog.items()
    }

    ordered_versions_desc = sorted(catalog.keys(), key=_version_key, reverse=True)
    diff_links = {}
    for version in ordered_versions_desc:
        if version == selected_version:
            continue
        diff_links[f"{selected_version}->{version}"] = (
            f"/admin/insights-retrospective-export-schema-diff/?from={selected_version}&to={version}"
        )

    upgrade_anchor = resolved_from_version or resolved_schema_version
    upgrade_paths = []
    if upgrade_anchor and upgrade_anchor in catalog and upgrade_anchor != selected_version:
        direction = 1 if _version_key(selected_version) >= _version_key(upgrade_anchor) else -1
        ordered_asc = sorted(catalog.keys(), key=_version_key)
        if direction == -1:
            ordered_asc = list(reversed(ordered_asc))

        start_idx = ordered_asc.index(upgrade_anchor)
        end_idx = ordered_asc.index(selected_version)
        path_versions = ordered_asc[start_idx : end_idx + 1]

        for idx in range(len(path_versions) - 1):
            from_version = path_versions[idx]
            to_version = path_versions[idx + 1]
            diff = _schema_diff_payload(from_version, to_version, catalog) or {}
            upgrade_paths.append(
                {
                    "from_version": from_version,
                    "to_version": to_version,
                    "breaking_change_detected": bool(diff.get("breaking_change_detected", False)),
                    "required_added": diff.get("required_added", []),
                    "optional_added": diff.get("optional_added", []),
                    "diff_url": f"/admin/insights-retrospective-export-schema-diff/?from={from_version}&to={to_version}",
                }
            )

    payload = {
        "service": "basetrue-retrospective-contract-negotiation",
        "generated": timezone.now().isoformat(),
        "inputs": {
            "schema_version": requested_schema_version,
            "default_schema_version": requested_default_schema_version,
            "from_version": requested_from_version,
            "client": client_name,
            "tenant": tenant_key,
            "capabilities": sorted(capability_tokens),
            "strict_negotiation": strict_negotiation,
            "strict_payload_shape": strict_payload_shape,
            "applied_client_profile": applied_profile,
        },
        "alias_resolution": {
            "schema_version": {
                "provided": requested_schema_version,
                "resolved": resolved_schema_version,
            },
            "default_schema_version": {
                "provided": requested_default_schema_version,
                "resolved": resolved_default_schema_version,
            },
            "from_version": {
                "provided": requested_from_version,
                "resolved": resolved_from_version,
            },
            "aliases": version_aliases,
        },
        "recommendation": {
            "selected_version": selected_version,
            "selection_source": selection.get("source", "negotiated"),
            "why": selection.get("negotiation", {}).get("reasons", []),
            "lifecycle_state": lifecycle_states.get(selected_version, {}).get("lifecycle_state", "unknown"),
            "schema_hash": _schema_hash_for(selected_contract),
        },
        "upgrade_paths": upgrade_paths,
        "diff_links": diff_links,
        "contract_lifecycle_states": lifecycle_states,
        "compatibility_matrix": compatibility_matrix,
        "strict_shaping_guarantees": {
            "supported": True,
            "enabled": strict_payload_shape,
            "field_leakage_prevented_when_enabled": True,
            "selected_version_required_fields": selected_contract.get("required_fields", []),
            "selected_version_optional_fields": selected_contract.get("optional_fields", []),
            "example_export_url": (
                f"/admin/insights-retrospective-export/?period=monthly&format=json"
                f"&schema_version={selected_version}&strict_payload_shape=1"
            ),
        },
        "schema_docs": {
            "schema_metadata": "/admin/insights-retrospective-export-schema/",
            "schema_diff": "/admin/insights-retrospective-export-schema-diff/",
            "contract_selftest": "/admin/insights-retrospective-contract-selftest/",
        },
    }
    _record_contract_usage(
        endpoint="negotiate",
        tenant_key=tenant_key,
        client_key=client_name,
        requested_schema_version=requested_schema_version,
        selected_schema_version=selected_version,
        strict_negotiation=strict_negotiation,
        strict_payload_shape=strict_payload_shape,
        status_code=200,
        negotiation_source=selection.get("source", ""),
    )
    return JsonResponse(payload)


def _insights_contract_usage_analytics_view(request):
    tenant_key = (request.GET.get("tenant") or "").strip()
    try:
        window_days = int((request.GET.get("window_days") or "30").strip())
    except ValueError:
        window_days = 30
    if window_days <= 0:
        window_days = 30

    payload = _contract_usage_analytics_payload(window_days=window_days, tenant_key=tenant_key)
    return JsonResponse(payload)


def _insights_contract_billing_summary_view(request):
    tenant_key = (request.GET.get("tenant") or "").strip()
    client_key = (request.GET.get("client") or "").strip()
    output_format = (request.GET.get("format") or "json").strip().lower()
    persist_snapshot = _parse_bool(request.GET.get("persist_snapshot"))
    if output_format not in {"json", "csv", "txt"}:
        output_format = "json"
    try:
        window_days = int((request.GET.get("window_days") or "30").strip())
    except ValueError:
        window_days = 30
    if window_days <= 0:
        window_days = 30

    payload = _contract_billing_summary_payload(
        window_days=window_days,
        tenant_key=tenant_key,
        client_key=client_key,
    )
    if persist_snapshot:
        snapshot = _persist_billing_snapshot(payload)
        payload["snapshot_created"] = bool(snapshot)
        payload["snapshot_history"] = _billing_snapshot_history_payload(tenant_key=tenant_key, client_key=client_key)
    _record_contract_usage(
        endpoint="billing_summary",
        tenant_key=tenant_key or "default",
        client_key=client_key or "system",
        output_format=output_format,
        status_code=200,
        negotiation_source="control-plane",
    )

    if output_format == "json":
        return JsonResponse(payload)

    rows = payload.get("summary", [])
    if output_format == "csv":
        headers = [
            "tenant_key",
            "client_key",
            "billing_plan",
            "event_count",
            "billable_units",
            "monthly_event_allowance",
            "usage_pct",
            "enforcement_state",
            "enforcement_mode",
            "estimated_amount",
            "overage_units",
            "overage_amount",
        ]
        csv_lines = [",".join(headers)]
        for row in rows:
            csv_lines.append(
                ",".join(str(row.get(header, "")) for header in headers)
            )
        response = HttpResponse("\n".join(csv_lines) + "\n", content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="contract-billing-summary.csv"'
        return response

    txt_lines = [
        f"Contract Billing Summary ({payload.get('window_days')}d)",
        f"Tenant: {payload.get('tenant_key')}",
        f"Client: {payload.get('client_key')}",
        "",
    ]
    for row in rows:
        txt_lines.extend(
            [
                f"{row.get('tenant_key')} / {row.get('client_key')}",
                f"Plan: {row.get('billing_plan')}",
                f"Units: {row.get('billable_units')} of {row.get('monthly_event_allowance')} ({row.get('usage_pct')}%)",
                f"State: {row.get('enforcement_state')} ({row.get('enforcement_mode')})",
                f"Estimated: {row.get('estimated_amount')} | Overage: {row.get('overage_amount')}",
                "",
            ]
        )
    response = HttpResponse("\n".join(txt_lines), content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="contract-billing-summary.txt"'
    return response


def _insights_contract_enforcement_execute_view(request):
    tenant_key = (request.GET.get("tenant") or "default").strip() or "default"
    client_key = (request.GET.get("client") or "").strip()
    action = (request.GET.get("action") or "").strip()
    result = _execute_billing_enforcement_action(tenant_key=tenant_key, client_key=client_key, action=action)
    status_code = 200 if result.get("ok") else 400
    _record_contract_usage(
        endpoint="billing_enforcement",
        tenant_key=tenant_key,
        client_key=client_key,
        status_code=status_code,
        negotiation_source=action,
    )
    return JsonResponse(result, status=status_code)


def _insights_contract_billing_job_queue_view(request):
    tenant_key = (request.GET.get("tenant") or "default").strip() or "default"
    client_key = (request.GET.get("client") or "all").strip() or "all"
    job_type = (request.GET.get("job_type") or "billing_cycle").strip()
    try:
        window_days = int((request.GET.get("window_days") or "30").strip())
    except ValueError:
        window_days = 30
    job = _enqueue_billing_job(
        job_type=job_type,
        tenant_key=tenant_key,
        client_key=client_key,
        payload={"tenant": tenant_key, "client": client_key, "window_days": window_days},
        requested_by=request.user if getattr(request.user, "is_authenticated", False) else None,
    )
    status_code = 200 if job else 500
    payload = {
        "queued": bool(job),
        "job_id": getattr(job, "id", None),
        "job_type": job_type,
        "tenant": tenant_key,
        "client": client_key,
    }
    _record_contract_usage(
        endpoint="billing_job_queue",
        tenant_key=tenant_key,
        client_key=client_key,
        status_code=status_code,
        negotiation_source=job_type,
    )
    return JsonResponse(payload, status=status_code)


def _insights_contract_billing_job_process_view(request):
    try:
        limit = int((request.GET.get("limit") or "10").strip())
    except ValueError:
        limit = 10
    processed = _process_pending_billing_jobs(limit=limit)
    payload = {
        "processed_count": len(processed),
        "jobs": [
            {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "tenant_key": job.tenant_key,
                "client_key": job.client_key,
            }
            for job in processed
        ],
    }
    _record_contract_usage(
        endpoint="billing_job_process",
        tenant_key="default",
        client_key="system",
        status_code=200,
        negotiation_source="process",
    )
    return JsonResponse(payload)


def _insights_contract_billing_access_links_view(request):
    tenant_key = (request.GET.get("tenant") or "default").strip() or "default"
    client_key = (request.GET.get("client") or "all").strip() or "all"
    action = (request.GET.get("action") or "list").strip().lower()
    try:
        window_days = int((request.GET.get("window_days") or "30").strip())
    except ValueError:
        window_days = 30
    try:
        ttl_days = int((request.GET.get("ttl_days") or str(BILLING_ACCESS_DEFAULT_TTL_DAYS)).strip())
    except ValueError:
        ttl_days = BILLING_ACCESS_DEFAULT_TTL_DAYS
    link_id = (request.GET.get("link_id") or "").strip()

    if action == "issue":
        link = _issue_billing_access_link(
            tenant_key=tenant_key,
            client_key=client_key,
            window_days=window_days,
            created_by=request.user if getattr(request.user, "is_authenticated", False) else None,
            label=(request.GET.get("label") or "Customer billing portal").strip(),
            recipient_email=(request.GET.get("recipient") or "").strip(),
            ttl_days=ttl_days,
            reuse_existing=False,
        )
        payload = {
            "ok": bool(link),
            "action": action,
            "link": _billing_access_link_payload(link) if link else {},
        }
        return JsonResponse(payload, status=200 if link else 500)

    if action == "revoke":
        try:
            from .models import ContractBillingAccessLink
        except Exception:
            return JsonResponse({"ok": False, "error": "Access link model unavailable"}, status=500)

        link = ContractBillingAccessLink.objects.filter(id=link_id).first()
        if not link:
            return JsonResponse({"ok": False, "error": "Access link not found"}, status=404)
        link.is_active = False
        link.revoked_at = timezone.now()
        link.save(update_fields=["is_active", "revoked_at", "updated_at"])
        return JsonResponse({"ok": True, "action": action, "link": _billing_access_link_payload(link)})

    payload = {
        "ok": True,
        "action": "list",
        "links": _billing_access_links_payload(
            tenant_key=tenant_key if tenant_key != "all" else "",
            client_key=client_key if client_key != "all" else "",
            window_days=window_days,
        ),
    }
    return JsonResponse(payload)


def _insights_contract_billing_access_links_audit_view(request):
    tenant_key = (request.GET.get("tenant") or "").strip()
    client_key = (request.GET.get("client") or "").strip()
    status_filter = (request.GET.get("status") or "all").strip().lower()
    expires_filter = (request.GET.get("expires") or "all").strip().lower()
    sort_by = (request.GET.get("sort") or "newest").strip().lower()
    output_format = (request.GET.get("format") or "json").strip().lower()
    if output_format not in {"json", "csv"}:
        output_format = "json"
    try:
        window_days = int((request.GET.get("window_days") or "30").strip())
    except ValueError:
        window_days = 30
    if window_days <= 0:
        window_days = 30

    links = _billing_access_links_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=window_days,
        limit=1000,
        status_filter=status_filter,
        expires_filter=expires_filter,
        sort_by=sort_by,
    )
    analytics = _billing_access_link_analytics_payload(
        tenant_key=tenant_key,
        client_key=client_key,
        window_days=window_days,
        status_filter=status_filter,
        expires_filter=expires_filter,
    )
    payload = {
        "ok": True,
        "window_days": window_days,
        "tenant_key": tenant_key or "all",
        "client_key": client_key or "all",
        "status_filter": status_filter,
        "expires_filter": expires_filter,
        "sort": sort_by,
        "count": len(links),
        "analytics": analytics,
        "links": links,
    }
    if output_format == "json":
        return JsonResponse(payload)

    headers = [
        "id",
        "label",
        "tenant_key",
        "client_key",
        "window_days",
        "status",
        "expires_at",
        "expires_in_days",
        "use_count",
        "last_used_at",
        "created_at",
        "recipient_email",
    ]
    lines = [",".join(headers)]
    for row in links:
        lines.append(
            ",".join(
                str(row.get(col, "")).replace(",", " ")
                for col in headers
            )
        )
    response = HttpResponse("\n".join(lines) + "\n", content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="access-link-audit.csv"'
    return response


def _insights_contract_billing_notifications_view(request):
    action = (request.GET.get("action") or "list").strip().lower()
    tenant_key = (request.GET.get("tenant") or "").strip()
    client_key = (request.GET.get("client") or "").strip()

    if action == "retry":
        result = _retry_billing_notification(
            notification_id=(request.GET.get("notification_id") or "").strip(),
            recipient_override=(request.GET.get("recipient") or "").strip(),
        )
        status_code = 200 if result.get("ok") else 400
        return JsonResponse(result, status=status_code)

    return JsonResponse(
        {
            "ok": True,
            "notifications": _customer_billing_notifications_payload(
                tenant_key=tenant_key,
                client_key=client_key,
                limit=20,
            ),
        }
    )


def _insights_retrospective_export_schema_diff_view(request):
    from_version = (request.GET.get("from") or CURRENT_SCHEMA_VERSION).strip()
    to_version = (request.GET.get("to") or CURRENT_SCHEMA_VERSION).strip()
    catalog = _schema_contract_catalog()
    diff_payload = _schema_diff_payload(from_version, to_version, catalog)
    if diff_payload is None:
        return JsonResponse(
            {
                "error": "Unknown schema version(s)",
                "from": from_version,
                "to": to_version,
                "available_versions": sorted(catalog.keys()),
            },
            status=404,
        )
    return JsonResponse(diff_payload)


def _insights_retrospective_contract_selftest_view(request):
    catalog = _schema_contract_catalog()
    contract = dict(catalog.get(CURRENT_SCHEMA_VERSION, {}))
    contract["version"] = CURRENT_SCHEMA_VERSION
    required = contract.get("required_fields", [])
    optional = contract.get("optional_fields", [])
    schema_hash = _schema_hash_for(contract)

    checks = []
    checks.append({
        "name": "required_fields_non_empty",
        "passed": bool(required),
        "detail": f"required_fields_count={len(required)}",
    })
    checks.append({
        "name": "schema_hash_present",
        "passed": bool(schema_hash),
        "detail": f"schema_hash={schema_hash}",
    })
    checks.append({
        "name": "no_required_optional_overlap",
        "passed": not bool(set(required).intersection(set(optional))),
        "detail": f"overlap_count={len(set(required).intersection(set(optional)))}",
    })
    checks.append({
        "name": "current_version_in_catalog",
        "passed": CURRENT_SCHEMA_VERSION in catalog,
        "detail": f"current_version={CURRENT_SCHEMA_VERSION}",
    })
    checks.append({
        "name": "current_version_is_active",
        "passed": contract.get("lifecycle_state") == "active",
        "detail": f"lifecycle_state={contract.get('lifecycle_state', 'unknown')}",
    })
    checks.append({
        "name": "compatibility_matrix_present",
        "passed": bool(_schema_compatibility_matrix()),
        "detail": f"matrix_entries={len(_schema_compatibility_matrix())}",
    })
    checks.append({
        "name": "lifecycle_states_present",
        "passed": all("lifecycle_state" in entry for entry in catalog.values()),
        "detail": f"catalog_versions={len(catalog)}",
    })

    passed = all(check["passed"] for check in checks)
    payload = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "passed": passed,
        "checks": checks,
        "timestamp": timezone.now().isoformat(),
    }
    return JsonResponse(payload, status=200 if passed else 500)


def configure_unified_admin():
    admin.site.site_header = "GrassRoots Control Center"
    admin.site.site_title = "GrassRoots Admin"
    admin.site.index_title = "Unified application administration"

    current_get_urls = admin.site.get_urls

    @wraps(current_get_urls)
    def get_urls_with_dashboard():
        urls = current_get_urls()
        custom_urls = [
            path(
                "dashboard/",
                admin.site.admin_view(_dashboard_view),
                name="dashboard",
            ),
            path(
                "platform-dashboard/",
                admin.site.admin_view(_dashboard_view),
                name="platform-dashboard",
            ),
            path(
                "operator-dashboard/",
                admin.site.admin_view(_operator_dashboard_view),
                name="operator-dashboard",
            ),
            path(
                "operator/",
                admin.site.admin_view(_operator_dashboard_view),
                name="operator",
            ),
            path(
                "moderator-dashboard/",
                admin.site.admin_view(_moderator_dashboard_view),
                name="moderator-dashboard",
            ),
            path(
                "moderator/",
                admin.site.admin_view(_moderator_dashboard_view),
                name="moderator",
            ),
            path(
                "executive-dashboard/",
                admin.site.admin_view(_executive_dashboard_view),
                name="executive-dashboard",
            ),
            path(
                "executive/",
                admin.site.admin_view(_executive_dashboard_view),
                name="executive",
            ),
            path(
                "basetrue-insights/",
                admin.site.admin_view(_basetrue_insights_view),
                name="basetrue-insights",
            ),
            path(
                "insights/",
                admin.site.admin_view(_basetrue_insights_view),
                name="insights",
            ),
            path(
                "insights-retrospective-export/",
                admin.site.admin_view(_insights_retrospective_export_view),
                name="insights-retrospective-export",
            ),
            path(
                "insights-retrospective-export-schema/",
                admin.site.admin_view(_insights_retrospective_export_schema_view),
                name="insights-retrospective-export-schema",
            ),
            path(
                "insights-retrospective-export-schema-diff/",
                admin.site.admin_view(_insights_retrospective_export_schema_diff_view),
                name="insights-retrospective-export-schema-diff",
            ),
            path(
                "insights-retrospective-contract-selftest/",
                admin.site.admin_view(_insights_retrospective_contract_selftest_view),
                name="insights-retrospective-contract-selftest",
            ),
            path(
                "insights-retrospective-negotiate/",
                admin.site.admin_view(_insights_retrospective_negotiate_view),
                name="insights-retrospective-negotiate",
            ),
            path(
                "insights-contract-usage-analytics/",
                admin.site.admin_view(_insights_contract_usage_analytics_view),
                name="insights-contract-usage-analytics",
            ),
            path(
                "insights-contract-billing-summary/",
                admin.site.admin_view(_insights_contract_billing_summary_view),
                name="insights-contract-billing-summary",
            ),
            path(
                "insights-contract-enforcement/",
                admin.site.admin_view(_insights_contract_enforcement_execute_view),
                name="insights-contract-enforcement",
            ),
            path(
                "insights-contract-billing-jobs-queue/",
                admin.site.admin_view(_insights_contract_billing_job_queue_view),
                name="insights-contract-billing-jobs-queue",
            ),
            path(
                "insights-contract-billing-jobs-process/",
                admin.site.admin_view(_insights_contract_billing_job_process_view),
                name="insights-contract-billing-jobs-process",
            ),
            path(
                "insights-contract-billing-access-links/",
                admin.site.admin_view(_insights_contract_billing_access_links_view),
                name="insights-contract-billing-access-links",
            ),
            path(
                "insights-contract-billing-access-links-audit/",
                admin.site.admin_view(_insights_contract_billing_access_links_audit_view),
                name="insights-contract-billing-access-links-audit",
            ),
            path(
                "insights-contract-billing-notifications/",
                admin.site.admin_view(_insights_contract_billing_notifications_view),
                name="insights-contract-billing-notifications",
            ),
        ]
        return custom_urls + urls

    admin.site.get_urls = get_urls_with_dashboard
