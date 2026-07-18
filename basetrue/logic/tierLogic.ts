import anchor from "../anchors/bt_anchor.json";
import type { Tier, TierConfig } from "../types";
import { TIER_COMMANDS } from "./baseTrueConstants";
import { assertDeterministicAnchorConsistency } from "./schemaGuards";

assertDeterministicAnchorConsistency();

export function getTierConfig(tier: Tier): TierConfig {
  return anchor.tiers[tier] as TierConfig;
}

export function hasRR(tier: Tier): boolean {
  return Boolean(anchor.tiers[tier].rr);
}

export function hasQPU(tier: Tier): boolean {
  return Boolean(anchor.tiers[tier].qpu);
}

export function canAccessCommandPower(tier: Tier, power: number): boolean {
  const commands = TIER_COMMANDS[tier];
  return commands.includes("all") || commands.includes(power);
}
