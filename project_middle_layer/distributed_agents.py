from __future__ import annotations

from project_middle_layer.insights import build_semantic_insights
from project_middle_layer.models import DistributedAgentRun, ReplicationConfig, SemanticShard


DISTRIBUTED_AGENT_NAMES = [
    "Global Drift Agent",
    "Global Stability Agent",
    "Federated Lineage Agent",
    "Shard Health Agent",
]


def run_distributed_agent(agent_name: str) -> DistributedAgentRun:
    if agent_name not in DISTRIBUTED_AGENT_NAMES:
        raise ValueError(f"Unknown distributed agent: {agent_name}")

    nodes = list(ReplicationConfig.objects.filter(is_active=True)[:100])
    shards = list(SemanticShard.objects.filter(is_active=True)[:200])
    insights = build_semantic_insights(limit=10)

    metrics = {
        "active_nodes": len(nodes),
        "active_shards": len(shards),
        "average_shard_health": round(sum(item.health_score for item in shards) / len(shards), 2) if shards else 0.0,
    }

    return DistributedAgentRun.objects.create(
        agent_name=agent_name,
        node_count=len(nodes),
        shard_count=len(shards),
        status="completed",
        metrics=metrics,
        insights=insights,
    )
