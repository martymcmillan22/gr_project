from __future__ import annotations

from project_middle_layer.permissions import has_semantic_capability
from project_middle_layer.plugins import map_plugin_capabilities


GATEWAY_VERSION_MAP = {
    "v1": {
        "status": "stable",
        "routes": [
            "compile",
            "export",
            "search",
            "analytics",
            "merge",
            "versions",
            "marketplace",
            "extensions",
            "external-agents",
        ],
    }
}


def gateway_version_negotiation(requested_version: str | None) -> str:
    version = str(requested_version or "v1").strip().lower()
    if version not in GATEWAY_VERSION_MAP:
        return "v1"
    return version


def gateway_capability_enforcement(user, capability: str) -> bool:
    return has_semantic_capability(user, capability)


def gateway_route_map() -> dict[str, object]:
    return {
        "versions": GATEWAY_VERSION_MAP,
        "plugin_capability_map": map_plugin_capabilities(),
    }


def gateway_schema_introspection() -> dict[str, object]:
    return {
        "gateway_versions": list(GATEWAY_VERSION_MAP.keys()),
        "semantic_payload_sections": [
            "identity_payload",
            "semantic_tags",
            "lineage_explorer",
            "drift_forecast",
            "confidence",
            "stability_analysis",
            "analytics",
            "insights",
            "versioning",
        ],
    }


def gateway_health_status() -> dict[str, object]:
    return {
        "status": "healthy",
        "route_count": sum(len(block.get("routes", [])) for block in GATEWAY_VERSION_MAP.values()),
        "supported_versions": list(GATEWAY_VERSION_MAP.keys()),
    }


def gateway_dispatch(*, route: str, requested_version: str | None = None) -> dict[str, object]:
    version = gateway_version_negotiation(requested_version)
    routes = GATEWAY_VERSION_MAP[version].get("routes", [])
    return {
        "version": version,
        "route": route,
        "available": route in routes,
        "available_routes": routes,
    }
