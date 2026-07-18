import { TierKey } from "../../workflow/tier/tier_types"

import {
	getStorytellingRules,
	StorytellingRules,
	StorytellingMode,
} from "./tier_storytelling_rules"
import {
	getStorytellingComponents,
	StorytellingComponentSet,
} from "./tier_storytelling_components"

export interface StorytellingBundle {
	rules: StorytellingRules | null
	components: StorytellingComponentSet
}

export const StorytellingMap: Partial<Record<StorytellingMode, (tier: TierKey) => StorytellingBundle>> = {
	basic_story: (tier) => ({
		rules: getStorytellingRules(tier).find((r) => r.id === "basic_story") ?? null,
		components: getStorytellingComponents(tier),
	}),
	guided_story: (tier) => ({
		rules: getStorytellingRules(tier).find((r) => r.id === "guided_story") ?? null,
		components: getStorytellingComponents(tier),
	}),
	advanced_story: (tier) => ({
		rules: getStorytellingRules(tier).find((r) => r.id === "advanced_story") ?? null,
		components: getStorytellingComponents(tier),
	}),
	semantic_story: (tier) => ({
		rules: getStorytellingRules(tier).find((r) => r.id === "semantic_story") ?? null,
		components: getStorytellingComponents(tier),
	}),
}

export function getStorytellingBundle(mode: StorytellingMode, tier: TierKey): StorytellingBundle {
	const fn = StorytellingMap[mode]

	if (!fn) {
		return {
			rules: null,
			components: getStorytellingComponents(tier),
		}
	}

	return fn(tier)
}
