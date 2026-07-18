export const TIER_KEYS = ["novice", "intermediate", "advanced", "veteran"] as const
export type TierKey = (typeof TIER_KEYS)[number]

export const PROFILE_KEYS = ["public_free", "personal_free", "enterprise"] as const
export type ProfileKey = (typeof PROFILE_KEYS)[number]

export type TierFeature =
  | "multi_panel"
  | "advanced_controls"
  | "semantic_debug"
  | "expert_tools"

export type TemplateGroup =
  | "dashboard"
  | "interface_public_profile"
  | "interface_personal_profile"
  | "interface_corporation"
  | "interface_museum"
  | "interface_garden"
  | "storytelling_dashboard"
  | "workflow_dashboard"
  | "semantic_debugger"
  | "btpe_visualizer"

export type SemanticExposureLevel = "none" | "basic" | "full"

export interface TierDefinition {
  id: TierKey
  label: string
  description: string
  complexity: number
}

export interface TierCapability {
  tier: TierKey
  ui_density: string
  workflow_depth: number
  semantic_exposure: {
    mlas: SemanticExposureLevel
    svem: SemanticExposureLevel
    cccp: SemanticExposureLevel
    dchd: SemanticExposureLevel
  }
  btpe_depth: number
  routing_complexity: string
  error_tolerance: string
  cognitive_load: string
  component_rules: {
    allow_multi_panel: boolean
    allow_advanced_controls: boolean
    allow_semantic_debug: boolean
    allow_expert_tools: boolean
    allowed_template_groups: TemplateGroup[]
  }
  interface_rules: {
    allow_interface_expansion: boolean
    allow_compartment_crossing: boolean
  }
}

export interface TierProfileDefinition {
  id: ProfileKey
  default: TierKey
  allowed: TierKey[]
  lock_tier: boolean
  conditions: Record<string, boolean>
}