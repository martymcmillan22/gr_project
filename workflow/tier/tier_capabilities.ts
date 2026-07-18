import { UITiers } from "./tier_registry"
import { TierCapability, TierKey } from "./tier_types"

export const TierCapabilities: Record<TierKey, TierCapability> = {
  novice: {
    tier: UITiers.novice.id,
    ui_density: "minimal",
    workflow_depth: 1,
    semantic_exposure: {
      mlas: "basic",
      svem: "none",
      cccp: "none",
      dchd: "none"
    },
    btpe_depth: 1,
    routing_complexity: "linear",
    error_tolerance: "high",
    cognitive_load: "low",
    component_rules: {
      allow_multi_panel: false,
      allow_advanced_controls: false,
      allow_semantic_debug: false,
      allow_expert_tools: false,
      allowed_template_groups: [
        "dashboard",
        "interface_public_profile",
        "interface_personal_profile"
      ]
    },
    interface_rules: {
      allow_interface_expansion: false,
      allow_compartment_crossing: false
    }
  },

  intermediate: {
    tier: UITiers.intermediate.id,
    ui_density: "moderate",
    workflow_depth: 2,
    semantic_exposure: {
      mlas: "full",
      svem: "basic",
      cccp: "none",
      dchd: "none"
    },
    btpe_depth: 2,
    routing_complexity: "branching",
    error_tolerance: "medium",
    cognitive_load: "medium",
    component_rules: {
      allow_multi_panel: true,
      allow_advanced_controls: false,
      allow_semantic_debug: false,
      allow_expert_tools: false,
      allowed_template_groups: [
        "dashboard",
        "interface_public_profile",
        "interface_personal_profile",
        "interface_corporation",
        "interface_museum",
        "interface_garden"
      ]
    },
    interface_rules: {
      allow_interface_expansion: true,
      allow_compartment_crossing: false
    }
  },

  advanced: {
    tier: UITiers.advanced.id,
    ui_density: "high",
    workflow_depth: 3,
    semantic_exposure: {
      mlas: "full",
      svem: "full",
      cccp: "basic",
      dchd: "none"
    },
    btpe_depth: 3,
    routing_complexity: "multi-branch",
    error_tolerance: "low",
    cognitive_load: "high",
    component_rules: {
      allow_multi_panel: true,
      allow_advanced_controls: true,
      allow_semantic_debug: false,
      allow_expert_tools: false,
      allowed_template_groups: [
        "dashboard",
        "interface_public_profile",
        "interface_personal_profile",
        "interface_corporation",
        "interface_museum",
        "interface_garden",
        "storytelling_dashboard",
        "workflow_dashboard"
      ]
    },
    interface_rules: {
      allow_interface_expansion: true,
      allow_compartment_crossing: true
    }
  },

  veteran: {
    tier: UITiers.veteran.id,
    ui_density: "maximal",
    workflow_depth: 4,
    semantic_exposure: {
      mlas: "full",
      svem: "full",
      cccp: "full",
      dchd: "full"
    },
    btpe_depth: 4,
    routing_complexity: "semantic-graph",
    error_tolerance: "strict",
    cognitive_load: "expert",
    component_rules: {
      allow_multi_panel: true,
      allow_advanced_controls: true,
      allow_semantic_debug: true,
      allow_expert_tools: true,
      allowed_template_groups: [
        "dashboard",
        "interface_public_profile",
        "interface_personal_profile",
        "interface_corporation",
        "interface_museum",
        "interface_garden",
        "storytelling_dashboard",
        "workflow_dashboard",
        "semantic_debugger",
        "btpe_visualizer"
      ]
    },
    interface_rules: {
      allow_interface_expansion: true,
      allow_compartment_crossing: true
    }
  }
}
