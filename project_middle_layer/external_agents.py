from __future__ import annotations

from project_middle_layer.models import ExternalAgent


def register_external_agent(payload: dict[str, object]) -> ExternalAgent:
    slug = str(payload.get("slug") or "").strip()
    if not slug:
        raise ValueError("External agent slug is required.")

    agent, _ = ExternalAgent.objects.update_or_create(
        slug=slug,
        defaults={
            "name": str(payload.get("name") or slug),
            "endpoint": str(payload.get("endpoint") or ""),
            "capabilities": payload.get("capabilities", []) if isinstance(payload.get("capabilities", []), list) else [],
            "auth_token": str(payload.get("auth_token") or ""),
            "status": str(payload.get("status") or "active"),
            "metadata": payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {},
        },
    )
    return agent


def external_agent_capability_negotiation(agent: ExternalAgent) -> dict[str, object]:
    capabilities = [str(item).strip().lower() for item in (agent.capabilities or [])]
    return {
        "agent_slug": agent.slug,
        "capabilities": capabilities,
        "status": agent.status,
    }


def run_external_agent(*, agent_slug: str, operation: str, payload: dict[str, object]) -> dict[str, object]:
    agent = ExternalAgent.objects.filter(slug=agent_slug, status="active").first()
    if not agent:
        raise ValueError("Active external agent not found.")

    negotiated = external_agent_capability_negotiation(agent)
    operation_key = str(operation or "").strip().lower()
    if operation_key and operation_key not in negotiated["capabilities"]:
        raise ValueError("External agent does not expose requested capability.")

    # Deterministic local simulation for secure execution/sandbox behavior.
    return {
        "agent_slug": agent.slug,
        "operation": operation_key,
        "sandboxed": True,
        "status": "completed",
        "result": {
            "echo": payload,
            "capabilities": negotiated["capabilities"],
        },
    }
