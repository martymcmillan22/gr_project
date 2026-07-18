import React from "react"
import { TierSelector } from "../../workflow/tier/tier_selector"
import { ProfileKey } from "../../workflow/tier/tier_types"

import {
  getStorytellingBundle,
  StorytellingMap,
} from "../../storytelling_dashboard/tier/tier_storytelling_map"
import { getStorytellingRules } from "../../storytelling_dashboard/tier/tier_storytelling_rules"
import {
  getGroupsForInterface,
  getGroupsForStorytelling,
  getTemplateGroupsForTier,
} from "../../templates/tier/template_group_registry"

interface StorytellingInspectorPanelProps {
  profile: ProfileKey
}

type StorytellingRule = ReturnType<typeof getStorytellingRules>[number]

function renderList(items: string[]) {
  return React.createElement(
    "ul",
    null,
    items.map((item) => React.createElement("li", { key: item }, item))
  )
}

function renderStorytellingRule(rule: StorytellingRule) {
  return React.createElement(
    "div",
    { key: rule.id, style: { marginBottom: "16px" } },
    React.createElement("strong", null, rule.id),
    React.createElement("p", null, "Tier: " + rule.tier),
    React.createElement("p", null, "Routing Complexity: " + rule.routing_complexity),
    React.createElement("p", null, "BTPE Depth: " + rule.btpe_depth),
    React.createElement("p", null, "Allowed Interfaces:"),
    renderList(rule.allowed_interfaces),
    React.createElement("p", null, "Allowed Compartments:"),
    renderList(rule.allowed_compartments.map((value) => String(value)))
  )
}

export function StorytellingInspectorPanel({ profile }: StorytellingInspectorPanelProps) {
  const selector = new TierSelector(profile)
  const tier = selector.getCurrentTier()
  const rules = getStorytellingRules(tier)
  const allowedGroups = getTemplateGroupsForTier(tier)
  const storytellingKeys = Object.keys(StorytellingMap)
  const bundlePreview = getStorytellingBundle("basic_story", tier)

  return React.createElement(
    "div",
    { style: { padding: "20px", fontFamily: "sans-serif" } },
    React.createElement("h2", null, "Storytelling Inspector Panel"),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Tier Metadata"),
      React.createElement("p", null, "Tier: " + tier),
      React.createElement("p", null, "Allowed Template Groups:"),
      renderList(allowedGroups)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Storytelling Registry Keys"),
      renderList(storytellingKeys)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Storytelling Rules"),
      rules.map(renderStorytellingRule)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Storytelling → Template Group Mappings"),
      rules.map((rule) =>
        React.createElement(
          "div",
          { key: rule.id },
          React.createElement("strong", null, rule.id),
          React.createElement("p", null, getGroupsForStorytelling(rule.id).join(", ") || "None")
        )
      )
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Storytelling → Interface Mappings"),
      rules.map((rule) =>
        React.createElement(
          "div",
          { key: rule.id },
          React.createElement("strong", null, rule.id),
          renderList(rule.allowed_interfaces)
        )
      )
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Bundle Preview"),
      React.createElement("p", null, "Rules: " + (bundlePreview.rules ? bundlePreview.rules.id : "none")),
      React.createElement("p", null, "Components:"),
      renderList(bundlePreview.components.components)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Storytelling Lookup"),
      React.createElement("p", null, "basic_story: " + JSON.stringify(getStorytellingBundle("basic_story", tier).rules !== null)),
      React.createElement("p", null, "guided_story: " + JSON.stringify(getStorytellingBundle("guided_story", tier).rules !== null)),
      React.createElement("p", null, "advanced_story: " + JSON.stringify(getStorytellingBundle("advanced_story", tier).rules !== null)),
      React.createElement("p", null, "semantic_story: " + JSON.stringify(getStorytellingBundle("semantic_story", tier).rules !== null))
    )
  )
}
