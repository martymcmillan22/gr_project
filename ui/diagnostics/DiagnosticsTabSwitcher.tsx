import React from "react"
import { ProfileKey } from "../../workflow/tier/tier_types"

import { TemplateGroupInspectorPanel } from "./TemplateGroupInspectorPanel"
import { TierCapabilityDashboard } from "./TierCapabilityDashboard"
import { WorkflowInspectorPanel } from "./WorkflowInspectorPanel"
import { StorytellingInspectorPanel } from "./StorytellingInspectorPanel"
import { SemanticDepthVisualizer } from "./SemanticDepthVisualizer"

type DiagnosticsTabKey =
  | "template-groups"
  | "tier-capabilities"
  | "workflow"
  | "storytelling"
  | "semantic-depth"

interface DiagnosticsTabSwitcherProps {
  profile: ProfileKey
}

const tabLabels: Record<DiagnosticsTabKey, string> = {
  "template-groups": "Template Groups",
  "tier-capabilities": "Tier Capabilities",
  workflow: "Workflow Inspector",
  storytelling: "Storytelling Inspector",
  "semantic-depth": "Semantic Depth",
}

export function DiagnosticsTabSwitcher({ profile }: DiagnosticsTabSwitcherProps) {
  const [activeTab, setActiveTab] = React.useState<DiagnosticsTabKey>("template-groups")

  const tabs: DiagnosticsTabKey[] = [
    "template-groups",
    "tier-capabilities",
    "workflow",
    "storytelling",
    "semantic-depth",
  ]

  const activePanel =
    activeTab === "template-groups"
      ? React.createElement(TemplateGroupInspectorPanel, { profile })
      : activeTab === "tier-capabilities"
        ? React.createElement(TierCapabilityDashboard, { profile })
        : activeTab === "workflow"
          ? React.createElement(WorkflowInspectorPanel, { profile })
          : activeTab === "storytelling"
            ? React.createElement(StorytellingInspectorPanel, { profile })
            : React.createElement(SemanticDepthVisualizer, { profile })

  return React.createElement(
    "div",
    { style: { padding: "20px", fontFamily: "sans-serif" } },
    React.createElement(
      "div",
      { style: { display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "20px" } },
      tabs.map((tab) =>
        React.createElement(
          "button",
          {
            key: tab,
            type: "button",
            onClick: () => setActiveTab(tab),
            style: {
              padding: "8px 12px",
              border: activeTab === tab ? "2px solid #000" : "1px solid #999",
              background: activeTab === tab ? "#f3f3f3" : "#fff",
              cursor: "pointer",
            },
          },
          tabLabels[tab]
        )
      )
    ),
    activePanel
  )
}
