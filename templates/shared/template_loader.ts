import { TemplateGroup, TierKey } from "../../workflow/tier/tier_types"
import {
  TEMPLATE_GROUPS,
  getTemplateGroupsForTier,
  isValidTemplateGroup,
} from "../tier/template_group_registry"

export const TEMPLATE_BASE_PATHS: TemplateGroup[] = TEMPLATE_GROUPS

export type TemplateBasePath = TemplateGroup

interface TemplateLoadOptions {
  bypassTierCheck?: boolean
}

export class TemplateLoader {
  static async load(group: TemplateBasePath, tier: TierKey, options: TemplateLoadOptions = {}) {
    if (!isValidTemplateGroup(group)) {
      console.warn(`[TemplateLoader] Invalid template group: ${group}`)
      return this.safeFallback(tier)
    }

    const allowed = getTemplateGroupsForTier(tier)
    if (!options.bypassTierCheck && !allowed.includes(group)) {
      console.warn(
        `[TemplateLoader] Template group '${group}' not allowed for tier '${tier}'`
      )
      return this.safeFallback(tier)
    }

    try {
      return await import(`../${group}/template.${tier}.mdx`)
    } catch (err) {
      console.error(`[TemplateLoader] Failed to load template group '${group}' for tier '${tier}'`, err)
      return this.safeFallback(tier)
    }
  }

  static async safeFallback(tier: TierKey) {
    const fallbackGroup: TemplateGroup = "dashboard"

    try {
      return await import(`../${fallbackGroup}/template.${tier}.mdx`)
    } catch (err) {
      console.error(`[TemplateLoader] Fallback template missing for tier '${tier}'`, err)
      return null
    }
  }

  static getMetadata(tier: TierKey) {
    return {
      tier,
      allowed_groups: getTemplateGroupsForTier(tier),
      all_groups: TEMPLATE_GROUPS,
    }
  }
}
