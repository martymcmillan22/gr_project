from __future__ import annotations

from project_middle_layer.models import MarketplaceInstall, MarketplaceItem, MarketplaceVersion


def _parse_version_tuple(value: str) -> tuple[int, int, int]:
    parts = (value or "0.0.0").split(".")
    normalized = []
    for item in parts[:3]:
        try:
            normalized.append(int(item))
        except ValueError:
            normalized.append(0)
    while len(normalized) < 3:
        normalized.append(0)
    return tuple(normalized)


def resolve_marketplace_version(item: MarketplaceItem, requested_version: str | None = None) -> MarketplaceVersion | None:
    versions = list(item.versions.all()[:200])
    if not versions:
        return None
    if requested_version:
        return next((v for v in versions if v.version == requested_version), None)
    return sorted(versions, key=lambda item_version: _parse_version_tuple(item_version.version), reverse=True)[0]


def check_marketplace_compatibility(item_version: MarketplaceVersion) -> dict[str, object]:
    compatibility = item_version.compatibility if isinstance(item_version.compatibility, dict) else {}
    required = str(compatibility.get("min_project_middle_layer", "0.0.0"))
    return {
        "compatible": True,
        "required_min_project_middle_layer": required,
        "notes": compatibility.get("notes", ""),
    }


def build_marketplace_dependency_graph(item_version: MarketplaceVersion) -> dict[str, object]:
    dependencies = item_version.dependency_slugs if isinstance(item_version.dependency_slugs, list) else []
    return {
        "item_slug": item_version.item.slug,
        "version": item_version.version,
        "dependencies": dependencies,
    }


def install_marketplace_item(*, item_slug: str, requested_version: str | None = None, owner=None) -> dict[str, object]:
    item = MarketplaceItem.objects.filter(slug=item_slug, is_active=True).first()
    if not item:
        raise ValueError("Marketplace item not found.")

    version = resolve_marketplace_version(item, requested_version=requested_version)
    if not version:
        raise ValueError("Marketplace version not found.")

    compatibility = check_marketplace_compatibility(version)
    dependency_graph = build_marketplace_dependency_graph(version)

    install, _ = MarketplaceInstall.objects.update_or_create(
        item=item,
        defaults={
            "installed_version": version.version,
            "status": "installed",
            "owner": owner,
        },
    )

    return {
        "item_slug": item.slug,
        "installed_version": install.installed_version,
        "status": install.status,
        "compatibility": compatibility,
        "dependency_graph": dependency_graph,
    }


def uninstall_marketplace_item(*, item_slug: str) -> dict[str, object]:
    install = MarketplaceInstall.objects.select_related("item").filter(item__slug=item_slug).first()
    if not install:
        raise ValueError("Marketplace install not found.")

    install.status = "removed"
    install.save(update_fields=["status", "updated_at"])
    return {
        "item_slug": install.item.slug,
        "status": install.status,
    }


def build_marketplace_update_notifications() -> list[dict[str, object]]:
    notifications = []
    installs = MarketplaceInstall.objects.select_related("item").all()[:200]
    for install in installs:
        latest = resolve_marketplace_version(install.item)
        if latest and latest.version != install.installed_version:
            notifications.append(
                {
                    "item_slug": install.item.slug,
                    "installed_version": install.installed_version,
                    "latest_version": latest.version,
                }
            )
    return notifications
