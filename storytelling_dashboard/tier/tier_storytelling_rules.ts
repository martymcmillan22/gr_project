import { TierEngine } from "../../workflow/tier/tier_integration"
import { TierKey } from "../../workflow/tier/tier_types"

export type StorytellingMode =
	| "basic_story"
	| "guided_story"
	| "advanced_story"
	| "semantic_story"

export interface StorytellingRules {
	id: StorytellingMode
	tier: TierKey
	semantic_depth: ReturnType<typeof TierEngine.getTierContext>["semantic_depth"]
	routing_complexity: string
	btpe_depth: number
	allowed_interfaces: string[]
	allowed_compartments: number[]
}

function buildAllowedInterfaces(tier: TierKey): string[] {
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

export function getStorytellingRules(tier: TierKey): StorytellingRules[] {
	const ctx = TierEngine.getTierContext(tier)

	const base: Omit<StorytellingRules, "id"> = {
		tier,
		semantic_depth: ctx.semantic_depth,
		routing_complexity: ctx.routing_complexity,
		btpe_depth: ctx.btpe_depth,
		allowed_interfaces: buildAllowedInterfaces(tier),
		allowed_compartments: buildAllowedCompartments(tier),
	}

	const modes: StorytellingRules[] = [
		{ ...base, id: "basic_story" },
		{ ...base, id: "guided_story" },
	]

	if (tier === "advanced" || tier === "veteran") {
		modes.push({ ...base, id: "advanced_story" })
	}

	if (tier === "veteran") {
		modes.push({ ...base, id: "semantic_story" })
	}

	return modes
}
