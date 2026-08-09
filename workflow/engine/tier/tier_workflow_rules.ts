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

export type WorkflowCompartmentPhase =
	| "Ideas"
	| "Seeds"
	| "Projects"
	| "MVP"
	| "Enterprise"
	| "Studio"

export const CANONICAL_COMPARTMENT_MAX = 16
export const EXTENDED_COMPARTMENT_MAX = 24

export const WORKFLOW_PHASE_RANGES: Array<{
	phase: WorkflowCompartmentPhase
	start: number
	end: number
}> = [
	{ phase: "Ideas", start: 1, end: 4 },
	{ phase: "Seeds", start: 5, end: 8 },
	{ phase: "Projects", start: 9, end: 12 },
	{ phase: "MVP", start: 13, end: 16 },
	{ phase: "Studio", start: 17, end: 20 },
	{ phase: "Enterprise", start: 21, end: 24 },
]

export function resolveWorkflowCompartmentPhase(compartmentId: number): WorkflowCompartmentPhase | null {
	const range = WORKFLOW_PHASE_RANGES.find(
		(item) => compartmentId >= item.start && compartmentId <= item.end,
	)
	return range ? range.phase : null
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
	const max = TierEngine.canCrossCompartments(tier) ? EXTENDED_COMPARTMENT_MAX : 6
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
