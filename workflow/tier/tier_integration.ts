import { UITiers } from "./tier_registry"
import { TierCapabilities } from "./tier_capabilities"
import { TierProfiles } from "./tier_profiles"
import { ProfileKey, TierFeature, TierKey } from "./tier_types"

/**
 * TierEngine
 * The semantic integration layer that unifies:
 * - Tier Registry
 * - Tier Capabilities
 * - Tier Profiles
 * - Tier State
 * - Tier Validation
 * - Tier Transition Logic
 */

export const TierEngine = {
  /**
   * Returns the canonical tier definition (Novice, Intermediate, Advanced, Veteran)
   */
  getTierDefinition(tier: TierKey) {
    return UITiers[tier]
  },

  /**
   * Returns the capability map for the given tier
   */
  getTierCapabilities(tier: TierKey) {
    return TierCapabilities[tier]
  },

  /**
   * Returns the allowed tiers for a given user profile
   * (public_free, personal_free, enterprise)
   */
  getAllowedTiers(profile: ProfileKey) {
    return TierProfiles[profile].allowed
  },

  /**
   * Returns the default tier for a given user profile
   */
  getDefaultTier(profile: ProfileKey): TierKey {
    return TierProfiles[profile].default as TierKey
  },

  /**
   * Validates whether a tier transition is allowed
   */
  validateTierTransition(profile: ProfileKey, targetTier: TierKey) {
    const allowed = TierProfiles[profile].allowed
    return allowed.includes(targetTier)
  },

  /**
   * Returns a merged semantic context object for the given tier
   * This is the core of the Tier Engine.
   */
  getTierContext(tier: TierKey) {
    return {
      definition: UITiers[tier],
      capabilities: TierCapabilities[tier],
      semantic_depth: {
        mlas: TierCapabilities[tier].semantic_exposure.mlas,
        svem: TierCapabilities[tier].semantic_exposure.svem,
        cccp: TierCapabilities[tier].semantic_exposure.cccp,
        dchd: TierCapabilities[tier].semantic_exposure.dchd
      },
      btpe_depth: TierCapabilities[tier].btpe_depth,
      routing_complexity: TierCapabilities[tier].routing_complexity,
      component_rules: TierCapabilities[tier].component_rules,
      interface_rules: TierCapabilities[tier].interface_rules
    }
  },

  /**
   * Determines whether a component is allowed to render a specific feature
   * based on tier capability rules.
   */
  canRenderFeature(tier: TierKey, feature: TierFeature) {
    const capabilities = TierCapabilities[tier]

    switch (feature) {
      case "multi_panel":
        return capabilities.component_rules.allow_multi_panel
      case "advanced_controls":
        return capabilities.component_rules.allow_advanced_controls
      case "semantic_debug":
        return capabilities.component_rules.allow_semantic_debug
      case "expert_tools":
        return capabilities.component_rules.allow_expert_tools
      default:
        return false
    }
  },

  /**
   * Determines whether a tier allows interface expansion or compartment crossing.
   */
  canExpandInterface(tier: TierKey) {
    return TierCapabilities[tier].interface_rules.allow_interface_expansion
  },

  canCrossCompartments(tier: TierKey) {
    return TierCapabilities[tier].interface_rules.allow_compartment_crossing
  }
}
