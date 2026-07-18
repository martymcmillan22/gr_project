import { TierKey } from "../../workflow/tier/tier_types"

import { getUIRules, UIRules, UIMode } from "./tier_ui_rules"
import { getUIComponents, UIComponentSet } from "./tier_ui_components"

export interface UIBundle {
	rules: UIRules | null
	components: UIComponentSet
}

export const UIMap: Partial<Record<UIMode, (tier: TierKey) => UIBundle>> = {
	ui_basic: (tier) => ({
		rules: getUIRules(tier).find((r) => r.id === "ui_basic") ?? null,
		components: getUIComponents(tier),
	}),
	ui_guided: (tier) => ({
		rules: getUIRules(tier).find((r) => r.id === "ui_guided") ?? null,
		components: getUIComponents(tier),
	}),
	ui_advanced: (tier) => ({
		rules: getUIRules(tier).find((r) => r.id === "ui_advanced") ?? null,
		components: getUIComponents(tier),
	}),
	ui_semantic: (tier) => ({
		rules: getUIRules(tier).find((r) => r.id === "ui_semantic") ?? null,
		components: getUIComponents(tier),
	}),
	ui_diagnostics: (tier) => ({
		rules: getUIRules(tier).find((r) => r.id === "ui_diagnostics") ?? null,
		components: getUIComponents(tier),
	}),
}

export function getUIBundle(mode: UIMode, tier: TierKey): UIBundle {
	const fn = UIMap[mode]

	if (!fn) {
		return {
			rules: null,
			components: getUIComponents(tier),
		}
	}

	return fn(tier)
}
