from __future__ import annotations

from django.utils import timezone

from project_middle_layer.exports import build_semantic_export_payload
from project_middle_layer.models import SemanticIntegration
from project_middle_layer.services import compile_and_store_project_node


def get_active_integration_by_key(api_key: str | None, *, direction: str | None = None) -> SemanticIntegration | None:
    key = (api_key or "").strip()
    if not key:
        return None

    query = SemanticIntegration.objects.filter(api_key=key, status="active")
    if direction == "inbound":
        query = query.filter(direction__in=["inbound", "bidirectional"])
    elif direction == "outbound":
        query = query.filter(direction__in=["outbound", "bidirectional"])
    return query.first()


def run_inbound_integration_sync(*, integration: SemanticIntegration, payload: dict[str, object], triggered_by: str) -> dict[str, object]:
    title = str(payload.get("title") or payload.get("name") or "").strip()
    intent = str(payload.get("intent") or payload.get("semantic_intent") or "").strip()
    tier = str(payload.get("tier") or payload.get("visibility_tier") or "public").strip()
    tags = payload.get("tags") or payload.get("semantic_tags") or []

    if not isinstance(tags, list):
        raise ValueError("Inbound payload tags must be a list.")
    normalized_tags = sorted({str(tag).strip().lower() for tag in tags if str(tag).strip()})
    if not title or not intent or not normalized_tags:
        raise ValueError("Inbound payload requires title/name, intent, and at least one tag.")

    compiled, node = compile_and_store_project_node(
        {
            "slug": str(payload.get("slug") or title.lower().replace(" ", "-")).strip(),
            "name": title,
            "semantic_intent": intent,
            "mlas_tier": str(payload.get("mlas_tier") or "Semantic Utility"),
            "btif_classification": str(payload.get("btif_classification") or "ExpansionFlow"),
            "semantic_tags": normalized_tags,
            "visibility_tier": tier,
            "metadata": {
                "integration_slug": integration.slug,
                "integration_target_system": integration.target_system,
                "triggered_by": triggered_by,
            },
        }
    )

    integration.last_synced_at = timezone.now()
    integration.save(update_fields=["last_synced_at", "updated_at"])

    return {
        "integration": integration.slug,
        "project": {
            "id": node.id,
            "slug": node.slug,
            "name": node.name,
        },
        "identity_uri": compiled.get("identity_payload", {}).get("identity", {}).get("identity_uri", ""),
    }


def run_outbound_integration_sync(
    *,
    integration: SemanticIntegration,
    scope: str,
    project_slug: str | None,
    include_history: bool,
    max_items: int,
    triggered_by: str,
) -> dict[str, object]:
    payload = build_semantic_export_payload(
        scope=scope,
        project_slug=project_slug,
        include_history=include_history,
        max_items=max_items,
        exported_by=triggered_by,
    )

    integration.last_synced_at = timezone.now()
    integration.save(update_fields=["last_synced_at", "updated_at"])

    return payload
