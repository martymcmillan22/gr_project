import { TemplateGroup, TierKey } from "../../workflow/tier/tier_types"
import { TierEngine } from "../../workflow/tier/tier_integration"

// Canonical list of all template groups.
export const TEMPLATE_GROUPS: TemplateGroup[] = [
  "dashboard",
  "interface_public_profile",
  "interface_personal_profile",
  "interface_corporation",
  "interface_museum",
  "interface_garden",
  "storytelling_dashboard",
  "workflow_dashboard",
  "semantic_debugger",
  "btpe_visualizer",
]

// Per-tier mapping (TierEngine is the source of truth).
export function getTemplateGroupsForTier(tier: TierKey): TemplateGroup[] {
  const ctx = TierEngine.getTierContext(tier)
  return ctx.component_rules.allowed_template_groups
}

// Per-interface mapping.
export const INTERFACE_TEMPLATE_GROUPS: Record<string, TemplateGroup[]> = {
  diagnostics: ["semantic_debugger"],
  public_profile: ["interface_public_profile"],
  personal_profile: ["interface_personal_profile"],
  corporation: ["interface_corporation"],
  museum: ["interface_museum"],
  garden: ["interface_garden"],
  storytelling: ["storytelling_dashboard"],
}

// Per-workflow mapping.
export const WORKFLOW_TEMPLATE_GROUPS: Record<string, TemplateGroup[]> = {
  basic_navigation: ["dashboard"],
  guided_creation: ["dashboard"],
  advanced_authoring: ["workflow_dashboard"],
  semantic_debugging: ["semantic_debugger", "btpe_visualizer"],
}

// Per-storytelling mode mapping.
export const STORYTELLING_TEMPLATE_GROUPS: Record<string, TemplateGroup[]> = {
  basic_story: ["storytelling_dashboard"],
  guided_story: ["storytelling_dashboard"],
  advanced_story: ["storytelling_dashboard"],
  semantic_story: ["semantic_debugger", "btpe_visualizer"],
}

// Safe lookup helpers.
export function isValidTemplateGroup(group: string): group is TemplateGroup {
  return TEMPLATE_GROUPS.includes(group as TemplateGroup)
}

export function getGroupsForInterface(interfaceId: string): TemplateGroup[] {
  return INTERFACE_TEMPLATE_GROUPS[interfaceId] ?? []
}

export function getGroupsForWorkflow(workflowId: string): TemplateGroup[] {
  return WORKFLOW_TEMPLATE_GROUPS[workflowId] ?? []
}

export function getGroupsForStorytelling(mode: string): TemplateGroup[] {
  return STORYTELLING_TEMPLATE_GROUPS[mode] ?? []
}
