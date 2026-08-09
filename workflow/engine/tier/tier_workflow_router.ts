import { TierKey } from "../../tier/tier_types"
import { getWorkflowById } from "./tier_workflow_map"
import {
	InterfaceId,
	resolveWorkflowCompartmentPhase,
	WorkflowCompartmentPhase,
	WorkflowId,
	WorkflowRules,
} from "./tier_workflow_rules"

export interface WorkflowRouteInput {
	tier: TierKey
	interfaceId: string
	compartmentId: number
	timelineState?: {
		completed_slots?: number[]
		phase_gates?: Array<{
			phase?: WorkflowCompartmentPhase | string
			locked?: boolean
		}>
	}
}

export interface WorkflowRouteResult {
	workflow: WorkflowId | null
	tier: TierKey
	interfaceId: string
	compartmentId: number
	error?: boolean
	reason?: string
}

function isGateLockedForCompartment(
	compartmentId: number,
	phaseGates: Array<{ phase?: WorkflowCompartmentPhase | string; locked?: boolean }>,
): boolean {
	const phase = resolveWorkflowCompartmentPhase(compartmentId)
	if (!phase) {
		return false
	}
	const gate = phaseGates.find((item) => String(item?.phase || "") === phase)
	return gate ? Boolean(gate.locked) : false
}

function isWorkflowError(
	value: WorkflowRules | null | { error: boolean; reason: string }
): value is { error: boolean; reason: string } {
	return !!value && typeof value === "object" && "error" in value
}

export function routeWorkflow(input: WorkflowRouteInput): WorkflowRouteResult {
	const { tier, interfaceId, compartmentId, timelineState } = input

	let workflow: WorkflowId | null = "basic_navigation"

	if (tier === "intermediate" || tier === "advanced") {
		workflow = "guided_creation"
	}

	if (tier === "advanced" && compartmentId > 16) {
		workflow = "advanced_authoring"
	}

	if (tier === "veteran") {
		workflow = "semantic_debugging"
	}

	const phaseGates = Array.isArray(timelineState?.phase_gates) ? timelineState.phase_gates : []
	const resolvedPhase = resolveWorkflowCompartmentPhase(compartmentId)
	if (phaseGates.length > 0 && isGateLockedForCompartment(compartmentId, phaseGates)) {
		return {
			workflow,
			tier,
			interfaceId,
			compartmentId,
			error: true,
			reason: `Timeline phase gate is locked for ${resolvedPhase || "Unassigned"} compartment routing.`,
		}
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
