import { TierKey } from "../../workflow/tier/tier_types"
import { TierEngine } from "../../workflow/tier/tier_integration"

export interface UIComponentSet {
	tier: TierKey
	components: string[]
}

export function getUIComponents(tier: TierKey): UIComponentSet {
	const components: string[] = ["ui_header", "ui_footer", "ui_navigation"]

	if (TierEngine.canRenderFeature(tier, "multi_panel")) {
		components.push("ui_sidebar", "ui_context_panel")
	}

	if (TierEngine.canRenderFeature(tier, "advanced_controls")) {
		components.push("ui_semantic_overlay")
	}

	if (TierEngine.canRenderFeature(tier, "semantic_debug")) {
		components.push("ui_btpe_debug_panel")
	}

	return {
		tier,
		components,
	}
}
