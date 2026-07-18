import { TierKey } from "../../tier/tier_types"
import { getWorkflowById } from "./tier_workflow_map"
import { InterfaceId, WorkflowId, WorkflowRules } from "./tier_workflow_rules"

export interface WorkflowRouteInput {
	tier: TierKey
	interfaceId: string
	compartmentId: number
}

export interface WorkflowRouteResult {
	workflow: WorkflowId | null
	tier: TierKey
	interfaceId: string
	compartmentId: number
	error?: boolean
	reason?: string
}

function isWorkflowError(
	value: WorkflowRules | null | { error: boolean; reason: string }
): value is { error: boolean; reason: string } {
	return !!value && typeof value === "object" && "error" in value
}

export function routeWorkflow(input: WorkflowRouteInput): WorkflowRouteResult {
	const { tier, interfaceId, compartmentId } = input

	let workflow: WorkflowId | null = "basic_navigation"

	if (tier === "intermediate" || tier === "advanced") {
		workflow = "guided_creation"
	}

	if (tier === "advanced" && compartmentId > 12) {
		workflow = "advanced_authoring"
	}

	if (tier === "veteran") {
		workflow = "semantic_debugging"
	}

	const rules = workflow ? getWorkflowById(workflow, tier) : null

	if (!rules || isWorkflowError(rules)) {
		return {
			workflow,
			tier,
			interfaceId,
			compartmentId,
			error: true,
			reason: rules && isWorkflowError(rules)
				? rules.reason
				: "No valid workflow rules found for this tier.",
		}
	}

	const allowedInterface = rules.allowed_interfaces.includes(interfaceId as InterfaceId)
	const allowedCompartment = rules.allowed_compartments.includes(compartmentId)

	if (!allowedInterface || !allowedCompartment) {
		return {
			workflow,
			tier,
			interfaceId,
			compartmentId,
			error: true,
			reason: "Input is outside allowed interface or compartment scope for this workflow/tier.",
		}
	}

	return {
		workflow,
		tier,
		interfaceId,
		compartmentId,
	}
}
