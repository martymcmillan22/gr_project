from __future__ import annotations

from django.utils import timezone

from project_middle_layer.models import SemanticPlugin


def register_plugin(payload: dict[str, object]) -> SemanticPlugin:
    slug = str(payload.get("slug") or "").strip()
    if not slug:
        raise ValueError("Plugin slug is required.")

    plugin, _ = SemanticPlugin.objects.update_or_create(
        slug=slug,
        defaults={
            "name": str(payload.get("name") or slug),
            "plugin_type": str(payload.get("plugin_type") or "agent"),
            "entrypoint": str(payload.get("entrypoint") or ""),
            "capabilities": payload.get("capabilities", []) if isinstance(payload.get("capabilities", []), list) else [],
            "version": str(payload.get("version") or "0.0.1"),
            "metadata": payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {},
        },
    )
    return plugin


def _plugin_hook(plugin: SemanticPlugin, event: str):
    metadata = plugin.metadata if isinstance(plugin.metadata, dict) else {}
    metadata["last_hook"] = event
    metadata["last_hook_at"] = timezone.now().isoformat()
    plugin.metadata = metadata


def plugin_lifecycle_on_load(plugin: SemanticPlugin):
    _plugin_hook(plugin, "on_load")
    plugin.last_status = "loaded"
    plugin.last_error = ""
    plugin.save(update_fields=["metadata", "last_status", "last_error", "updated_at"])


def plugin_lifecycle_on_unload(plugin: SemanticPlugin):
    _plugin_hook(plugin, "on_unload")
    plugin.last_status = "unloaded"
    plugin.save(update_fields=["metadata", "last_status", "updated_at"])


def plugin_lifecycle_on_update(plugin: SemanticPlugin):
    _plugin_hook(plugin, "on_update")
    plugin.last_status = "updated"
    plugin.save(update_fields=["metadata", "last_status", "updated_at"])


def set_plugin_enabled(*, slug: str, enabled: bool) -> SemanticPlugin:
    plugin = SemanticPlugin.objects.filter(slug=slug).first()
    if not plugin:
        raise ValueError("Plugin not found.")

    plugin.enabled = bool(enabled)
    if plugin.enabled:
        plugin_lifecycle_on_load(plugin)
    else:
        plugin_lifecycle_on_unload(plugin)
    return plugin


def map_plugin_capabilities() -> dict[str, list[str]]:
    mapping = {}
    for plugin in SemanticPlugin.objects.all()[:300]:
        mapping[plugin.slug] = [str(item).strip().lower() for item in (plugin.capabilities or [])]
    return mapping


def load_plugin_registry() -> dict[str, object]:
    plugins = list(SemanticPlugin.objects.order_by("name")[:300])
    return {
        "count": len(plugins),
        "plugins": [
            {
                "slug": plugin.slug,
                "name": plugin.name,
                "plugin_type": plugin.plugin_type,
                "entrypoint": plugin.entrypoint,
                "version": plugin.version,
                "enabled": plugin.enabled,
                "capabilities": plugin.capabilities,
                "last_status": plugin.last_status,
            }
            for plugin in plugins
        ],
        "capability_map": map_plugin_capabilities(),
    }
