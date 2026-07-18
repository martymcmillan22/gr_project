import { TierKey } from "../../workflow/tier/tier_types"
import { TemplateBasePath } from "../shared/template_loader"
import { getUIBundle } from "./tier_ui_map"
import { UIMode } from "./tier_ui_rules"

export interface UIRouteInput {
	tier: TierKey
	interfaceId: string
	templateGroup: string
}

export interface UIRouteResult {
	mode: UIMode | null
	tier: TierKey
	interfaceId: string
	templateGroup: string
	error?: boolean
	reason?: string
}

export function routeUI(input: UIRouteInput): UIRouteResult {
	const { tier, interfaceId, templateGroup } = input

	let mode: UIMode | null = "ui_basic"

	if (interfaceId === "diagnostics" || templateGroup === "semantic_debugger") {
		mode = "ui_diagnostics"
	}

	if (mode !== "ui_diagnostics" && tier === "intermediate") {
		mode = "ui_guided"
	}

	if (mode !== "ui_diagnostics" && tier === "advanced") {
		mode = "ui_advanced"
	}

	if (mode !== "ui_diagnostics" && tier === "veteran") {
		mode = "ui_semantic"
	}

	const bundle = mode ? getUIBundle(mode, tier) : null

	if (!bundle || !bundle.rules) {
		return {
			mode,
			tier,
			interfaceId,
			templateGroup,
			error: true,
			reason: "No valid UI rules found for this tier.",
		}
	}

	const interfaceAllowed = bundle.rules.allowed_interfaces.includes(interfaceId)
	const templateAllowed = bundle.rules.allowed_template_groups.includes(
		templateGroup as TemplateBasePath
	)

	if (!interfaceAllowed || !templateAllowed) {
		return {
			mode,
			tier,
			interfaceId,
			templateGroup,
			error: true,
			reason: "Interface or template group is not allowed for this tier.",
		}
	}

	return {
		mode,
		tier,
		interfaceId,
		templateGroup,
	}
}
