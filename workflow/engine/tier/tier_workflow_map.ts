import { TierKey } from "../../tier/tier_types"
import { getWorkflowRules, WorkflowId, WorkflowRules } from "./tier_workflow_rules"

export const WorkflowMap: Partial<Record<WorkflowId, (tier: TierKey) => WorkflowRules | null>> = {
	basic_navigation: (tier) => getWorkflowRules(tier).find((w) => w.id === "basic_navigation") ?? null,
	guided_creation: (tier) => getWorkflowRules(tier).find((w) => w.id === "guided_creation") ?? null,
	advanced_authoring: (tier) => getWorkflowRules(tier).find((w) => w.id === "advanced_authoring") ?? null,
	semantic_debugging: (tier) => getWorkflowRules(tier).find((w) => w.id === "semantic_debugging") ?? null,
}

export function getWorkflowById(id: WorkflowId, tier: TierKey) {
	const fn = WorkflowMap[id]

	if (!fn) {
		return {
			error: true,
			reason: `Invalid workflow ID: ${id}`,
			id,
			tier,
		}
	}

	return fn(tier)
}
