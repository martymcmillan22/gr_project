import { TierKey } from "../../workflow/tier/tier_types"
import { TemplateLoader } from "../shared/template_loader"

import {
  getGroupsForInterface,
  getGroupsForStorytelling,
  getGroupsForWorkflow,
  getTemplateGroupsForTier,
  isValidTemplateGroup,
} from "./template_group_registry"

export interface TemplateGroupInspector {
  tier: TierKey
  allowed_groups: string[]
  all_groups: string[]
  interface_groups: Record<string, string[]>
  workflow_groups: Record<string, string[]>
  storytelling_groups: Record<string, string[]>
  validateGroup: (group: string) => boolean
  getGroupInfo: (group: string) => {
    valid: boolean
    allowed_for_tier: boolean
    interfaces: string[]
    workflows: string[]
    storytelling_modes: string[]
  }
}

export function createTemplateGroupInspector(tier: TierKey): TemplateGroupInspector {
  const metadata = TemplateLoader.getMetadata(tier)
  const allowed = getTemplateGroupsForTier(tier)

  return {
    tier,
    allowed_groups: metadata.allowed_groups,
    all_groups: metadata.all_groups,

    interface_groups: {
      diagnostics: getGroupsForInterface("diagnostics"),
      public_profile: getGroupsForInterface("public_profile"),
      personal_profile: getGroupsForInterface("personal_profile"),
      corporation: getGroupsForInterface("corporation"),
      museum: getGroupsForInterface("museum"),
      garden: getGroupsForInterface("garden"),
      storytelling: getGroupsForInterface("storytelling"),
    },

    workflow_groups: {
      basic_navigation: getGroupsForWorkflow("basic_navigation"),
      guided_creation: getGroupsForWorkflow("guided_creation"),
      advanced_authoring: getGroupsForWorkflow("advanced_authoring"),
      semantic_debugging: getGroupsForWorkflow("semantic_debugging"),
    },

    storytelling_groups: {
      basic_story: getGroupsForStorytelling("basic_story"),
      guided_story: getGroupsForStorytelling("guided_story"),
      advanced_story: getGroupsForStorytelling("advanced_story"),
      semantic_story: getGroupsForStorytelling("semantic_story"),
    },

    validateGroup: (group: string) => {
      return isValidTemplateGroup(group) && allowed.includes(group)
    },

    getGroupInfo: (group: string) => {
      const valid = isValidTemplateGroup(group)
      const allowed_for_tier = allowed.includes(group)

      const interfaces = Object.entries({
        diagnostics: getGroupsForInterface("diagnostics"),
        public_profile: getGroupsForInterface("public_profile"),
        personal_profile: getGroupsForInterface("personal_profile"),
        corporation: getGroupsForInterface("corporation"),
        museum: getGroupsForInterface("museum"),
        garden: getGroupsForInterface("garden"),
        storytelling: getGroupsForInterface("storytelling"),
      })
        .filter(([, groups]) => groups.includes(group))
        .map(([key]) => key)

      const workflows = Object.entries({
        basic_navigation: getGroupsForWorkflow("basic_navigation"),
        guided_creation: getGroupsForWorkflow("guided_creation"),
        advanced_authoring: getGroupsForWorkflow("advanced_authoring"),
        semantic_debugging: getGroupsForWorkflow("semantic_debugging"),
      })
        .filter(([, groups]) => groups.includes(group))
        .map(([key]) => key)

      const storytelling_modes = Object.entries({
        basic_story: getGroupsForStorytelling("basic_story"),
        guided_story: getGroupsForStorytelling("guided_story"),
        advanced_story: getGroupsForStorytelling("advanced_story"),
        semantic_story: getGroupsForStorytelling("semantic_story"),
      })
        .filter(([, groups]) => groups.includes(group))
        .map(([key]) => key)

      return {
        valid,
        allowed_for_tier,
        interfaces,
        workflows,
        storytelling_modes,
      }
    },
  }
}
