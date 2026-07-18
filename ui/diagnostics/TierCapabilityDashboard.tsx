import React from "react"
import { TierSelector } from "../../workflow/tier/tier_selector"
import { TierEngine } from "../../workflow/tier/tier_integration"
import { ProfileKey } from "../../workflow/tier/tier_types"
import { getUIRules } from "../../templates/tier/tier_ui_rules"
import { getTemplateGroupsForTier } from "../../templates/tier/template_group_registry"

interface TierCapabilityDashboardProps {
  profile: ProfileKey
}

function renderList(items: string[]) {
  return React.createElement(
    "ul",
    null,
    items.map((item) => React.createElement("li", { key: item }, item))
  )
}

export function TierCapabilityDashboard(props: TierCapabilityDashboardProps) {
  const profile = props.profile
  const selector = new TierSelector(profile)
  const tier = selector.getCurrentTier()

  const ctx = TierEngine.getTierContext(tier)
  const uiRules = getUIRules(tier)
  const allowedGroups = getTemplateGroupsForTier(tier)

  return React.createElement(
    "div",
    { style: { padding: "20px", fontFamily: "sans-serif" } },

    React.createElement("h2", null, "Tier Capability Dashboard"),

    React.createElement(
      "div",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Tier Metadata"),
      React.createElement("p", null, "Tier: " + tier),
      React.createElement("p", null, "Semantic Depth: " + JSON.stringify(ctx.semantic_depth)),
      React.createElement("p", null, "Routing Complexity: " + ctx.routing_complexity)
    ),

    React.createElement(
      "div",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Allowed Interfaces"),
      renderList(ctx.interface_rules.allowed_interfaces ?? [])
    ),

    React.createElement(
      "div",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Allowed Template Groups"),
      renderList(allowedGroups)
    ),

    React.createElement(
      "div",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Unlocked UI Modes"),
      renderList(uiRules.map((rule) => rule.id))
    )
  )
}
