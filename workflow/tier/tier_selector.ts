import { TierEngine } from "./tier_integration"
import { TierProfiles } from "./tier_profiles"
import { ProfileKey, TierKey } from "./tier_types"

/**
 * TierSelector
 * The semantic controller for tier switching.
 *
 * Responsibilities:
 * - Determine allowed tiers for the current user profile
 * - Validate tier transitions
 * - Update UI state
 * - Trigger re-render of tier-aware components
 * - Enforce enterprise lock-tier rules
 * - Support auto-tier evolution
 * - Support tier preview mode
 */

export class TierSelector {
  profile: ProfileKey
  currentTier: TierKey
  locked: boolean

  constructor(profile: ProfileKey) {
    this.profile = profile
    this.currentTier = TierEngine.getDefaultTier(profile)
    this.locked = TierProfiles[profile].lock_tier || false
  }

  /**
   * Returns the list of tiers the user is allowed to switch to.
   */
  getAllowedTiers() {
    return TierEngine.getAllowedTiers(this.profile)
  }

  /**
   * Returns the current tier.
   */
  getCurrentTier() {
    return this.currentTier
  }

  /**
   * Attempts to switch to a new tier.
   * Validates permissions and lock-tier rules.
   */
  switchTier(targetTier: TierKey) {
    if (this.locked) {
      return {
        success: false,
        reason: "Tier is locked for this profile."
      }
    }

    const allowed = this.getAllowedTiers()

    if (!allowed.includes(targetTier)) {
      return {
        success: false,
        reason: `Tier '${targetTier}' is not allowed for profile '${this.profile}'.`
      }
    }

    this.currentTier = targetTier

    return {
      success: true,
      tier: this.currentTier
    }
  }

  /**
   * Tier Preview Mode
   * Allows the user to preview a tier without committing to it.
   */
  previewTier(targetTier: TierKey) {
    const allowed = this.getAllowedTiers()

    if (!allowed.includes(targetTier)) {
      return {
        success: false,
        reason: `Cannot preview tier '${targetTier}'.`
      }
    }

    return {
      success: true,
      preview: TierEngine.getTierContext(targetTier)
    }
  }

  /**
   * Auto-Tier Evolution
   * Automatically adjusts tier based on usage patterns.
   */
  autoTier(usageScore: number) {
    const allowed = this.getAllowedTiers()

    // Example thresholds (you can tune these later)
    if (usageScore > 90 && allowed.includes("veteran")) {
      this.currentTier = "veteran"
    } else if (usageScore > 70 && allowed.includes("advanced")) {
      this.currentTier = "advanced"
    } else if (usageScore > 40 && allowed.includes("intermediate")) {
      this.currentTier = "intermediate"
    } else {
      this.currentTier = "novice"
    }

    return {
      success: true,
      tier: this.currentTier
    }
  }
}
