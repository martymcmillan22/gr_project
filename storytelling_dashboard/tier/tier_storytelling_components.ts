import { TierKey } from "../../workflow/tier/tier_types"

export interface StorytellingComponentSet {
	tier: TierKey
	components: string[]
}

export function getStorytellingComponents(tier: TierKey): StorytellingComponentSet {
	const components: string[] = ["story_title", "story_body"]

	if (tier === "intermediate" || tier === "advanced" || tier === "veteran") {
		components.push("story_outline")
	}

	if (tier === "advanced" || tier === "veteran") {
		components.push("story_semantic_map")
	}

	if (tier === "veteran") {
		components.push("story_btpe_debug")
	}

	return {
		tier,
		components,
	}
}
