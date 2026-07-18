import { TierEngine } from "../../workflow/tier/tier_integration"
import { TemplateGroup, TierKey } from "../../workflow/tier/tier_types"
import {
	INTERFACE_TEMPLATE_GROUPS,
	TEMPLATE_GROUPS,
	getTemplateGroupsForTier,
} from "./template_group_registry"

export type UIMode =
	| "ui_basic"
	| "ui_guided"
	| "ui_advanced"
	| "ui_semantic"
	| "ui_diagnostics"

export interface UIRules {
	id: UIMode
	tier: TierKey
	ui_depth: ReturnType<typeof TierEngine.getTierContext>["semantic_depth"]
	ui_complexity: string
	allowed_template_groups: TemplateGroup[]
	allowed_interfaces: string[]
	all_template_groups: TemplateGroup[]
}

function buildAllowedInterfaces(allowedGroups: TemplateGroup[]): string[] {
	return Object.entries(INTERFACE_TEMPLATE_GROUPS)
		.filter(([, groups]) => groups.some((group) => allowedGroups.includes(group)))
		.map(([interfaceId]) => interfaceId)
}

export function getUIRules(tier: TierKey): UIRules[] {
	const ctx = TierEngine.getTierContext(tier)
	const allowedGroups = getTemplateGroupsForTier(tier)

	const base: Omit<UIRules, "id"> = {
		tier,
		ui_depth: ctx.semantic_depth,
		ui_complexity: ctx.routing_complexity,
		allowed_template_groups: allowedGroups,
		allowed_interfaces: buildAllowedInterfaces(allowedGroups),
		all_template_groups: TEMPLATE_GROUPS,
	}

	const modes: UIRules[] = [
		{ ...base, id: "ui_basic" },
		{ ...base, id: "ui_guided" },
	]

	if (tier === "advanced" || tier === "veteran") {
		modes.push({ ...base, id: "ui_advanced" })
	}

	if (tier === "veteran") {
		modes.push({ ...base, id: "ui_semantic" })
	}

	modes.push({
		...base,
		id: "ui_diagnostics",
		allowed_template_groups: ["semantic_debugger"],
		allowed_interfaces: ["diagnostics"],
	})

	return modes
}
