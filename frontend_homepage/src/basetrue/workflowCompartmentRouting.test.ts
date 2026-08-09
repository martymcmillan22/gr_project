import { describe, expect, it } from "vitest";

import { routeWorkflow } from "../../../workflow/engine/tier/tier_workflow_router";
import {
  getWorkflowRules,
  resolveWorkflowCompartmentPhase,
  WORKFLOW_PHASE_RANGES,
} from "../../../workflow/engine/tier/tier_workflow_rules";

describe("workflow compartment semantics", () => {
  it("maps canonical and extended compartment ranges deterministically", () => {
    expect(WORKFLOW_PHASE_RANGES).toEqual([
      { phase: "Ideas", start: 1, end: 4 },
      { phase: "Seeds", start: 5, end: 8 },
      { phase: "Projects", start: 9, end: 12 },
      { phase: "MVP", start: 13, end: 16 },
      { phase: "Studio", start: 17, end: 20 },
      { phase: "Enterprise", start: 21, end: 24 },
    ]);

    expect(resolveWorkflowCompartmentPhase(1)).toBe("Ideas");
    expect(resolveWorkflowCompartmentPhase(6)).toBe("Seeds");
    expect(resolveWorkflowCompartmentPhase(11)).toBe("Projects");
    expect(resolveWorkflowCompartmentPhase(16)).toBe("MVP");
    expect(resolveWorkflowCompartmentPhase(18)).toBe("Studio");
    expect(resolveWorkflowCompartmentPhase(22)).toBe("Enterprise");
    expect(resolveWorkflowCompartmentPhase(0)).toBeNull();
    expect(resolveWorkflowCompartmentPhase(25)).toBeNull();
  });

  it("keeps advanced allowed compartments across 1-24", () => {
    const advancedRules = getWorkflowRules("advanced");
    expect(advancedRules.length).toBeGreaterThan(0);
    for (const rule of advancedRules) {
      expect(rule.allowed_compartments[0]).toBe(1);
      expect(rule.allowed_compartments[rule.allowed_compartments.length - 1]).toBe(24);
      expect(rule.allowed_compartments.length).toBe(24);
    }
  });

  it("routes advanced post-16 compartments through advanced authoring", () => {
    const result = routeWorkflow({
      tier: "advanced",
      interfaceId: "corporation",
      compartmentId: 22,
      timelineState: {
        phase_gates: [{ phase: "Enterprise", locked: false }],
      },
    });

    expect(result.error).toBeUndefined();
    expect(result.workflow).toBe("advanced_authoring");
  });

  it("enforces deterministic gate locks for enterprise and studio phases", () => {
    const enterpriseLocked = routeWorkflow({
      tier: "advanced",
      interfaceId: "corporation",
      compartmentId: 18,
      timelineState: {
        phase_gates: [{ phase: "Studio", locked: true }],
      },
    });

    expect(enterpriseLocked.error).toBe(true);
    expect(enterpriseLocked.reason).toContain("Studio");

    const studioLocked = routeWorkflow({
      tier: "advanced",
      interfaceId: "corporation",
      compartmentId: 22,
      timelineState: {
        phase_gates: [{ phase: "Enterprise", locked: true }],
      },
    });

    expect(studioLocked.error).toBe(true);
    expect(studioLocked.reason).toContain("Enterprise");
  });

  it("rejects novice routing beyond allowed compartment scope", () => {
    const noviceResult = routeWorkflow({
      tier: "novice",
      interfaceId: "public_profile",
      compartmentId: 18,
      timelineState: {
        phase_gates: [{ phase: "Studio", locked: false }],
      },
    });

    expect(noviceResult.error).toBe(true);
    expect(noviceResult.reason).toContain("outside allowed interface or compartment scope");
  });
});
