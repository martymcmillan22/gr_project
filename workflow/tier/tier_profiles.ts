import { UITiers } from "./tier_registry"
import { ProfileKey, TierProfileDefinition } from "./tier_types"

/**
 * TierProfiles
 * Identity-based tier permissions for BaseTrue.
 *
 * Profiles:
 * - public_free
 * - personal_free
 * - enterprise
 *
 * Each profile defines:
 * - default tier
 * - allowed tiers
 * - lock-tier rules
 * - conditional unlock rules
 */

export const TierProfiles: Record<ProfileKey, TierProfileDefinition> = {
  /**
   * Free Public
   * For nonprofits, public servants, community orgs, civic workflows.
   *
   * Intent:
   * - Maximum simplicity
   * - Minimal cognitive load
   * - No advanced or veteran exposure
   */
  public_free: {
    id: "public_free",
    default: UITiers.novice.id,
    allowed: [UITiers.novice.id, UITiers.intermediate.id],
    lock_tier: false,
    conditions: {}
  },

  /**
   * Free Personal
   * For individuals, students, creators, freelancers, small businesses.
   *
   * Intent:
   * - Start simple
   * - Allow growth
   * - Unlock advanced only when needed
   */
  personal_free: {
    id: "personal_free",
    default: UITiers.novice.id,
    allowed: [
      UITiers.novice.id,
      UITiers.intermediate.id,
      UITiers.advanced.id
    ],
    lock_tier: false,

    /**
     * Conditional unlock:
     * Advanced tier requires a project context
     * (small business, solo entrepreneur, active workflow)
     */
    conditions: {
      advanced_requires_project: true
    }
  },

  /**
   * Enterprise
   * For corporations, institutions, agencies, large teams.
   *
   * Intent:
   * - Provide full semantic depth
   * - Maintain workflow consistency
   * - Allow expert-level tools
   * - Lock tier for compliance and training
   */
  enterprise: {
    id: "enterprise",
    default: UITiers.intermediate.id,
    allowed: [
      UITiers.intermediate.id,
      UITiers.advanced.id,
      UITiers.veteran.id
    ],

    /**
     * Enterprise workflows require consistency.
     * Veteran tier exposes:
     * - MLAS
     * - SVEM
     * - CCCP
     * - DCHD
     */
    lock_tier: true,

    conditions: {
      require_training_for_veteran: true
    }
  }
}
