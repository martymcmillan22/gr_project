import { TierDefinition, TierKey } from "./tier_types"

export const UITiers: Record<TierKey, TierDefinition> = {
  novice: {
    id: "novice",
    label: "Novice",
    description: "Simplified interface with guided workflows and minimal cognitive load.",
    complexity: 1,
  },
  intermediate: {
    id: "intermediate",
    label: "Intermediate",
    description: "Moderate complexity with expanded options and light autonomy.",
    complexity: 2,
  },
  advanced: {
    id: "advanced",
    label: "Advanced",
    description: "Full access to tools, multi-panel layouts, and semantic controls.",
    complexity: 3,
  },
  veteran: {
    id: "veteran",
    label: "Veteran",
    description: "Developer-level interface exposing raw internals and semantic debugging.",
    complexity: 4,
  },
}
