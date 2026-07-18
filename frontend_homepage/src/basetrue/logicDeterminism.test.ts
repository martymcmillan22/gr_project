import { afterEach, describe, expect, it, vi } from "vitest";
import * as baseTrueConstants from "../../../basetrue/logic/baseTrueConstants";

import {
  canUseGovernedApplyMode,
  getGovernanceProfilesForTier,
  getAvailableCommandPowers,
  getTierQpuMaxCompartment,
  isGovernanceProfileAllowed,
  validatePipelineAnchorConsistency,
} from "../../../basetrue/logic/pipelineLogic";
import { buildQpuPlan } from "../../../basetrue/logic/qpuEngine";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("BaseTrue deterministic pipeline constants", () => {
  it("matches anchor consistency checks without throwing", () => {
    expect(() => validatePipelineAnchorConsistency()).not.toThrow();
  });

  it("returns deterministic command powers and qpu max compartment", () => {
    expect(getAvailableCommandPowers("novice")).toEqual([4]);
    expect(getAvailableCommandPowers("intermediate")).toEqual([4, 16]);
    expect(getAvailableCommandPowers("studio")).toEqual([4, 16, 64]);
    expect(getAvailableCommandPowers("enterprise")).toEqual([4, 16, 64, 256]);

    expect(getTierQpuMaxCompartment("novice")).toBe(0);
    expect(getTierQpuMaxCompartment("studio")).toBe(8);
    expect(getTierQpuMaxCompartment("enterprise")).toBe(12);

    expect(getGovernanceProfilesForTier("studio")).toEqual(["weekly"]);
    expect(getGovernanceProfilesForTier("enterprise")).toEqual(["monthly", "quarterly", "annual"]);
    expect(isGovernanceProfileAllowed("studio", "weekly")).toBe(true);
    expect(isGovernanceProfileAllowed("studio", "monthly")).toBe(false);
    expect(isGovernanceProfileAllowed("enterprise", "monthly")).toBe(true);
    expect(canUseGovernedApplyMode("studio")).toBe(false);
    expect(canUseGovernedApplyMode("enterprise")).toBe(true);
  });

  it("fails fast when anchor commands drift from typed constants", () => {
    vi.spyOn(baseTrueConstants, "getAnchorTierCommands").mockImplementation((tier) => {
      if (tier === "novice") {
        return [16];
      }
      return baseTrueConstants.TIER_COMMANDS[tier];
    });

    expect(() => validatePipelineAnchorConsistency()).toThrow(/Pipeline tier commands mismatch for novice/);
  });

  it("fails fast when studio_enterprise guided chain drifts", () => {
    vi.spyOn(baseTrueConstants, "getAnchorStudioEnterpriseGuidedChain").mockReturnValue([
      "Monuments",
      "Checkout",
      "Survey",
      "Polls",
    ]);

    expect(() => validatePipelineAnchorConsistency()).toThrow(/Pipeline studio_enterprise guided_chain mismatch/);
  });
});

describe("BaseTrue QPU engine guards", () => {
  it("rejects out-of-range compartment indexes", () => {
    expect(() =>
      buildQpuPlan({
        tier: "studio",
        compartmentIndex: 0,
        temporalGroup: "past",
      }),
    ).toThrow(/Invalid compartment index/);

    expect(() =>
      buildQpuPlan({
        tier: "studio",
        compartmentIndex: 13,
        temporalGroup: "future",
      }),
    ).toThrow(/Invalid compartment index/);
  });

  it("falls back invalid workspace mode to default", () => {
    const plan = buildQpuPlan({
      tier: "studio",
      compartmentIndex: 8,
      temporalGroup: "present_future",
      workspaceMode: "unknown" as never,
    });

    expect(plan.qpu_plan_id.startsWith("qpu.default.studio.8.present_future")).toBe(true);
  });
});

describe("BaseTrue qpu_plan_id determinism", () => {
  it("is stable for identical inputs and distinct across workspace modes", () => {
    const params = {
      tier: "enterprise" as const,
      compartmentIndex: 10,
      temporalGroup: "present_future" as const,
      rrSelection: {
        quadrant: "math" as const,
        subnode: "C" as const,
        logic_mode: "network" as const,
        temporal_group: "present_future" as const,
      },
    };

    const a = buildQpuPlan({ ...params, workspaceMode: "default" });
    const b = buildQpuPlan({ ...params, workspaceMode: "default" });
    const studio = buildQpuPlan({ ...params, workspaceMode: "studio" });
    const enterprise = buildQpuPlan({ ...params, workspaceMode: "enterprise" });

    expect(a.qpu_plan_id).toBe(b.qpu_plan_id);
    expect(a.qpu_plan_id).not.toBe(studio.qpu_plan_id);
    expect(a.qpu_plan_id).not.toBe(enterprise.qpu_plan_id);
    expect(studio.qpu_plan_id).not.toBe(enterprise.qpu_plan_id);
  });
});

describe("BaseTrue studio_enterprise drift matrix", () => {
  it("fails on qpu_mode drift", () => {
    vi.spyOn(baseTrueConstants, "getAnchorStudioEnterpriseQpuMode").mockImplementation((mode) => {
      if (mode === "studio") {
        return "tower";
      }
      return baseTrueConstants.STUDIO_ENTERPRISE_WORKSPACE_MODES[mode].qpu_mode;
    });

    expect(() => validatePipelineAnchorConsistency()).toThrow(/Pipeline studio_enterprise qpu_mode mismatch for studio/);
  });

  it("fails on tower_enabled drift", () => {
    vi.spyOn(baseTrueConstants, "getAnchorStudioEnterpriseTowerEnabled").mockImplementation((mode) => {
      if (mode === "enterprise") {
        return false;
      }
      return baseTrueConstants.STUDIO_ENTERPRISE_WORKSPACE_MODES[mode].tower_enabled;
    });

    expect(() => validatePipelineAnchorConsistency()).toThrow(
      /Pipeline studio_enterprise tower_enabled mismatch for enterprise/,
    );
  });

  it("fails on garden_maintenance drift", () => {
    vi.spyOn(baseTrueConstants, "getAnchorStudioEnterpriseGardenMaintenance").mockReturnValue([
      "manufacturing",
      "contractors",
      "shipping",
      "logistics",
    ]);

    expect(() => validatePipelineAnchorConsistency()).toThrow(/Pipeline studio_enterprise garden_maintenance mismatch/);
  });

  it("fails on temporal ownership drift", () => {
    vi.spyOn(baseTrueConstants, "getAnchorStudioEnterpriseTemporalOwner").mockImplementation((owner) => {
      if (owner === "qc_user") {
        return ["past", "future"];
      }
      return baseTrueConstants.STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP[owner];
    });

    expect(() => validatePipelineAnchorConsistency()).toThrow(
      /Pipeline studio_enterprise temporal_ownership.qc_user mismatch/,
    );
  });

  it("fails on section wing drift", () => {
    vi.spyOn(baseTrueConstants, "getAnchorStudioEnterpriseSectionWing").mockImplementation((section) => {
      if (section === "JAVA") {
        return "Duseum";
      }
      return baseTrueConstants.STUDIO_ENTERPRISE_SECTION_WING[section];
    });

    expect(() => validatePipelineAnchorConsistency()).toThrow(/Pipeline studio_enterprise sections.JAVA.wing mismatch/);
  });

  it("fails on section role drift", () => {
    vi.spyOn(baseTrueConstants, "getAnchorStudioEnterpriseSectionRole").mockImplementation((section) => {
      if (section === "DATA") {
        return "descriptive_flow";
      }
      return baseTrueConstants.STUDIO_ENTERPRISE_SECTION_ROLE[section];
    });

    expect(() => validatePipelineAnchorConsistency()).toThrow(/Pipeline studio_enterprise sections.DATA.role mismatch/);
  });

  it("fails on enterprise tower dimension drift", () => {
    vi.spyOn(baseTrueConstants, "getAnchorStudioEnterpriseTowerDimension").mockImplementation((dimension) => {
      if (dimension === "total_floors") {
        return 15;
      }
      return baseTrueConstants.STUDIO_ENTERPRISE_TOWER[dimension];
    });

    expect(() => validatePipelineAnchorConsistency()).toThrow(
      /Pipeline studio_enterprise enterprise_tower.total_floors mismatch/,
    );
  });

  it("fails when governance long-term apply gates are disabled", () => {
    vi.spyOn(baseTrueConstants, "getGovernanceLongTermCycleApplyGate").mockReturnValue(false);

    expect(() => validatePipelineAnchorConsistency()).toThrow(/Pipeline governance cycle apply gates are not enabled/);
  });

  it("fails when required governance release safety check is missing", () => {
    vi.spyOn(baseTrueConstants, "getGovernancePolicyReleaseSafetyChecks").mockReturnValue([
      "semantic-drift",
      "semantic-infer",
      "semantic-resolve",
      "validate-suite",
      "sync-all",
      "ai-export",
    ]);

    expect(() => validatePipelineAnchorConsistency()).toThrow(
      /Pipeline governance release safety check missing: visualize-all/,
    );
  });
});
