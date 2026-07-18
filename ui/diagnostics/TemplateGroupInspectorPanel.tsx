import React from "react"
import { TierSelector } from "../../workflow/tier/tier_selector"
import { ProfileKey } from "../../workflow/tier/tier_types"

import { createTemplateGroupInspector } from "../../templates/tier/template_group_inspector"

interface Props {
  profile: ProfileKey
}

type Inspector = ReturnType<typeof createTemplateGroupInspector>

function renderList(items: string[]) {
  return React.createElement(
    "ul",
    null,
    items.map((item) => React.createElement("li", { key: item }, item))
  )
}

function renderMapping(entries: Record<string, string[]>) {
  return Object.entries(entries).map(([key, groups]) =>
    React.createElement(
      "div",
      { key },
      React.createElement("strong", null, key),
      renderList(groups)
    )
  )
}

export const TemplateGroupInspectorPanel: React.FC<Props> = ({ profile }) => {
  const selector = new TierSelector(profile)
  const tier = selector.getCurrentTier()
  const inspector = createTemplateGroupInspector(tier)

  return React.createElement(
    "div",
    { style: { padding: "20px", fontFamily: "sans-serif" } },
    React.createElement("h2", null, "Template Group Inspector"),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Tier Metadata"),
      React.createElement(
        "p",
        null,
        React.createElement("strong", null, "Tier:"),
        " ",
        inspector.tier
      )
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Allowed Template Groups"),
      renderList(inspector.allowed_groups)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Interface → Template Groups"),
      renderMapping(inspector.interface_groups)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Workflow → Template Groups"),
      renderMapping(inspector.workflow_groups)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Storytelling → Template Groups"),
      renderMapping(inspector.storytelling_groups)
    )
  )
}
