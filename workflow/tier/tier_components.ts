import { TierEngine } from "./tier_integration"
import { TierFeature, TierKey } from "./tier_types"

/**
 * TierAwareComponent
 * The semantic rendering contract for all UI components.
 *
 * Every component must implement:
 * - renderNovice()
 * - renderIntermediate()
 * - renderAdvanced()
 * - renderVeteran()
 *
 * The TierEngine determines which version to render.
 */

export abstract class TierAwareComponent {
  tier: TierKey

  constructor(tier: TierKey) {
    this.tier = tier
  }

  /**
   * Main render function.
   * Delegates to tier-specific render methods.
   */
  render() {
    switch (this.tier) {
      case "novice":
        return this.renderNovice()
      case "intermediate":
        return this.renderIntermediate()
      case "advanced":
        return this.renderAdvanced()
      case "veteran":
        return this.renderVeteran()
      default:
        return this.renderNovice()
    }
  }

  /**
   * Tier-specific rendering methods.
   * These MUST be implemented by every component.
   */
  abstract renderNovice(): any
  abstract renderIntermediate(): any
  abstract renderAdvanced(): any
  abstract renderVeteran(): any

  /**
   * Utility: check if a feature is allowed for this tier.
   */
  can(feature: TierFeature) {
    return TierEngine.canRenderFeature(this.tier, feature)
  }

  /**
   * Utility: get full semantic context for this tier.
   * Components can use this to adjust behavior.
   */
  getContext() {
    return TierEngine.getTierContext(this.tier)
  }
}

/**
 * Example: A Tier-Aware Dashboard Component
 * (This is a template for how your real components will behave.)
 */

export class DashboardComponent extends TierAwareComponent {
  renderNovice() {
    return {
      layout: "single_panel",
      controls: ["basic_navigation"],
      semantic: this.getContext().semantic_depth.mlas
    }
  }

  renderIntermediate() {
    return {
      layout: "dual_panel",
      controls: ["basic_navigation", "filters"],
      semantic: this.getContext().semantic_depth.svem
    }
  }

  renderAdvanced() {
    return {
      layout: "multi_panel",
      controls: ["filters", "analysis_tools"],
      semantic: {
        mlas: this.getContext().semantic_depth.mlas,
        svem: this.getContext().semantic_depth.svem,
        cccp: this.getContext().semantic_depth.cccp
      }
    }
  }

  renderVeteran() {
    return {
      layout: "multi_panel_expert",
      controls: ["filters", "analysis_tools", "semantic_debug"],
      semantic: this.getContext().semantic_depth
    }
  }
}
