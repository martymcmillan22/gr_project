import anchor from "../anchors/bt_anchor.json";
import governancePolicy from "../../workflow/meta/governance_policy.json";
import governanceLongTerm from "../../workflow/meta/governance_long_term.json";
import type {
  GeometryMode,
  GovernanceProfile,
  Phase,
  RRLogicMode,
  RRQuadrant,
  RRSubnode,
  TemporalGroup,
  Tier,
  ViewType,
  WorkspaceMode,
} from "../types";

export const PHASES: readonly Phase[] = ["create", "post", "work"];
export const TEMPORAL_GROUPS: readonly TemporalGroup[] = ["past", "present_past", "present_future", "future"];
export const VIEWS: readonly ViewType[] = ["list", "detail", "how_to", "present"];
export const TIERS: readonly Tier[] = ["novice", "intermediate", "advanced", "studio", "enterprise"];
export const WORKSPACE_MODES: readonly WorkspaceMode[] = ["default", "studio", "enterprise"];
export const RR_QUADRANTS: readonly RRQuadrant[] = ["language", "arts", "math", "science"];
export const RR_SUBNODES: readonly RRSubnode[] = ["A", "B", "C", "D"];
export const RR_LOGIC_MODES: readonly RRLogicMode[] = ["hierarchical", "network", "object", "relational"];
export const GEOMETRY_MODES: readonly GeometryMode[] = ["architectural", "layered", "flat"];
export const GOVERNANCE_PROFILES: readonly GovernanceProfile[] = ["weekly", "monthly", "quarterly", "annual"];

export const TIER_RANK: Readonly<Record<Tier, number>> = {
  novice: 1,
  intermediate: 2,
  advanced: 3,
  studio: 4,
  enterprise: 5,
};

export const TEMPORAL_GROUP_BY_INDEX: Readonly<Record<number, TemporalGroup>> = {
  1: "past",
  2: "present_past",
  3: "present_future",
  4: "future",
  5: "past",
  6: "present_past",
  7: "present_future",
  8: "future",
  9: "past",
  10: "present_past",
  11: "present_future",
  12: "future",
};

export const VIEW_BY_TEMPORAL_GROUP: Readonly<Record<TemporalGroup, ViewType>> = {
  past: "list",
  present_past: "detail",
  present_future: "how_to",
  future: "present",
};

export const PHASE_COLOR_BY_GROUP: Readonly<Record<Phase, Record<TemporalGroup, string>>> = {
  create: {
    past: "red",
    present_past: "blue",
    present_future: "yellow",
    future: "green",
  },
  post: {
    past: "purple",
    present_past: "teal",
    present_future: "orange",
    future: "lime",
  },
  work: {
    past: "pink",
    present_past: "cyan",
    present_future: "amber",
    future: "green_lime",
  },
};

export const TIER_COMMANDS: Readonly<Record<Tier, ReadonlyArray<number | "all">>> = {
  novice: [4],
  intermediate: [4, 16],
  advanced: [4, 16, 64],
  studio: [4, 16, 64],
  enterprise: ["all"],
};

export const TIER_QPU_MAX_COMPARTMENT: Readonly<Record<Tier, number>> = {
  novice: 0,
  intermediate: 0,
  advanced: 0,
  studio: 8,
  enterprise: 12,
};

export const STUDIO_ENTERPRISE_WORKSPACE_MODES = {
  studio: {
    qpu_mode: "scaled",
    tower_enabled: false,
  },
  enterprise: {
    qpu_mode: "tower",
    tower_enabled: true,
  },
} as const;

export const STUDIO_ENTERPRISE_GUIDED_CHAIN = ["Monuments", "Checkout", "Surveys", "Polls"] as const;

export const STUDIO_ENTERPRISE_GARDEN_MAINTENANCE = [
  "manufacturing",
  "contractors",
  "logistics",
  "shipping",
] as const;

export const STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP = {
  qc_user: ["past", "present_past"],
  qa_va: ["present_future", "future"],
} as const;

export const STUDIO_ENTERPRISE_SECTION_WING = {
  DATA: "Duseum_Library",
  LOGIC: "Duseum",
  JAVA: "Nuseum",
  TEMPLATES: "Nuseum_Monuments",
} as const;

export const STUDIO_ENTERPRISE_SECTION_ROLE = {
  DATA: "safe_modification_layer",
  LOGIC: "descriptive_flow",
  JAVA: "narrative_action",
  TEMPLATES: "narrative_presentation",
} as const;

export const STUDIO_ENTERPRISE_TOWER = {
  zones: 4,
  floors_per_zone: 4,
  total_floors: 16,
} as const;

export const STUDIO_ENTERPRISE_PROFILE_BINDING = {
  studio: {
    profiles: ["weekly"],
    immediate_semantic_ops: true,
    governed_apply_mode: false,
    qpu_mode: "scaled",
    tower_enabled: false,
  },
  enterprise: {
    profiles: ["monthly", "quarterly", "annual"],
    immediate_semantic_ops: false,
    governed_apply_mode: true,
    qpu_mode: "tower",
    tower_enabled: true,
  },
} as const;

export const STUDIO_PROFILE_COMMANDS = [
  "semantic-health",
  "improve-all",
  "semantic-drift",
  "semantic-infer",
  "semantic-resolve",
  "ai-context",
  "ai-export",
] as const;

export const ENTERPRISE_PROFILE_COMMANDS = [
  "semantic-scorecard",
  "semantic-strategy-report",
  "improve-all-apply",
  "release",
  "release-notes",
  "ai-export",
] as const;

export const REQUIRED_RELEASE_SAFETY_CHECKS = ["validate-suite", "visualize-all", "sync-all", "ai-export"] as const;

export function getAnchorTierCommands(tier: Tier): ReadonlyArray<number | "all"> {
  const commands = anchor.tiers[tier]?.commands ?? [];
  return commands.filter((value): value is number | "all" => typeof value === "number" || value === "all");
}

export function getAnchorTierQpuMaxCompartment(tier: Tier): number {
  return anchor.tiers[tier]?.qpu_max_compartment ?? 0;
}

export function getAnchorStudioEnterpriseQpuMode(mode: "studio" | "enterprise"): string {
  return anchor.canonical_blueprint?.studio_enterprise?.[mode]?.qpu_mode ?? "";
}

export function getAnchorStudioEnterpriseTowerEnabled(mode: "studio" | "enterprise"): boolean {
  return Boolean(anchor.canonical_blueprint?.studio_enterprise?.[mode]?.tower_enabled);
}

export function getAnchorStudioEnterpriseGuidedChain(): readonly string[] {
  const chain = anchor.canonical_blueprint?.studio_enterprise?.guided_chain;
  return Array.isArray(chain) ? chain.filter((value): value is string => typeof value === "string") : [];
}

export function getAnchorStudioEnterpriseGardenMaintenance(): readonly string[] {
  const items = anchor.canonical_blueprint?.studio_enterprise?.garden_maintenance;
  return Array.isArray(items) ? items.filter((value): value is string => typeof value === "string") : [];
}

export function getAnchorStudioEnterpriseTemporalOwner(owner: "qc_user" | "qa_va"): readonly TemporalGroup[] {
  const groups = anchor.canonical_blueprint?.studio_enterprise?.temporal_ownership?.[owner];
  if (!Array.isArray(groups)) {
    return [];
  }
  return groups.filter((value): value is TemporalGroup => (TEMPORAL_GROUPS as readonly string[]).includes(value));
}

export function getAnchorStudioEnterpriseSectionWing(section: "DATA" | "LOGIC" | "JAVA" | "TEMPLATES"): string {
  return anchor.canonical_blueprint?.studio_enterprise?.sections?.[section]?.wing ?? "";
}

export function getAnchorStudioEnterpriseSectionRole(section: "DATA" | "LOGIC" | "JAVA" | "TEMPLATES"): string {
  return anchor.canonical_blueprint?.studio_enterprise?.sections?.[section]?.role ?? "";
}

export function getAnchorStudioEnterpriseTowerDimension(
  dimension: "zones" | "floors_per_zone" | "total_floors",
): number {
  const value = anchor.canonical_blueprint?.studio_enterprise?.enterprise_tower?.[dimension];
  return typeof value === "number" ? value : 0;
}

export function getGovernancePolicyReleaseSafetyChecks(): readonly string[] {
  const checks = governancePolicy.release_safety_checks;
  return Array.isArray(checks) ? checks.filter((value): value is string => typeof value === "string") : [];
}

export function getGovernanceLongTermCycleApplyGate(): boolean {
  return Boolean(
    governanceLongTerm.gates?.cycle_apply_requires_engine_approvals &&
      governanceLongTerm.gates?.cycle_apply_requires_cross_domain_approvals,
  );
}
