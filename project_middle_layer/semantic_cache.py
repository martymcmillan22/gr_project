from __future__ import annotations

import hashlib
import json

from django.core.cache import cache

from project_middle_layer.analytics import build_semantic_analytics_dashboard
from project_middle_layer.insights import build_semantic_insights
from project_middle_layer.semantic import build_semantic_diff
from project_middle_layer.semantic_search import run_semantic_search


CACHE_NAMESPACE = "project_middle_layer:semantic_cache"


def _cache_key(target: str, params: dict[str, object]) -> str:
    canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{CACHE_NAMESPACE}:{target}:{digest}"


def get_or_set_cached(target: str, params: dict[str, object], *, ttl_seconds: int = 300):
    key = _cache_key(target, params)
    hit = cache.get(key)
    if hit is not None:
        return {"cache_key": key, "cached": True, "data": hit}

    if target == "analytics":
        data = build_semantic_analytics_dashboard(
            limit=int(params.get("limit", 20) or 20),
            branch_filter=str(params.get("branch_filter", "") or ""),
            tier_filter=str(params.get("tier_filter", "") or ""),
        )
    elif target == "search":
        data = run_semantic_search(str(params.get("q", "") or ""), limit=int(params.get("limit", 50) or 50))
    elif target == "insights":
        data = build_semantic_insights(limit=int(params.get("limit", 20) or 20))
    elif target == "diff":
        data = build_semantic_diff(
            params.get("source", {}) if isinstance(params.get("source", {}), dict) else {},
            params.get("target", {}) if isinstance(params.get("target", {}), dict) else {},
        )
    else:
        raise ValueError("Unsupported cache target.")

    cache.set(key, data, timeout=ttl_seconds)
    return {"cache_key": key, "cached": False, "data": data}


def flush_semantic_cache() -> dict[str, object]:
    cache.clear()
    return {"status": "cleared"}


def warm_semantic_cache() -> dict[str, object]:
    warmed = []
    warmed.append(get_or_set_cached("analytics", {"limit": 20, "branch_filter": "", "tier_filter": ""}, ttl_seconds=600)["cache_key"])
    warmed.append(get_or_set_cached("insights", {"limit": 20}, ttl_seconds=600)["cache_key"])
    warmed.append(get_or_set_cached("search", {"q": "semantic", "limit": 20}, ttl_seconds=600)["cache_key"])
    return {"status": "warmed", "keys": warmed}
