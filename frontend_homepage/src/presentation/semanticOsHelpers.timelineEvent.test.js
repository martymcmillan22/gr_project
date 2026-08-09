import { describe, expect, it } from "vitest";

import {
  buildUnifiedPlatformIntelligenceState,
  buildTimelineOrchestrationGroups,
  buildTimelineOrchestrationPriorityQueue,
  buildTimelineSignalGroups,
  createTimelineSignalState,
  evaluateTimelineOrchestrationPolicies,
  normalizeSemanticActionLogEntry,
  normalizeTimelineSlotEventEnvelope,
  reduceTimelineSlotSignal,
} from "./semanticOsHelpers";

describe("normalizeTimelineSlotEventEnvelope", () => {
  it("normalizes camelCase input to canonical snake_case contract", () => {
    const payload = normalizeTimelineSlotEventEnvelope({
      eventType: "slot_state_change",
      eventVersion: "v1",
      source: "frontend.timeline.grid",
      slotIndex: 3,
      phase: "Ideas",
      temporalAlignment: "past",
      calculusOperation: "Integral",
      isLocked: false,
      isCompleted: true,
      industryMetadata: { group_name: "Arts" },
      semanticState: { drift_score: 0.2 },
      completedSlots: [1, 2, 3],
    });

    expect(payload.event_type).toBe("slot_state_change");
    expect(payload.event_version).toBe("v1");
    expect(payload.slot_index).toBe(3);
    expect(payload.temporal_alignment).toBe("past");
    expect(payload.calculus_operation).toBe("Integral");
    expect(payload.gate_locked).toBe(false);
    expect(payload.slot_completed).toBe(true);
    expect(payload.industry_metadata.group_name).toBe("Arts");
    expect(payload.semantic_state.drift_score).toBe(0.2);
    expect(payload.completed_slots).toEqual([1, 2, 3]);
  });

  it("keeps canonical snake_case payload stable", () => {
    const payload = normalizeTimelineSlotEventEnvelope({
      event_type: "slot_completion",
      event_version: "v1",
      source: "project_middle_layer.calculus_timeline_runtime",
      slot_index: 8,
      phase: "Seeds",
      temporal_alignment: "future",
      calculus_operation: "Derivative",
      gate_locked: false,
      slot_completed: true,
      industry_metadata: { industry: "Software" },
      semantic_state: { alignment_score: 0.9 },
      completed_slots: [1, 2, 3, 4, 5, 6, 7, 8],
    });

    expect(payload.event_type).toBe("slot_completion");
    expect(payload.slot_index).toBe(8);
    expect(payload.completed_slots).toEqual([1, 2, 3, 4, 5, 6, 7, 8]);
    expect(payload.industry_metadata.industry).toBe("Software");
  });

  it("reduces slot events into deterministic timeline semantic state", () => {
    const initial = createTimelineSignalState();
    const next = reduceTimelineSlotSignal(initial, {
      event_type: "slot_completion",
      event_version: "v1",
      source: "frontend.timeline.grid",
      slot_index: 4,
      phase: "Ideas",
      temporal_alignment: "future",
      calculus_operation: "Derivative",
      gate_locked: false,
      slot_completed: true,
      completed_slots: [1, 2, 3, 4],
      industry_metadata: { group_id: 2, group_name: "Math", industry: "Capital Markets" },
      semantic_state: { drift_score: 0.2, stability_score: 0.8, alignment_score: 0.9 },
    });

    expect(next.slot_count).toBe(16);
    expect(next.completed_slots).toEqual([1, 2, 3, 4]);
    expect(next.latest_event.slot_index).toBe(4);
    expect(next.latest_event.semantic_state.stability_score).toBe(0.8);
    expect(next.latest_event.industry_metadata.group_name).toBe("Math");
    const ideasGate = next.phase_gates.find((item) => item.phase === "Ideas");
    const seedsGate = next.phase_gates.find((item) => item.phase === "Seeds");
    const studioGate = next.phase_gates.find((item) => item.phase === "Studio");
    const enterpriseGate = next.phase_gates.find((item) => item.phase === "Enterprise");
    expect(ideasGate?.locked).toBe(false);
    expect(seedsGate?.locked).toBe(false);
    expect(studioGate?.locked).toBe(true);
    expect(enterpriseGate?.locked).toBe(true);
  });

  it("normalizes timeline slot entries inside semantic action logs", () => {
    const normalized = normalizeSemanticActionLogEntry({
      action: "advance_workflow_step",
      status: "executed",
      subject: "Math",
      phase: "Ideas",
      timeline_entry: {
        eventType: "slot_state_change",
        slotIndex: 1,
        temporalAlignment: "past",
      },
    });

    expect(normalized.timeline_entry.event_type).toBe("slot_state_change");
    expect(normalized.timeline_entry.slot_index).toBe(1);
    expect(normalized.timeline_entry.temporal_alignment).toBe("past");
  });

  it("builds deterministic timeline groups from slot event signal state", () => {
    const state = reduceTimelineSlotSignal(createTimelineSignalState(), {
      event_type: "slot_state_change",
      slot_index: 9,
      phase: "Projects",
      industry_metadata: { group_name: "Math", industry: "Capital Markets" },
      semantic_state: { drift_score: 0.1, stability_score: 0.9, alignment_score: 0.8 },
      completed_slots: [1, 2, 3, 4, 5, 6, 7, 8, 9],
    });

    const groups = buildTimelineSignalGroups(state);
    expect(groups.length).toBe(1);
    expect(groups[0].subject).toBe("Math");
    expect(groups[0].phase).toBe("Projects");
    expect(groups[0].items[0].industry_metadata.industry).toBe("Capital Markets");
  });

  it("builds deterministic orchestration groups from timeline signal state", () => {
    const state = reduceTimelineSlotSignal(createTimelineSignalState(), {
      event_type: "slot_state_change",
      slot_index: 6,
      phase: "Seeds",
      slot_completed: true,
      gate_locked: false,
      completed_slots: [1, 2, 3, 4, 5, 6],
      industry_metadata: { group_name: "Math", industry: "Software" },
      semantic_state: { drift_score: 0.72, stability_score: 0.5, alignment_score: 0.31 },
    });

    const groups = buildTimelineOrchestrationGroups(state);
    const seedsCluster = groups.slot_clusters.find((item) => item.phase === "Seeds");
    const seedsPhase = groups.semantic_phases.find((item) => item.phase === "Seeds");

    expect(groups.slot_clusters.length).toBe(6);
    expect(seedsCluster?.completed_count).toBe(2);
    expect(seedsPhase?.event_count).toBe(1);
    expect(groups.drift_risk_groups.high.length).toBe(1);
    expect(groups.drift_risk_groups.medium.length).toBe(0);
  });

  it("unlocks Studio and Enterprise surface gates after canonical MVP completion", () => {
    const completedSlots = Array.from({ length: 16 }, (_, index) => index + 1);
    const state = reduceTimelineSlotSignal(createTimelineSignalState(), {
      event_type: "slot_completion",
      slot_index: 16,
      phase: "MVP",
      slot_completed: true,
      gate_locked: false,
      completed_slots: completedSlots,
      semantic_state: { drift_score: 0.2, stability_score: 0.8, alignment_score: 0.9 },
      industry_metadata: { group_name: "Systemics", industry: "Operations" },
    });

    const studioGate = state.phase_gates.find((item) => item.phase === "Studio");
    const enterpriseGate = state.phase_gates.find((item) => item.phase === "Enterprise");
    const triggerIds = evaluateTimelineOrchestrationPolicies(state).triggers.map((item) => item.id);

    expect(studioGate?.locked).toBe(false);
    expect(enterpriseGate?.locked).toBe(false);
    expect(triggerIds).toContain("gate_unlock");
  });

  it("evaluates timeline orchestration policies from latest event state", () => {
    const state = reduceTimelineSlotSignal(createTimelineSignalState(), {
      event_type: "slot_completion",
      slot_index: 4,
      phase: "Ideas",
      slot_completed: true,
      gate_locked: false,
      completed_slots: [1, 2, 3, 4],
      semantic_state: { drift_score: 0.73, stability_score: 0.4, alignment_score: 0.28 },
      industry_metadata: { group_name: "Math", industry: "Software" },
    });

    const policy = evaluateTimelineOrchestrationPolicies(state);
    const triggerIds = policy.triggers.map((item) => item.id);

    expect(policy.latest_slot_index).toBe(4);
    expect(triggerIds).toContain("slot_completion");
    expect(triggerIds).toContain("drift_spike");
    expect(triggerIds).toContain("alignment_change");
    expect(triggerIds).toContain("gate_unlock");
  });

  it("builds deterministic orchestration priority queue in critical-warn-info order", () => {
    const state = reduceTimelineSlotSignal(createTimelineSignalState(), {
      event_type: "slot_completion",
      slot_index: 4,
      phase: "Ideas",
      slot_completed: true,
      gate_locked: false,
      completed_slots: [1, 2, 3, 4],
      semantic_state: { drift_score: 0.9, stability_score: 0.45, alignment_score: 0.3 },
      industry_metadata: { group_name: "Math", industry: "Software" },
    });

    const queue = buildTimelineOrchestrationPriorityQueue(state);
    expect(queue.length).toBe(4);
    expect(queue.map((item) => item.id)).toEqual([
      "drift_spike",
      "alignment_change",
      "slot_completion",
      "gate_unlock",
    ]);
    expect(queue.map((item) => item.priority)).toEqual([
      "critical",
      "warn",
      "info",
      "info",
    ]);
    expect(queue[0].priority_rank).toBeLessThan(queue[1].priority_rank);
    expect(queue[1].priority_rank).toBeLessThan(queue[2].priority_rank);
  });

  it("builds unified platform intelligence state from timeline signal state", () => {
    const state = reduceTimelineSlotSignal(createTimelineSignalState(), {
      event_type: "slot_completion",
      slot_index: 4,
      phase: "Ideas",
      slot_completed: true,
      gate_locked: false,
      completed_slots: [1, 2, 3, 4],
      semantic_state: { drift_score: 0.9, stability_score: 0.5, alignment_score: 0.3 },
      industry_metadata: { group_name: "Math", industry: "Software" },
    });

    const intelligenceState = buildUnifiedPlatformIntelligenceState(state);
    expect(intelligenceState.orchestration.priority_queue.map((item) => item.id)).toEqual([
      "drift_spike",
      "alignment_change",
      "slot_completion",
      "gate_unlock",
    ]);
    expect(intelligenceState.semantic_metadata.drift_score).toBe(0.9);
    expect(intelligenceState.slot_progression.completed_count).toBe(4);
    expect(intelligenceState.synthesis.risk_clusters.primary).toBe("high");
  });
});
