export interface TimelineSemanticState {
  drift_score: number;
  stability_score: number;
  alignment_score: number;
}

export interface TimelineIndustryMetadata {
  group_id: number | null;
  group_name: string;
  industry: string;
  raw_label: string;
}

export interface TimelineSlotEvent {
  event_type: string;
  event_version: string;
  source: string;
  slot_index: number;
  phase: string;
  temporal_alignment: string;
  calculus_operation: string;
  gate_locked: boolean;
  slot_completed: boolean;
  industry_metadata: TimelineIndustryMetadata;
  semantic_state: TimelineSemanticState;
  completed_slots: number[];
}

export interface TimelinePhaseGate {
  phase: string;
  slot_start: number;
  slot_end: number;
  depends_on_slots: number[];
  locked: boolean;
}

export interface TimelineSignalState {
  slot_count: number;
  completed_slots: number[];
  phase_gates: TimelinePhaseGate[];
  slot_events: Record<number, TimelineSlotEvent>;
  latest_event: TimelineSlotEvent | null;
}

export interface TimelineOrchestrationTrigger {
  id: string;
  priority: "critical" | "warn" | "info";
  action: string;
  message: string;
  priority_rank: number;
}

export interface WorkspaceUnifiedPlatformIntelligenceState {
  source: string;
  orchestration: {
    priority_order: Array<"critical" | "warn" | "info">;
    priority_queue: TimelineOrchestrationTrigger[];
    trigger_count: number;
    highest_priority: "critical" | "warn" | "info";
  };
  semantic_metadata: {
    drift_score: number;
    stability_score: number;
    alignment_score: number;
  };
  phase_gate_state: {
    phase_gates: TimelinePhaseGate[];
    locked_phases: string[];
    unlocked_phases: string[];
  };
  slot_progression: {
    slot_count: number;
    completed_slots: number[];
    completed_count: number;
    completion_ratio: number;
    latest_slot_index: number;
    latest_phase: string;
  };
  synthesis: {
    risk_level: "high" | "medium" | "low";
    drift_trend: {
      direction: "rising" | "falling" | "stable";
      delta: number;
      sample_count: number;
    };
    alignment_trajectory: {
      direction: "improving" | "declining" | "stable";
      delta: number;
      sample_count: number;
    };
    mbsp_surface: {
      surface_phase: string;
      surface_tiers: {
        studio: {
          phase: string;
          label: string;
          unlocked: boolean;
          active: boolean;
          readiness_score: number;
        };
        enterprise: {
          phase: string;
          label: string;
          unlocked: boolean;
          active: boolean;
          readiness_score: number;
        };
      };
    };
  };
  latest_event: TimelineSlotEvent | null;
}

const SLOT_COUNT = 16;
const ORCHESTRATION_PRIORITY_ORDER: Array<"critical" | "warn" | "info"> = ["critical", "warn", "info"];
const ORCHESTRATION_PRIORITY_RANK: Record<"critical" | "warn" | "info", number> = {
  critical: 0,
  warn: 1,
  info: 2,
};

function buildSlotRange(start: number, end: number): number[] {
  const slots: number[] = [];
  for (let slot = start; slot <= end; slot += 1) {
    slots.push(slot);
  }
  return slots;
}

const PHASES: Array<{ phase: string; slot_start: number; slot_end: number; depends_on_slots: number[] }> = [
  { phase: "Ideas", slot_start: 1, slot_end: 4, depends_on_slots: [] },
  { phase: "Seeds", slot_start: 5, slot_end: 8, depends_on_slots: buildSlotRange(1, 4) },
  { phase: "Projects", slot_start: 9, slot_end: 12, depends_on_slots: buildSlotRange(1, 8) },
  { phase: "MVP", slot_start: 13, slot_end: 16, depends_on_slots: buildSlotRange(1, 12) },
  { phase: "Studio", slot_start: 17, slot_end: 20, depends_on_slots: buildSlotRange(1, 16) },
  { phase: "Enterprise", slot_start: 21, slot_end: 24, depends_on_slots: buildSlotRange(1, 16) },
];

function normalizeCompletedSlots(value: unknown): number[] {
  const list = Array.isArray(value) ? value : [];
  const deduped = new Set<number>();
  list.forEach((item) => {
    const slot = Number(item);
    if (Number.isFinite(slot) && slot >= 1 && slot <= SLOT_COUNT) {
      deduped.add(slot);
    }
  });
  return Array.from(deduped).sort((left, right) => left - right);
}

function buildPhaseGates(completedSlots: number[]): TimelinePhaseGate[] {
  return PHASES.map((phase) => {
    const dependencies = Array.isArray(phase.depends_on_slots) ? phase.depends_on_slots : [];
    const locked = dependencies.some((slot) => !completedSlots.includes(slot));
    return {
      phase: phase.phase,
      slot_start: phase.slot_start,
      slot_end: phase.slot_end,
      depends_on_slots: dependencies,
      locked,
    };
  });
}

function normalizeSemanticState(value: unknown): TimelineSemanticState {
  const state = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  return {
    drift_score: Number(state.drift_score || 0),
    stability_score: Number(state.stability_score || 0),
    alignment_score: Number(state.alignment_score || 0),
  };
}

function normalizeIndustryMetadata(value: unknown): TimelineIndustryMetadata {
  const metadata = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  return {
    group_id: Number(metadata.group_id || 0) || null,
    group_name: String(metadata.group_name || ""),
    industry: String(metadata.industry || ""),
    raw_label: String(metadata.raw_label || ""),
  };
}

export function createWorkspaceTimelineSignalState(): TimelineSignalState {
  return {
    slot_count: SLOT_COUNT,
    completed_slots: [],
    phase_gates: buildPhaseGates([]),
    slot_events: {},
    latest_event: null,
  };
}

export function reduceWorkspaceTimelineSlotSignal(
  previousState: TimelineSignalState,
  detail: Record<string, unknown>,
): TimelineSignalState {
  const eventType = String(detail.event_type || detail.eventType || "slot_state_change");
  const slotIndex = Number(detail.slot_index || detail.slotIndex || 0);
  if (!Number.isFinite(slotIndex) || slotIndex < 1 || slotIndex > SLOT_COUNT) {
    return previousState;
  }

  const rawCompletedSlots = Array.isArray(detail.completed_slots)
    ? detail.completed_slots
    : Array.isArray(detail.completedSlots)
      ? detail.completedSlots
      : [];

  const completedSlots = rawCompletedSlots.length > 0
    ? normalizeCompletedSlots(rawCompletedSlots)
    : Boolean(detail.slot_completed ?? detail.isCompleted)
      ? normalizeCompletedSlots([...previousState.completed_slots, slotIndex])
      : previousState.completed_slots;

  const slotEvent: TimelineSlotEvent = {
    event_type: eventType,
    event_version: String(detail.event_version || detail.eventVersion || "v1"),
    source: String(detail.source || "frontend.timeline.grid"),
    slot_index: slotIndex,
    phase: String(detail.phase || ""),
    temporal_alignment: String(detail.temporal_alignment || detail.temporalAlignment || ""),
    calculus_operation: String(detail.calculus_operation || detail.calculusOperation || ""),
    gate_locked: Boolean(detail.gate_locked ?? detail.isLocked),
    slot_completed: Boolean(detail.slot_completed ?? detail.isCompleted),
    industry_metadata: normalizeIndustryMetadata(detail.industry_metadata || detail.industryMetadata),
    semantic_state: normalizeSemanticState(detail.semantic_state || detail.semanticState),
    completed_slots: completedSlots,
  };

  return {
    slot_count: SLOT_COUNT,
    completed_slots: completedSlots,
    phase_gates: buildPhaseGates(completedSlots),
    slot_events: {
      ...previousState.slot_events,
      [slotIndex]: slotEvent,
    },
    latest_event: slotEvent,
  };
}

export function hydrateWorkspaceTimelineFromRuntimePayload(
  previousState: TimelineSignalState,
  payload: Record<string, unknown>,
): TimelineSignalState {
  if (!payload || typeof payload !== "object") {
    return previousState;
  }

  const progression = payload.deterministic_progression && typeof payload.deterministic_progression === "object"
    ? payload.deterministic_progression as Record<string, unknown>
    : {};
  const selected = payload.selected_slot_state && typeof payload.selected_slot_state === "object"
    ? payload.selected_slot_state as Record<string, unknown>
    : {};
  const selectedEvent = selected.event && typeof selected.event === "object"
    ? selected.event as Record<string, unknown>
    : {};

  const detail: Record<string, unknown> = {
    ...selectedEvent,
    slot_completed: Boolean(selected.completed),
    completed_slots: progression.completed_slots,
    industry_metadata: selected.industry_metadata,
    semantic_state: selected.state,
  };

  return reduceWorkspaceTimelineSlotSignal(previousState, detail);
}

export function getPhaseForCompartment(compartmentId: number): string {
  if (compartmentId >= 1 && compartmentId <= 4) {
    return "Ideas";
  }
  if (compartmentId >= 5 && compartmentId <= 8) {
    return "Seeds";
  }
  if (compartmentId >= 9 && compartmentId <= 12) {
    return "Projects";
  }
  if (compartmentId >= 13 && compartmentId <= 16) {
    return "MVP";
  }
  if (compartmentId >= 17 && compartmentId <= 20) {
    return "Studio";
  }
  return "Enterprise";
}

export function isCompartmentUnlocked(compartmentId: number, gates: TimelinePhaseGate[]): boolean {
  const phase = getPhaseForCompartment(compartmentId);
  const gate = gates.find((item) => item.phase === phase);
  return gate ? !gate.locked : true;
}

function getSortedTimelineEvents(state: TimelineSignalState): TimelineSlotEvent[] {
  return Object.values(state.slot_events || {}).sort((left, right) => left.slot_index - right.slot_index);
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(1, Number(value || 0)));
}

function buildMbspSurfaceSynthesisState(args: {
  latestPhase: string;
  completionRatio: number;
  alignmentScore: number;
  stabilityScore: number;
  riskLevel: "high" | "medium" | "low";
  triggerCount: number;
}) {
  const latestPhase = String(args.latestPhase || "").toLowerCase();
  const completionRatio = Number(args.completionRatio || 0);
  const alignmentScore = Number(args.alignmentScore || 0);
  const stabilityScore = Number(args.stabilityScore || 0);
  const riskLevel = args.riskLevel;
  const triggerCount = Number(args.triggerCount || 0);

  const studioReadinessScore = clampScore(
    (0.4 * completionRatio) + (0.35 * alignmentScore) + (0.25 * stabilityScore),
  );
  const enterpriseReadinessScore = clampScore(
    (0.45 * alignmentScore) + (0.35 * stabilityScore) + (0.2 * completionRatio) - (0.03 * triggerCount),
  );

  let surfacePhase = latestPhase;
  if (surfacePhase !== "studio" && surfacePhase !== "enterprise") {
    if (completionRatio >= 1) {
      surfacePhase = alignmentScore >= 0.78 && stabilityScore >= 0.72 && riskLevel !== "high" && triggerCount <= 3
        ? "enterprise"
        : "studio";
    }
  }

  return {
    surface_phase: surfacePhase || latestPhase || "ideas",
    surface_tiers: {
      studio: {
        phase: "studio",
        label: "creator_publisher_tier",
        unlocked: completionRatio >= 1 || latestPhase === "studio" || latestPhase === "enterprise",
        active: surfacePhase === "studio",
        readiness_score: Number(studioReadinessScore.toFixed(3)),
      },
      enterprise: {
        phase: "enterprise",
        label: "operational_organizational_tier",
        unlocked: completionRatio >= 1 || latestPhase === "enterprise",
        active: surfacePhase === "enterprise",
        readiness_score: Number(enterpriseReadinessScore.toFixed(3)),
      },
    },
  };
}

function buildTimelineOrchestrationGroups(state: TimelineSignalState): {
  drift_risk_groups: { high: TimelineSlotEvent[]; medium: TimelineSlotEvent[]; low: TimelineSlotEvent[] };
} {
  const events = getSortedTimelineEvents(state);
  const groups = {
    high: [] as TimelineSlotEvent[],
    medium: [] as TimelineSlotEvent[],
    low: [] as TimelineSlotEvent[],
  };

  events.forEach((event) => {
    const driftScore = Number(event?.semantic_state?.drift_score || 0);
    const alignmentScore = Number(event?.semantic_state?.alignment_score || 0);
    if (driftScore >= 0.67 || alignmentScore <= 0.4) {
      groups.high.push(event);
      return;
    }
    if (driftScore >= 0.34 || alignmentScore <= 0.67) {
      groups.medium.push(event);
      return;
    }
    groups.low.push(event);
  });

  return {
    drift_risk_groups: groups,
  };
}

function evaluateTimelineOrchestrationPolicies(state: TimelineSignalState): {
  triggers: Array<Omit<TimelineOrchestrationTrigger, "priority" | "priority_rank">>;
} {
  const latestEvent = state.latest_event;
  if (!latestEvent) {
    return { triggers: [] };
  }

  const triggers: Array<Omit<TimelineOrchestrationTrigger, "priority" | "priority_rank">> = [];
  const driftScore = Number(latestEvent.semantic_state?.drift_score || 0);
  const alignmentScore = Number(latestEvent.semantic_state?.alignment_score || 0);
  const slotIndex = Number(latestEvent.slot_index || 0);
  const phaseUnlockSlots: Record<number, string> = { 4: "Seeds", 8: "Projects", 12: "MVP", 16: "Studio" };

  if (Boolean(latestEvent.slot_completed)) {
    triggers.push({
      id: "slot_completion",
      action: "advance_workflow_step",
      message: `Slot ${slotIndex} completed. Advance deterministic workflow chain.`,
    });
  }

  if (driftScore >= 0.67) {
    triggers.push({
      id: "drift_spike",
      action: "issue_stabilization_patch",
      message: `Drift score ${driftScore.toFixed(2)} crossed stabilization threshold.`,
    });
  }

  if (alignmentScore <= 0.4) {
    triggers.push({
      id: "alignment_change",
      action: "reroute_to_alignment_review",
      message: `Alignment score ${alignmentScore.toFixed(2)} requires review routing.`,
    });
  }

  const unlockedPhase = phaseUnlockSlots[slotIndex];
  if (Boolean(latestEvent.slot_completed) && unlockedPhase) {
    const gate = state.phase_gates.find((item) => item.phase === unlockedPhase);
    if (gate && !gate.locked) {
      triggers.push({
        id: "gate_unlock",
        action: "unlock_next_phase",
        message: `${unlockedPhase} phase gate is now unlocked.`,
      });
    }
  }

  return {
    triggers,
  };
}

function buildTimelineOrchestrationPriorityQueue(state: TimelineSignalState): TimelineOrchestrationTrigger[] {
  const policy = evaluateTimelineOrchestrationPolicies(state);
  const triggerPriority: Record<string, "critical" | "warn" | "info"> = {
    drift_spike: "critical",
    alignment_change: "warn",
    slot_completion: "info",
    gate_unlock: "info",
  };

  return policy.triggers
    .map((trigger) => {
      const priority = triggerPriority[trigger.id] || "info";
      return {
        ...trigger,
        priority,
        priority_rank: ORCHESTRATION_PRIORITY_RANK[priority],
      } as TimelineOrchestrationTrigger;
    })
    .sort((left, right) => {
      if (left.priority_rank !== right.priority_rank) {
        return left.priority_rank - right.priority_rank;
      }
      return left.id.localeCompare(right.id);
    });
}

export function buildWorkspaceUnifiedPlatformIntelligenceState(
  timelineSignalState: TimelineSignalState,
): WorkspaceUnifiedPlatformIntelligenceState {
  const latestEvent = timelineSignalState.latest_event;
  const priorityQueue = buildTimelineOrchestrationPriorityQueue(timelineSignalState);
  const groups = buildTimelineOrchestrationGroups(timelineSignalState);
  const sortedEvents = getSortedTimelineEvents(timelineSignalState);

  let driftDelta = 0;
  let driftDirection: "rising" | "falling" | "stable" = "stable";
  let alignmentDelta = 0;
  let alignmentDirection: "improving" | "declining" | "stable" = "stable";

  if (sortedEvents.length >= 2) {
    const first = sortedEvents[0];
    const last = sortedEvents[sortedEvents.length - 1];
    driftDelta = Number(((last.semantic_state?.drift_score || 0) - (first.semantic_state?.drift_score || 0)).toFixed(3));
    alignmentDelta = Number(((last.semantic_state?.alignment_score || 0) - (first.semantic_state?.alignment_score || 0)).toFixed(3));
    if (driftDelta >= 0.05) {
      driftDirection = "rising";
    } else if (driftDelta <= -0.05) {
      driftDirection = "falling";
    }
    if (alignmentDelta >= 0.05) {
      alignmentDirection = "improving";
    } else if (alignmentDelta <= -0.05) {
      alignmentDirection = "declining";
    }
  }

  const latestDrift = Number(latestEvent?.semantic_state?.drift_score || 0);
  const latestAlignment = Number(latestEvent?.semantic_state?.alignment_score || 0);
  const riskLevel: "high" | "medium" | "low" = latestDrift >= 0.85 || latestAlignment <= 0.2
    ? "high"
    : latestDrift >= 0.67 || latestAlignment <= 0.4 || Boolean(latestEvent?.gate_locked)
      ? "medium"
      : "low";
  const completionRatio = Number((timelineSignalState.completed_slots.length / timelineSignalState.slot_count).toFixed(3));
  const mbspSurface = buildMbspSurfaceSynthesisState({
    latestPhase: String(latestEvent?.phase || ""),
    completionRatio,
    alignmentScore: latestAlignment,
    stabilityScore: Number(latestEvent?.semantic_state?.stability_score || 0),
    riskLevel,
    triggerCount: priorityQueue.length,
  });

  return {
    source: "workspace.timeline_signal_state",
    orchestration: {
      priority_order: ORCHESTRATION_PRIORITY_ORDER,
      priority_queue: priorityQueue,
      trigger_count: priorityQueue.length,
      highest_priority: priorityQueue[0]?.priority || "info",
    },
    semantic_metadata: {
      drift_score: latestDrift,
      stability_score: Number(latestEvent?.semantic_state?.stability_score || 0),
      alignment_score: latestAlignment,
    },
    phase_gate_state: {
      phase_gates: timelineSignalState.phase_gates,
      locked_phases: timelineSignalState.phase_gates.filter((gate) => gate.locked).map((gate) => gate.phase),
      unlocked_phases: timelineSignalState.phase_gates.filter((gate) => !gate.locked).map((gate) => gate.phase),
    },
    slot_progression: {
      slot_count: timelineSignalState.slot_count,
      completed_slots: timelineSignalState.completed_slots,
      completed_count: timelineSignalState.completed_slots.length,
      completion_ratio: completionRatio,
      latest_slot_index: Number(latestEvent?.slot_index || 0),
      latest_phase: String(latestEvent?.phase || ""),
    },
    synthesis: {
      risk_level: riskLevel,
      drift_trend: {
        direction: driftDirection,
        delta: driftDelta,
        sample_count: sortedEvents.length,
      },
      alignment_trajectory: {
        direction: alignmentDirection,
        delta: alignmentDelta,
        sample_count: sortedEvents.length,
      },
      mbsp_surface: mbspSurface,
    },
    latest_event: latestEvent,
  };
}
