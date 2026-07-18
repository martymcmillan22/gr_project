import React from "react"
import { TierSelector } from "../../workflow/tier/tier_selector"
import { TierEngine } from "../../workflow/tier/tier_integration"
import { ProfileKey, SemanticExposureLevel } from "../../workflow/tier/tier_types"

interface SemanticDepthVisualizerProps {
  profile: ProfileKey
}

const levelMap: Record<SemanticExposureLevel, number> = {
  none: 0,
  basic: 1,
  full: 2,
}

function levelBar(level: SemanticExposureLevel) {
  const filled = levelMap[level]
  const total = 2
  const bar = Array.from({ length: total }, (_, index) => (index < filled ? "█" : "░")).join("")
  return `${bar} (${level})`
}

function renderRow(label: string, level: SemanticExposureLevel) {
  return React.createElement(
    "p",
    { key: label },
    label + ": " + levelBar(level)
  )
}

export function SemanticDepthVisualizer({ profile }: SemanticDepthVisualizerProps) {
  const selector = new TierSelector(profile)
  const tier = selector.getCurrentTier()
  const ctx = TierEngine.getTierContext(tier)

  return React.createElement(
    "div",
    { style: { padding: "20px", fontFamily: "sans-serif" } },
    React.createElement("h2", null, "Semantic Depth Visualizer"),
    React.createElement("p", null, "Tier: " + tier),
    React.createElement("p", null, "Routing Complexity: " + ctx.routing_complexity),
    React.createElement("p", null, "BTPE Depth: " + ctx.btpe_depth),
    React.createElement("div", null,
      renderRow("MLAS", ctx.semantic_depth.mlas),
      renderRow("SVEM", ctx.semantic_depth.svem),
      renderRow("CCCP", ctx.semantic_depth.cccp),
      renderRow("DCHD", ctx.semantic_depth.dchd)
    )
  )
}
