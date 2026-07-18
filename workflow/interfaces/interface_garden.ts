import { TierEngine } from "../tier/tier_integration"
import { TierKey } from "../tier/tier_types"

export function getInterfaceGardenRules(tier: TierKey) {
  const ctx = TierEngine.getTierContext(tier)

  return {
    id: "garden",
    semantic_depth: ctx.semantic_depth,
    routing_complexity: ctx.routing_complexity,
    btpe_depth: ctx.btpe_depth,
    component_rules: ctx.component_rules,
    interface_rules: ctx.interface_rules,
  }
}
