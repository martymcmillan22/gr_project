import type { GovernanceProfile, Tier } from "../types";
import {
  STUDIO_ENTERPRISE_GARDEN_MAINTENANCE,
  STUDIO_ENTERPRISE_GUIDED_CHAIN,
  STUDIO_ENTERPRISE_PROFILE_BINDING,
  STUDIO_ENTERPRISE_SECTION_ROLE,
  STUDIO_ENTERPRISE_SECTION_WING,
  STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP,
  STUDIO_ENTERPRISE_TOWER,
  STUDIO_ENTERPRISE_WORKSPACE_MODES,
  REQUIRED_RELEASE_SAFETY_CHECKS,
  TIER_COMMANDS,
  TIER_QPU_MAX_COMPARTMENT,
  TIER_RANK,
  getGovernanceLongTermCycleApplyGate,
  getGovernancePolicyReleaseSafetyChecks,
  getAnchorStudioEnterpriseGardenMaintenance,
  getAnchorStudioEnterpriseGuidedChain,
  getAnchorStudioEnterpriseQpuMode,
  getAnchorStudioEnterpriseSectionRole,
  getAnchorStudioEnterpriseSectionWing,
  getAnchorStudioEnterpriseTemporalOwner,
  getAnchorStudioEnterpriseTowerDimension,
  getAnchorStudioEnterpriseTowerEnabled,
  getAnchorTierCommands,
  getAnchorTierQpuMaxCompartment,
} from "./baseTrueConstants";
import { assertDeterministicAnchorConsistency } from "./schemaGuards";

assertDeterministicAnchorConsistency();

const DEFAULT_ALL_COMMANDS = [4, 16, 64, 256];

function hasTierAtLeast(tier: Tier, minTier: Tier): boolean {
  return TIER_RANK[tier] >= TIER_RANK[minTier];
}

export function canCreateIdea(_tier: Tier): boolean {
  return true;
}

export function canFormSeed(tier: Tier): boolean {
  return hasTierAtLeast(tier, "intermediate");
}

export function canRouteRRInPipeline(tier: Tier): boolean {
  return hasTierAtLeast(tier, "advanced");
}

export function canViewRRInPipeline(tier: Tier): boolean {
  return hasTierAtLeast(tier, "intermediate");
}

export function canPreviewQPUInSeed(tier: Tier): boolean {
  return hasTierAtLeast(tier, "studio");
}

export function canCreateProject(tier: Tier): boolean {
  return hasTierAtLeast(tier, "studio");
}

export function canUseQPUTower(tier: Tier): boolean {
  return tier === "enterprise";
}

export function getGovernanceProfilesForTier(tier: Extract<Tier, "studio" | "enterprise">): readonly GovernanceProfile[] {
  return STUDIO_ENTERPRISE_PROFILE_BINDING[tier].profiles;
}

export function isGovernanceProfileAllowed(
  tier: Extract<Tier, "studio" | "enterprise">,
  profile: GovernanceProfile,
): boolean {
  return STUDIO_ENTERPRISE_PROFILE_BINDING[tier].profiles.includes(profile);
}

export function canUseGovernedApplyMode(tier: Tier): boolean {
  if (tier !== "studio" && tier !== "enterprise") {
    return false;
  }
  return STUDIO_ENTERPRISE_PROFILE_BINDING[tier].governed_apply_mode;
}

export function getAvailableCommandPowers(tier: Tier): number[] {
  const commands = TIER_COMMANDS[tier];
  if (commands.includes("all")) {
    return DEFAULT_ALL_COMMANDS;
  }
  return commands.filter((value): value is number => typeof value === "number");
}

export function getTierQpuMaxCompartment(tier: Tier): number {
  return TIER_QPU_MAX_COMPARTMENT[tier];
}

export function validatePipelineAnchorConsistency(): void {
  for (const tier of Object.keys(TIER_COMMANDS) as Tier[]) {
    const expectedCommands = [...TIER_COMMANDS[tier]].sort().join(",");
    const actualCommands = [...getAnchorTierCommands(tier)].sort().join(",");
    if (expectedCommands !== actualCommands) {
      throw new Error(`Pipeline tier commands mismatch for ${tier}`);
    }

    const expectedMax = TIER_QPU_MAX_COMPARTMENT[tier];
    const actualMax = getAnchorTierQpuMaxCompartment(tier);
    if (expectedMax !== actualMax) {
      throw new Error(`Pipeline qpu max compartment mismatch for ${tier}`);
    }
  }

  for (const mode of ["studio", "enterprise"] as const) {
    const expectedQpuMode = STUDIO_ENTERPRISE_WORKSPACE_MODES[mode].qpu_mode;
    const actualQpuMode = getAnchorStudioEnterpriseQpuMode(mode);
    if (expectedQpuMode !== actualQpuMode) {
      throw new Error(`Pipeline studio_enterprise qpu_mode mismatch for ${mode}`);
    }

    const expectedTowerEnabled = STUDIO_ENTERPRISE_WORKSPACE_MODES[mode].tower_enabled;
    const actualTowerEnabled = getAnchorStudioEnterpriseTowerEnabled(mode);
    if (expectedTowerEnabled !== actualTowerEnabled) {
      throw new Error(`Pipeline studio_enterprise tower_enabled mismatch for ${mode}`);
    }
  }

  const expectedGuidedChain = STUDIO_ENTERPRISE_GUIDED_CHAIN.join(",");
  const actualGuidedChain = getAnchorStudioEnterpriseGuidedChain().join(",");
  if (expectedGuidedChain !== actualGuidedChain) {
    throw new Error("Pipeline studio_enterprise guided_chain mismatch");
  }

  const expectedGarden = STUDIO_ENTERPRISE_GARDEN_MAINTENANCE.join(",");
  const actualGarden = getAnchorStudioEnterpriseGardenMaintenance().join(",");
  if (expectedGarden !== actualGarden) {
    throw new Error("Pipeline studio_enterprise garden_maintenance mismatch");
  }

  const expectedQcOwner = STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP.qc_user.join(",");
  const actualQcOwner = getAnchorStudioEnterpriseTemporalOwner("qc_user").join(",");
  if (expectedQcOwner !== actualQcOwner) {
    throw new Error("Pipeline studio_enterprise temporal_ownership.qc_user mismatch");
  }

  const expectedQaOwner = STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP.qa_va.join(",");
  const actualQaOwner = getAnchorStudioEnterpriseTemporalOwner("qa_va").join(",");
  if (expectedQaOwner !== actualQaOwner) {
    throw new Error("Pipeline studio_enterprise temporal_ownership.qa_va mismatch");
  }

  for (const section of ["DATA", "LOGIC", "JAVA", "TEMPLATES"] as const) {
    const expectedWing = STUDIO_ENTERPRISE_SECTION_WING[section];
    const actualWing = getAnchorStudioEnterpriseSectionWing(section);
    if (expectedWing !== actualWing) {
      throw new Error(`Pipeline studio_enterprise sections.${section}.wing mismatch`);
    }

    const expectedRole = STUDIO_ENTERPRISE_SECTION_ROLE[section];
    const actualRole = getAnchorStudioEnterpriseSectionRole(section);
    if (expectedRole !== actualRole) {
      throw new Error(`Pipeline studio_enterprise sections.${section}.role mismatch`);
    }
  }

  for (const dimension of ["zones", "floors_per_zone", "total_floors"] as const) {
    const expectedDimension = STUDIO_ENTERPRISE_TOWER[dimension];
    const actualDimension = getAnchorStudioEnterpriseTowerDimension(dimension);
    if (expectedDimension !== actualDimension) {
      throw new Error(`Pipeline studio_enterprise enterprise_tower.${dimension} mismatch`);
    }
  }

  if (STUDIO_ENTERPRISE_PROFILE_BINDING.studio.profiles.join(",") !== "weekly") {
    throw new Error("Pipeline Studio profile binding mismatch");
  }

  if (STUDIO_ENTERPRISE_PROFILE_BINDING.enterprise.profiles.join(",") !== "monthly,quarterly,annual") {
    throw new Error("Pipeline Enterprise profile binding mismatch");
  }

  if (STUDIO_ENTERPRISE_PROFILE_BINDING.studio.governed_apply_mode) {
    throw new Error("Pipeline Studio governed apply mode must be disabled");
  }

  if (!STUDIO_ENTERPRISE_PROFILE_BINDING.enterprise.governed_apply_mode) {
    throw new Error("Pipeline Enterprise governed apply mode must be enabled");
  }

  if (!getGovernanceLongTermCycleApplyGate()) {
    throw new Error("Pipeline governance cycle apply gates are not enabled");
  }

  const releaseSafetyChecks = getGovernancePolicyReleaseSafetyChecks();
  for (const requiredCheck of REQUIRED_RELEASE_SAFETY_CHECKS) {
    if (!releaseSafetyChecks.includes(requiredCheck)) {
      throw new Error(`Pipeline governance release safety check missing: ${requiredCheck}`);
    }
  }
}

export function getIdeaGeometryMode(tier: Tier): "flat" | "layered" | "architectural" {
  if (tier === "novice") {
    return "flat";
  }
  if (tier === "intermediate") {
    return "layered";
  }
  return "architectural";
}

export function getSeedGeometryMode(tier: Tier): "layered" | "architectural" {
  return hasTierAtLeast(tier, "studio") ? "architectural" : "layered";
}

export function getProjectGeometryMode(): "architectural" {
  return "architectural";
}
