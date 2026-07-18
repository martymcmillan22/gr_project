import { TierEngine } from "../../tier/tier_integration"
import { TierKey } from "../../tier/tier_types"

export type WorkflowId =
	| "basic_navigation"
	| "guided_creation"
	| "advanced_authoring"
	| "semantic_debugging"

export type InterfaceId =
	| "corporation"
	| "museum"
	| "garden"
	| "public_profile"
	| "personal_profile"
	| "storytelling"

export interface WorkflowRules {
	id: WorkflowId
	tier: TierKey
	semantic_depth: ReturnType<typeof TierEngine.getTierContext>["semantic_depth"]
	routing_complexity: string
	btpe_depth: number
	allowed_interfaces: InterfaceId[]
	allowed_compartments: number[]
}

function buildAllowedInterfaces(tier: TierKey): InterfaceId[] {
	if (!TierEngine.canExpandInterface(tier)) {
		return ["public_profile", "personal_profile", "storytelling"]
	}

	return [
		"corporation",
		"museum",
		"garden",
		"public_profile",
		"personal_profile",
		"storytelling",
	]
}

function buildAllowedCompartments(tier: TierKey): number[] {
	const max = TierEngine.canCrossCompartments(tier) ? 24 : 6
	return Array.from({ length: max }, (_, idx) => idx + 1)
}

export function getWorkflowRules(tier: TierKey): WorkflowRules[] {
	const ctx = TierEngine.getTierContext(tier)

	const base: Omit<WorkflowRules, "id"> = {
		tier,
		semantic_depth: ctx.semantic_depth,
		routing_complexity: ctx.routing_complexity,
		btpe_depth: ctx.btpe_depth,
		allowed_interfaces: buildAllowedInterfaces(tier),
		allowed_compartments: buildAllowedCompartments(tier),
	}

	const workflows: WorkflowRules[] = [
		{
			...base,
			id: "basic_navigation",
		},
		{
			...base,
			id: "guided_creation",
		},
	]

	if (tier === "advanced" || tier === "veteran") {
		workflows.push({
			...base,
			id: "advanced_authoring",
		})
	}

	if (tier === "veteran") {
		workflows.push({
			...base,
			id: "semantic_debugging",
		})
	}

	return workflows
}
