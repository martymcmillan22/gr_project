from __future__ import annotations

from collections import Counter

from django.utils import timezone

from project_middle_layer.insights import build_semantic_insights
from project_middle_layer.models import FederationPeer, SemanticLineageRecord
from project_middle_layer.semantic_search import run_semantic_search


def _active_peers() -> list[FederationPeer]:
    return list(FederationPeer.objects.filter(is_active=True).order_by("name")[:100])


def run_federated_search(query: str, *, limit: int = 50) -> dict[str, object]:
    peers = _active_peers()
    local = run_semantic_search(query, limit=limit)

    remote_sources = [
        {
            "peer": peer.slug,
            "peer_identity": peer.peer_identity,
            "simulated_result_count": min(limit, max(0, len(query))),
        }
        for peer in peers
    ]

    for peer in peers:
        peer.last_sync_at = timezone.now()
        peer.last_sync_status = "completed"
        peer.last_error = ""
        peer.save(update_fields=["last_sync_at", "last_sync_status", "last_error", "updated_at"])

    return {
        "query": query,
        "local": local,
        "federated_sources": remote_sources,
        "peer_count": len(peers),
    }


def run_federated_insights(*, limit: int = 20) -> dict[str, object]:
    peers = _active_peers()
    local_insights = build_semantic_insights(limit=limit)

    return {
        "local_insights": local_insights,
        "peer_overview": [
            {
                "peer": peer.slug,
                "capabilities": peer.capabilities,
                "shared_rules": peer.sync_rules,
            }
            for peer in peers
        ],
        "peer_count": len(peers),
    }


def run_federated_lineage_cluster_mapping() -> dict[str, object]:
    peers = _active_peers()
    counter: Counter[str] = Counter()

    for record in SemanticLineageRecord.objects.all()[:500]:
        for cluster in (record.semantic_clusters or []):
            if isinstance(cluster, dict):
                label = str(cluster.get("cluster", "unknown"))
            else:
                label = str(cluster)
            counter[label] += 1

    return {
        "cluster_map": dict(counter),
        "peers": [peer.slug for peer in peers],
        "peer_count": len(peers),
    }
