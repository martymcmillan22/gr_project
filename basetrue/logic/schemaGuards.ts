import type { Phase, TemporalGroup, Tier, WorkspaceMode } from "../types";
import {
  ENTERPRISE_PROFILE_COMMANDS,
  GOVERNANCE_PROFILES,
  PHASE_COLOR_BY_GROUP,
  PHASES,
  REQUIRED_RELEASE_SAFETY_CHECKS,
  STUDIO_ENTERPRISE_PROFILE_BINDING,
  STUDIO_PROFILE_COMMANDS,
  STUDIO_ENTERPRISE_GARDEN_MAINTENANCE,
  STUDIO_ENTERPRISE_GUIDED_CHAIN,
  STUDIO_ENTERPRISE_SECTION_ROLE,
  STUDIO_ENTERPRISE_SECTION_WING,
  STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP,
  STUDIO_ENTERPRISE_TOWER,
  STUDIO_ENTERPRISE_WORKSPACE_MODES,
  TEMPORAL_GROUP_BY_INDEX,
  TEMPORAL_GROUPS,
  TIER_COMMANDS,
  TIERS,
  TIER_QPU_MAX_COMPARTMENT,
  VIEW_BY_TEMPORAL_GROUP,
  WORKSPACE_MODES,
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

export function isTier(value: unknown): value is Tier {
  return typeof value === "string" && (TIERS as readonly string[]).includes(value);
}

export function isTemporalGroup(value: unknown): value is TemporalGroup {
  return typeof value === "string" && (TEMPORAL_GROUPS as readonly string[]).includes(value);
}

export function isPhase(value: unknown): value is Phase {
  return typeof value === "string" && (PHASES as readonly string[]).includes(value);
}

export function isWorkspaceMode(value: unknown): value is WorkspaceMode {
  return typeof value === "string" && (WORKSPACE_MODES as readonly string[]).includes(value);
}

export function assertValidCompartmentIndex(index: number): void {
  if (!Number.isInteger(index) || index < 1 || index > 12) {
    throw new Error(`Invalid compartment index: ${index}`);
  }
}

export function assertDeterministicAnchorConsistency(): void {
  for (const tier of TIERS) {
    const expectedCommands = [...TIER_COMMANDS[tier]].sort().join(",");
    const actualCommands = [...getAnchorTierCommands(tier)].sort().join(",");
    if (expectedCommands !== actualCommands) {
      throw new Error(`Anchor mismatch for tier commands: ${tier}`);
    }

    const expectedMaxCompartment = TIER_QPU_MAX_COMPARTMENT[tier];
    const actualMaxCompartment = getAnchorTierQpuMaxCompartment(tier);
    if (expectedMaxCompartment !== actualMaxCompartment) {
      throw new Error(`Anchor mismatch for qpu_max_compartment: ${tier}`);
    }
  }

  for (const group of TEMPORAL_GROUPS) {
    if (!VIEW_BY_TEMPORAL_GROUP[group]) {
      throw new Error(`Missing deterministic view mapping for temporal group: ${group}`);
    }

    for (const phase of PHASES) {
      if (!PHASE_COLOR_BY_GROUP[phase][group]) {
        throw new Error(`Missing deterministic phase color mapping for ${phase}.${group}`);
      }
    }
  }

  for (let index = 1; index <= 12; index += 1) {
    if (!TEMPORAL_GROUP_BY_INDEX[index]) {
      throw new Error(`Missing temporal mapping for compartment index ${index}`);
    }
  }

  for (const mode of ["studio", "enterprise"] as const) {
    const expectedQpuMode = STUDIO_ENTERPRISE_WORKSPACE_MODES[mode].qpu_mode;
    const actualQpuMode = getAnchorStudioEnterpriseQpuMode(mode);
    if (expectedQpuMode !== actualQpuMode) {
      throw new Error(`Anchor mismatch for studio_enterprise qpu_mode: ${mode}`);
    }

    const expectedTowerEnabled = STUDIO_ENTERPRISE_WORKSPACE_MODES[mode].tower_enabled;
    const actualTowerEnabled = getAnchorStudioEnterpriseTowerEnabled(mode);
    if (expectedTowerEnabled !== actualTowerEnabled) {
      throw new Error(`Anchor mismatch for studio_enterprise tower_enabled: ${mode}`);
    }
  }

  const expectedGuidedChain = STUDIO_ENTERPRISE_GUIDED_CHAIN.join(",");
  const actualGuidedChain = getAnchorStudioEnterpriseGuidedChain().join(",");
  if (expectedGuidedChain !== actualGuidedChain) {
    throw new Error("Anchor mismatch for studio_enterprise guided_chain");
  }

  const expectedGarden = STUDIO_ENTERPRISE_GARDEN_MAINTENANCE.join(",");
  const actualGarden = getAnchorStudioEnterpriseGardenMaintenance().join(",");
  if (expectedGarden !== actualGarden) {
    throw new Error("Anchor mismatch for studio_enterprise garden_maintenance");
  }

  const expectedQcOwner = STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP.qc_user.join(",");
  const actualQcOwner = getAnchorStudioEnterpriseTemporalOwner("qc_user").join(",");
  if (expectedQcOwner !== actualQcOwner) {
    throw new Error("Anchor mismatch for studio_enterprise temporal_ownership.qc_user");
  }

  const expectedQaOwner = STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP.qa_va.join(",");
  const actualQaOwner = getAnchorStudioEnterpriseTemporalOwner("qa_va").join(",");
  if (expectedQaOwner !== actualQaOwner) {
    throw new Error("Anchor mismatch for studio_enterprise temporal_ownership.qa_va");
  }

  for (const section of ["DATA", "LOGIC", "JAVA", "TEMPLATES"] as const) {
    const expectedWing = STUDIO_ENTERPRISE_SECTION_WING[section];
    const actualWing = getAnchorStudioEnterpriseSectionWing(section);
    if (expectedWing !== actualWing) {
      throw new Error(`Anchor mismatch for studio_enterprise sections.${section}.wing`);
    }

    const expectedRole = STUDIO_ENTERPRISE_SECTION_ROLE[section];
    const actualRole = getAnchorStudioEnterpriseSectionRole(section);
    if (expectedRole !== actualRole) {
      throw new Error(`Anchor mismatch for studio_enterprise sections.${section}.role`);
    }
  }

  for (const dimension of ["zones", "floors_per_zone", "total_floors"] as const) {
    const expectedDimension = STUDIO_ENTERPRISE_TOWER[dimension];
    const actualDimension = getAnchorStudioEnterpriseTowerDimension(dimension);
    if (expectedDimension !== actualDimension) {
      throw new Error(`Anchor mismatch for studio_enterprise enterprise_tower.${dimension}`);
    }
  }

  const studioProfiles = STUDIO_ENTERPRISE_PROFILE_BINDING.studio.profiles;
  const enterpriseProfiles = STUDIO_ENTERPRISE_PROFILE_BINDING.enterprise.profiles;

  if (studioProfiles.join(",") !== "weekly") {
    throw new Error("Invalid Studio governance profile binding");
  }

  if (enterpriseProfiles.join(",") !== "monthly,quarterly,annual") {
    throw new Error("Invalid Enterprise governance profile binding");
  }

  for (const profile of [...studioProfiles, ...enterpriseProfiles]) {
    if (!(GOVERNANCE_PROFILES as readonly string[]).includes(profile)) {
      throw new Error(`Invalid governance profile in Studio/Enterprise binding: ${profile}`);
    }
  }

  if (STUDIO_ENTERPRISE_PROFILE_BINDING.studio.governed_apply_mode) {
    throw new Error("Studio cannot have governed apply mode enabled");
  }

  if (!STUDIO_ENTERPRISE_PROFILE_BINDING.enterprise.governed_apply_mode) {
    throw new Error("Enterprise must have governed apply mode enabled");
  }

  if (
    STUDIO_ENTERPRISE_PROFILE_BINDING.studio.qpu_mode !== STUDIO_ENTERPRISE_WORKSPACE_MODES.studio.qpu_mode ||
    STUDIO_ENTERPRISE_PROFILE_BINDING.studio.tower_enabled !== STUDIO_ENTERPRISE_WORKSPACE_MODES.studio.tower_enabled
  ) {
    throw new Error("Studio profile binding mismatches workspace mode contract");
  }

  if (
    STUDIO_ENTERPRISE_PROFILE_BINDING.enterprise.qpu_mode !== STUDIO_ENTERPRISE_WORKSPACE_MODES.enterprise.qpu_mode ||
    STUDIO_ENTERPRISE_PROFILE_BINDING.enterprise.tower_enabled !== STUDIO_ENTERPRISE_WORKSPACE_MODES.enterprise.tower_enabled
  ) {
    throw new Error("Enterprise profile binding mismatches workspace mode contract");
  }

  if (!getGovernanceLongTermCycleApplyGate()) {
    throw new Error("Governance long-term cycle apply gate must be enabled for Enterprise");
  }

  const releaseChecks = getGovernancePolicyReleaseSafetyChecks();
  for (const requiredCheck of REQUIRED_RELEASE_SAFETY_CHECKS) {
    if (!releaseChecks.includes(requiredCheck)) {
      throw new Error(`Missing governance release safety check: ${requiredCheck}`);
    }
  }

  if (!STUDIO_PROFILE_COMMANDS.includes("semantic-health") || !ENTERPRISE_PROFILE_COMMANDS.includes("release")) {
    throw new Error("Studio/Enterprise command routing map is incomplete");
  }
}
