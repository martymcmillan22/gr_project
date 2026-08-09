import { executeRrSemanticAction } from "../api/homepageApi";

export const SEMANTIC_ACTIONS = {
  ADVANCE_WORKFLOW_STEP: "advance_workflow_step",
  PREPARE_PUBLISHING_CHAPTER: "prepare_publishing_chapter",
  OPEN_RR_PROVENANCE_CHAIN: "open_rr_provenance_chain",
  REBALANCE_SUBJECT_MIX: "rebalance_subject_mix",
  REPAIR_PROVENANCE_CHAIN: "repair_provenance_chain",
  REALIGN_WORKFLOW_STEP: "realign_workflow_step",
  REGENERATE_CHAPTER_OUTLINE: "regenerate_chapter_outline",
  RESYNC_PUBLISHING_DIAGRAMS: "resync_publishing_diagrams",
  REBALANCE_SUBJECT_LOAD: "rebalance_subject_load",
  OPTIMIZE_WORKFLOW_PATH: "optimize_workflow_path",
  IMPROVE_PUBLISHING_READINESS: "improve_publishing_readiness",
  SHORTEN_WORKFLOW_PATH: "shorten_workflow_path",
  MERGE_SOP_STEPS: "merge_sop_steps",
  REALIGN_SUBJECT_DISTRIBUTION: "realign_subject_distribution",
  AUTO_ASSEMBLE_CHAPTER_OUTLINE: "auto_assemble_chapter_outline",
  IMPROVE_SUBJECT_BALANCE: "improve_subject_balance",
  RUN_SEMANTIC_IMPROVEMENT_CYCLE: "run_semantic_improvement_cycle",
};

export const CALCULUS_TIMELINE_SLOT_COUNT = 16;

export const ORCHESTRATION_PRIORITY_ORDER = ["critical", "warn", "info"];

const ORCHESTRATION_TRIGGER_ORDER = {
  drift_spike: 1,
  alignment_change: 2,
  slot_completion: 3,
  gate_unlock: 4,
};

function buildSlotRange(start, end) {
  const slots = [];
  for (let slot = start; slot <= end; slot += 1) {
    slots.push(slot);
  }
  return slots;
}

function clampScore(value) {
  return Math.max(0, Math.min(1, Number(value || 0)));
}

const CALCULUS_TIMELINE_PHASES = [
  { phase: "Ideas", slot_start: 1, slot_end: 4, depends_on_slots: [] },
  { phase: "Seeds", slot_start: 5, slot_end: 8, depends_on_slots: buildSlotRange(1, 4) },
  { phase: "Projects", slot_start: 9, slot_end: 12, depends_on_slots: buildSlotRange(1, 8) },
  { phase: "MVP", slot_start: 13, slot_end: 16, depends_on_slots: buildSlotRange(1, 12) },
  { phase: "Studio", slot_start: 17, slot_end: 20, depends_on_slots: buildSlotRange(1, 16) },
  { phase: "Enterprise", slot_start: 21, slot_end: 24, depends_on_slots: buildSlotRange(1, 16) },
];

function normalizeCompletedSlots(value) {
  const list = Array.isArray(value) ? value : [];
  return Array.from(new Set(
    list
      .map((item) => Number(item))
      .filter((item) => Number.isFinite(item) && item >= 1 && item <= CALCULUS_TIMELINE_SLOT_COUNT),
  )).sort((left, right) => left - right);
}

function buildPhaseGates(completedSlots) {
  return CALCULUS_TIMELINE_PHASES.map((phase) => {
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

function normalizeTimelineSemanticState(value = {}) {
  const state = value && typeof value === "object" ? value : {};
  return {
    drift_score: Number(state.drift_score || 0),
    stability_score: Number(state.stability_score || 0),
    alignment_score: Number(state.alignment_score || 0),
  };
}

function normalizeTimelineIndustryMetadata(value = {}) {
  const metadata = value && typeof value === "object" ? value : {};
  return {
    group_id: Number(metadata.group_id || 0) || null,
    group_name: String(metadata.group_name || ""),
    industry: String(metadata.industry || ""),
    raw_label: String(metadata.raw_label || ""),
  };
}

function normalizeTimelineSignalState(state = {}) {
  const next = state && typeof state === "object" ? state : {};
  const completedSlots = normalizeCompletedSlots(next.completed_slots);
  return {
    slot_count: CALCULUS_TIMELINE_SLOT_COUNT,
    completed_slots: completedSlots,
    phase_gates: Array.isArray(next.phase_gates) && next.phase_gates.length > 0
      ? next.phase_gates
      : buildPhaseGates(completedSlots),
    slot_events: next.slot_events && typeof next.slot_events === "object"
      ? next.slot_events
      : {},
    latest_event: next.latest_event && typeof next.latest_event === "object"
      ? next.latest_event
      : null,
  };
}

export function createTimelineSignalState() {
  return normalizeTimelineSignalState({});
}

export function buildTimelineSignalGroups(timelineSignalState = {}) {
  const slotEvents = timelineSignalState?.slot_events && typeof timelineSignalState.slot_events === "object"
    ? Object.values(timelineSignalState.slot_events)
    : [];

  if (!Array.isArray(slotEvents) || slotEvents.length === 0) {
    return [];
  }

  const grouped = new Map();
  slotEvents
    .filter((item) => item && typeof item === "object")
    .sort((left, right) => Number(left?.slot_index || 0) - Number(right?.slot_index || 0))
    .forEach((item) => {
      const subject = item?.industry_metadata?.group_name || "Timeline";
      const phase = item?.phase || "Unknown";
      const key = `${subject}::${phase}`;
      const current = grouped.get(key) || {
        subject,
        phase,
        count: 0,
        items: [],
        navigation_targets: ["middle_layer"],
      };
      current.count += 1;
      current.items.push({
        ...item,
        label: `Slot ${item.slot_index} · ${phase}`,
        surface: "middle_layer",
        compartment_id: Number(item.slot_index || 0),
        navigation: {
          surface: "middle_layer",
          compartment_id: Number(item.slot_index || 0),
        },
        breadcrumbs: [
          subject,
          item?.industry_metadata?.industry || "",
          `slot_${item.slot_index || "n/a"}`,
        ].filter(Boolean),
      });
      grouped.set(key, current);
    });

  return Array.from(grouped.values()).sort((left, right) => right.count - left.count);
}

function normalizeTimelineSlotEvents(timelineSignalState = {}) {
  const slotEvents = timelineSignalState?.slot_events && typeof timelineSignalState.slot_events === "object"
    ? Object.values(timelineSignalState.slot_events)
    : [];
  return Array.isArray(slotEvents)
    ? slotEvents
      .filter((item) => item && typeof item === "object")
      .sort((left, right) => Number(left?.slot_index || 0) - Number(right?.slot_index || 0))
    : [];
}

function buildMbspSurfaceSynthesisState({
  latestPhase = "",
  completionRatio = 0,
  alignmentScore = 0,
  stabilityScore = 0,
  riskLevel = "low",
  triggerCount = 0,
} = {}) {
  const normalizedLatestPhase = String(latestPhase || "").toLowerCase();
  const normalizedCompletionRatio = Number(completionRatio || 0);
  const normalizedAlignmentScore = Number(alignmentScore || 0);
  const normalizedStabilityScore = Number(stabilityScore || 0);
  const normalizedTriggerCount = Number(triggerCount || 0);
  const normalizedRiskLevel = String(riskLevel || "low");

  const studioReadinessScore = clampScore(
    (0.4 * normalizedCompletionRatio)
    + (0.35 * normalizedAlignmentScore)
    + (0.25 * normalizedStabilityScore),
  );
  const enterpriseReadinessScore = clampScore(
    (0.45 * normalizedAlignmentScore)
    + (0.35 * normalizedStabilityScore)
    + (0.2 * normalizedCompletionRatio)
    - (0.03 * normalizedTriggerCount),
  );

  let surfacePhase = normalizedLatestPhase;
  if (surfacePhase !== "studio" && surfacePhase !== "enterprise") {
    if (normalizedCompletionRatio >= 1) {
      surfacePhase = normalizedAlignmentScore >= 0.78
        && normalizedStabilityScore >= 0.72
        && normalizedRiskLevel !== "high"
        && normalizedTriggerCount <= 3
        ? "enterprise"
        : "studio";
    }
  }

  return {
    surface_phase: surfacePhase || normalizedLatestPhase || "ideas",
    surface_tiers: {
      studio: {
        phase: "studio",
        label: "creator_publisher_tier",
        unlocked: normalizedCompletionRatio >= 1 || normalizedLatestPhase === "studio" || normalizedLatestPhase === "enterprise",
        active: surfacePhase === "studio",
        readiness_score: Number(studioReadinessScore.toFixed(3)),
      },
      enterprise: {
        phase: "enterprise",
        label: "operational_organizational_tier",
        unlocked: normalizedCompletionRatio >= 1 || normalizedLatestPhase === "enterprise",
        active: surfacePhase === "enterprise",
        readiness_score: Number(enterpriseReadinessScore.toFixed(3)),
      },
    },
  };
}

export function buildTimelineOrchestrationGroups(timelineSignalState = {}) {
  const slotEvents = normalizeTimelineSlotEvents(timelineSignalState);
  const completedSlots = Array.isArray(timelineSignalState?.completed_slots) ? timelineSignalState.completed_slots : [];
  const phaseGates = Array.isArray(timelineSignalState?.phase_gates) ? timelineSignalState.phase_gates : [];

  const slotClusters = CALCULUS_TIMELINE_PHASES.map((phase) => {
    const slots = [];
    for (let slot = phase.slot_start; slot <= phase.slot_end; slot += 1) {
      slots.push(slot);
    }
    const completedCount = slots.filter((slot) => completedSlots.includes(slot)).length;
    return {
      phase: phase.phase,
      slots,
      completed_count: completedCount,
      completion_ratio: slots.length > 0 ? Number((completedCount / slots.length).toFixed(3)) : 0,
      locked: Boolean(phaseGates.find((gate) => gate.phase === phase.phase)?.locked),
    };
  });

  const semanticPhases = CALCULUS_TIMELINE_PHASES.map((phase) => {
    const events = slotEvents.filter((item) => String(item?.phase || "") === phase.phase);
    return {
      phase: phase.phase,
      event_count: events.length,
      latest_slot_index: events.length > 0 ? Number(events[events.length - 1]?.slot_index || 0) : null,
      drift_average: events.length > 0
        ? Number((events.reduce((sum, item) => sum + Number(item?.semantic_state?.drift_score || 0), 0) / events.length).toFixed(3))
        : 0,
      alignment_average: events.length > 0
        ? Number((events.reduce((sum, item) => sum + Number(item?.semantic_state?.alignment_score || 0), 0) / events.length).toFixed(3))
        : 0,
      locked: Boolean(phaseGates.find((gate) => gate.phase === phase.phase)?.locked),
    };
  });

  const driftRiskGroups = { high: [], medium: [], low: [] };
  slotEvents.forEach((item) => {
    const drift = Number(item?.semantic_state?.drift_score || 0);
    if (drift >= 0.67) {
      driftRiskGroups.high.push(item);
    } else if (drift >= 0.34) {
      driftRiskGroups.medium.push(item);
    } else {
      driftRiskGroups.low.push(item);
    }
  });

  return {
    slot_clusters: slotClusters,
    semantic_phases: semanticPhases,
    drift_risk_groups: driftRiskGroups,
  };
}

export function evaluateTimelineOrchestrationPolicies(timelineSignalState = {}) {
  const latest = timelineSignalState?.latest_event && typeof timelineSignalState.latest_event === "object"
    ? timelineSignalState.latest_event
    : null;
  const completedSlots = Array.isArray(timelineSignalState?.completed_slots) ? timelineSignalState.completed_slots : [];
  const phaseGates = Array.isArray(timelineSignalState?.phase_gates) ? timelineSignalState.phase_gates : [];

  const triggers = [];
  const driftScore = Number(latest?.semantic_state?.drift_score || 0);
  const alignmentScore = Number(latest?.semantic_state?.alignment_score || 0);
  const slotCompleted = Boolean(latest?.slot_completed);
  const gateLocked = Boolean(latest?.gate_locked);

  if (slotCompleted) {
    triggers.push({
      id: "slot_completion",
      severity: "info",
      priority: "info",
      message: `Slot ${latest?.slot_index || "?"} completed. Advance deterministic workflow choreography.`,
      action: SEMANTIC_ACTIONS.ADVANCE_WORKFLOW_STEP,
      navigation: { surface: "rr_workflows" },
    });
  }

  if (driftScore >= 0.67) {
    const driftPriority = driftScore >= 0.85 ? "critical" : "warn";
    triggers.push({
      id: "drift_spike",
      severity: driftPriority,
      priority: driftPriority,
      message: `Drift spike detected (${driftScore.toFixed(2)}). Route to guidance stabilization.`,
      action: SEMANTIC_ACTIONS.REPAIR_PROVENANCE_CHAIN,
      navigation: { surface: "rr_va" },
    });
  }

  if (alignmentScore <= 0.4) {
    const alignmentPriority = alignmentScore <= 0.2 ? "critical" : "warn";
    triggers.push({
      id: "alignment_change",
      severity: alignmentPriority,
      priority: alignmentPriority,
      message: `Alignment dropped (${alignmentScore.toFixed(2)}). Recommend semantic realignment.`,
      action: SEMANTIC_ACTIONS.REALIGN_WORKFLOW_STEP,
      navigation: { surface: "middle_layer" },
    });
  }

  if (slotCompleted && !gateLocked) {
    const completedKey = Number(latest?.slot_index || 0);
    const phaseUnlockMap = {
      4: "Seeds",
      8: "Projects",
      12: "MVP",
      16: "Studio",
    };
    const unlockedPhase = phaseUnlockMap[completedKey];
    if (unlockedPhase) {
      const gate = phaseGates.find((item) => item.phase === unlockedPhase);
      if (gate && !gate.locked) {
        triggers.push({
          id: "gate_unlock",
          severity: "info",
          priority: "info",
          message: `${unlockedPhase} gate unlocked. Cross-surface routing can advance.`,
          action: SEMANTIC_ACTIONS.ADVANCE_WORKFLOW_STEP,
          navigation: { surface: "workflow_swimlanes" },
        });
      }
    }
  }

  return {
    latest_slot_index: Number(latest?.slot_index || 0),
    completed_count: completedSlots.length,
    gate_locked: gateLocked,
    drift_score: driftScore,
    alignment_score: alignmentScore,
    triggers,
  };
}

function resolveOrchestrationPriorityRank(priority) {
  const value = String(priority || "info").toLowerCase();
  const index = ORCHESTRATION_PRIORITY_ORDER.indexOf(value);
  return index >= 0 ? index : ORCHESTRATION_PRIORITY_ORDER.length;
}

function resolveOrchestrationTriggerOrderRank(triggerId) {
  const key = String(triggerId || "");
  return ORCHESTRATION_TRIGGER_ORDER[key] || Number.MAX_SAFE_INTEGER;
}

export function buildTimelineOrchestrationPriorityQueue(timelineSignalState = {}) {
  const policy = evaluateTimelineOrchestrationPolicies(timelineSignalState);
  const triggers = Array.isArray(policy?.triggers) ? policy.triggers : [];

  return triggers
    .map((trigger, index) => {
      const priority = String(trigger?.priority || trigger?.severity || "info").toLowerCase();
      return {
        ...trigger,
        priority,
        priority_rank: resolveOrchestrationPriorityRank(priority),
        trigger_order_rank: resolveOrchestrationTriggerOrderRank(trigger?.id),
        sequence: index,
      };
    })
    .sort((left, right) => {
      if (left.priority_rank !== right.priority_rank) {
        return left.priority_rank - right.priority_rank;
      }
      if (left.trigger_order_rank !== right.trigger_order_rank) {
        return left.trigger_order_rank - right.trigger_order_rank;
      }
      if (left.sequence !== right.sequence) {
        return left.sequence - right.sequence;
      }
      return String(left.id || "").localeCompare(String(right.id || ""));
    });
}

export function buildTimelineDriftTrend(timelineSignalState = {}) {
  const slotEvents = normalizeTimelineSlotEvents(timelineSignalState);
  if (slotEvents.length < 2) {
    return {
      direction: "stable",
      latest: slotEvents.length === 1 ? Number(slotEvents[0]?.semantic_state?.drift_score || 0) : 0,
      delta: 0,
      sample_count: slotEvents.length,
    };
  }

  const first = Number(slotEvents[0]?.semantic_state?.drift_score || 0);
  const last = Number(slotEvents[slotEvents.length - 1]?.semantic_state?.drift_score || 0);
  const delta = Number((last - first).toFixed(3));

  let direction = "stable";
  if (delta >= 0.05) {
    direction = "rising";
  } else if (delta <= -0.05) {
    direction = "falling";
  }

  return {
    direction,
    latest: Number(last.toFixed(3)),
    delta,
    sample_count: slotEvents.length,
  };
}

export function buildTimelineAlignmentTrajectory(timelineSignalState = {}) {
  const slotEvents = normalizeTimelineSlotEvents(timelineSignalState);
  if (slotEvents.length < 2) {
    return {
      direction: "stable",
      latest: slotEvents.length === 1 ? Number(slotEvents[0]?.semantic_state?.alignment_score || 0) : 0,
      delta: 0,
      sample_count: slotEvents.length,
    };
  }

  const first = Number(slotEvents[0]?.semantic_state?.alignment_score || 0);
  const last = Number(slotEvents[slotEvents.length - 1]?.semantic_state?.alignment_score || 0);
  const delta = Number((last - first).toFixed(3));

  let direction = "stable";
  if (delta >= 0.05) {
    direction = "improving";
  } else if (delta <= -0.05) {
    direction = "declining";
  }

  return {
    direction,
    latest: Number(last.toFixed(3)),
    delta,
    sample_count: slotEvents.length,
  };
}

export function buildTimelineRiskClusters(timelineSignalState = {}) {
  const slotEvents = normalizeTimelineSlotEvents(timelineSignalState);
  const clusters = {
    high: [],
    medium: [],
    low: [],
  };

  slotEvents.forEach((event) => {
    const drift = Number(event?.semantic_state?.drift_score || 0);
    const alignment = Number(event?.semantic_state?.alignment_score || 0);
    const gateLocked = Boolean(event?.gate_locked);

    let riskLevel = "low";
    if (drift >= 0.67 || alignment <= 0.4 || gateLocked) {
      riskLevel = "medium";
    }
    if (drift >= 0.85 || alignment <= 0.2) {
      riskLevel = "high";
    }

    clusters[riskLevel].push(event);
  });

  const primary = clusters.high.length > 0
    ? "high"
    : clusters.medium.length > 0
      ? "medium"
      : "low";

  return {
    primary,
    high: clusters.high,
    medium: clusters.medium,
    low: clusters.low,
    counts: {
      high: clusters.high.length,
      medium: clusters.medium.length,
      low: clusters.low.length,
    },
  };
}

export function buildUnifiedPlatformIntelligenceState(timelineSignalState = {}) {
  const normalizedState = normalizeTimelineSignalState(timelineSignalState);
  const latestEvent = normalizedState.latest_event || null;
  const phaseGates = Array.isArray(normalizedState.phase_gates) ? normalizedState.phase_gates : [];
  const completedSlots = Array.isArray(normalizedState.completed_slots) ? normalizedState.completed_slots : [];
  const priorityQueue = buildTimelineOrchestrationPriorityQueue(normalizedState);
  const groups = buildTimelineOrchestrationGroups(normalizedState);
  const driftTrend = buildTimelineDriftTrend(normalizedState);
  const alignmentTrajectory = buildTimelineAlignmentTrajectory(normalizedState);
  const riskClusters = buildTimelineRiskClusters(normalizedState);
  const latestDriftScore = Number(latestEvent?.semantic_state?.drift_score || 0);
  const latestStabilityScore = Number(latestEvent?.semantic_state?.stability_score || 0);
  const latestAlignmentScore = Number(latestEvent?.semantic_state?.alignment_score || 0);
  const completionRatio = Number((completedSlots.length / Number(normalizedState.slot_count || CALCULUS_TIMELINE_SLOT_COUNT)).toFixed(3));
  const mbspSurface = buildMbspSurfaceSynthesisState({
    latestPhase: String(latestEvent?.phase || ""),
    completionRatio,
    alignmentScore: latestAlignmentScore,
    stabilityScore: latestStabilityScore,
    riskLevel: riskClusters.primary,
    triggerCount: priorityQueue.length,
  });

  return {
    source: "timeline_signal_state",
    orchestration: {
      priority_order: ORCHESTRATION_PRIORITY_ORDER,
      priority_queue: priorityQueue,
      trigger_count: priorityQueue.length,
      highest_priority: priorityQueue[0]?.priority || "info",
    },
    semantic_metadata: {
      drift_score: latestDriftScore,
      stability_score: latestStabilityScore,
      alignment_score: latestAlignmentScore,
    },
    industry_context: {
      group_id: Number(latestEvent?.industry_metadata?.group_id || 0) || null,
      group_name: String(latestEvent?.industry_metadata?.group_name || ""),
      industry: String(latestEvent?.industry_metadata?.industry || ""),
      raw_label: String(latestEvent?.industry_metadata?.raw_label || ""),
    },
    phase_gate_state: {
      phase_gates: phaseGates,
      locked_phases: phaseGates.filter((gate) => gate?.locked).map((gate) => gate.phase),
      unlocked_phases: phaseGates.filter((gate) => !gate?.locked).map((gate) => gate.phase),
    },
    slot_progression: {
      slot_count: Number(normalizedState.slot_count || CALCULUS_TIMELINE_SLOT_COUNT),
      completed_slots: completedSlots,
      completed_count: completedSlots.length,
      completion_ratio: completionRatio,
      latest_slot_index: Number(latestEvent?.slot_index || 0),
      latest_phase: String(latestEvent?.phase || ""),
    },
    groupings: groups,
    synthesis: {
      risk_clusters: riskClusters,
      drift_trend: driftTrend,
      alignment_trajectory: alignmentTrajectory,
      mbsp_surface: mbspSurface,
    },
    latest_event: latestEvent,
  };
}

export function reduceTimelineSlotSignal(previousState = {}, detail = {}) {
  const current = normalizeTimelineSignalState(previousState);
  const event = normalizeTimelineSlotEventEnvelope(detail);
  if (!Number.isFinite(event.slot_index) || event.slot_index < 1 || event.slot_index > CALCULUS_TIMELINE_SLOT_COUNT) {
    return current;
  }

  const completedSlots = event.completed_slots.length > 0
    ? normalizeCompletedSlots(event.completed_slots)
    : event.slot_completed
      ? normalizeCompletedSlots([...current.completed_slots, event.slot_index])
      : current.completed_slots;

  const normalizedEvent = {
    ...event,
    completed_slots: completedSlots,
    semantic_state: normalizeTimelineSemanticState(event.semantic_state),
    industry_metadata: normalizeTimelineIndustryMetadata(event.industry_metadata),
  };

  return {
    slot_count: CALCULUS_TIMELINE_SLOT_COUNT,
    completed_slots: completedSlots,
    phase_gates: buildPhaseGates(completedSlots),
    slot_events: {
      ...current.slot_events,
      [event.slot_index]: normalizedEvent,
    },
    latest_event: normalizedEvent,
  };
}

export function normalizeTimelineSlotEventEnvelope(detail = {}) {
  const eventType = String(detail.event_type || detail.eventType || "slot_state_change");
  const slotIndex = Number(detail.slot_index || detail.slotIndex || 0);
  const phase = String(detail.phase || "");
  const temporalAlignment = String(detail.temporal_alignment || detail.temporalAlignment || "");
  const calculusOperation = String(detail.calculus_operation || detail.calculusOperation || "");
  const gateLocked = Boolean(
    detail.gate_locked !== undefined
      ? detail.gate_locked
      : detail.isLocked,
  );
  const slotCompleted = Boolean(
    detail.slot_completed !== undefined
      ? detail.slot_completed
      : detail.isCompleted,
  );
  const industryMetadata = detail.industry_metadata && typeof detail.industry_metadata === "object"
    ? detail.industry_metadata
    : detail.industryMetadata && typeof detail.industryMetadata === "object"
      ? detail.industryMetadata
      : {};
  const semanticState = detail.semantic_state && typeof detail.semantic_state === "object"
    ? detail.semantic_state
    : detail.semanticState && typeof detail.semanticState === "object"
      ? detail.semanticState
      : {};
  const completedSlots = Array.isArray(detail.completed_slots)
    ? detail.completed_slots.map((item) => Number(item)).filter((item) => Number.isFinite(item) && item > 0)
    : Array.isArray(detail.completedSlots)
      ? detail.completedSlots.map((item) => Number(item)).filter((item) => Number.isFinite(item) && item > 0)
      : [];

  return {
    event_type: eventType,
    event_version: String(detail.event_version || detail.eventVersion || "v1"),
    source: String(detail.source || "frontend.timeline.grid"),
    slot_index: Number.isFinite(slotIndex) ? slotIndex : 0,
    phase,
    temporal_alignment: temporalAlignment,
    calculus_operation: calculusOperation,
    gate_locked: gateLocked,
    slot_completed: slotCompleted,
    industry_metadata: industryMetadata,
    semantic_state: semanticState,
    completed_slots: completedSlots,
    // compatibility aliases for existing consumers/tests
    eventType,
    eventVersion: String(detail.event_version || detail.eventVersion || "v1"),
    slotIndex: Number.isFinite(slotIndex) ? slotIndex : 0,
    temporalAlignment,
    calculusOperation,
    isLocked: gateLocked,
    isCompleted: slotCompleted,
    industryMetadata,
    semanticState,
    completedSlots,
  };
}

export function isTimelineSlotEventEnvelope(detail = {}) {
  const eventType = String(detail?.event_type || detail?.eventType || "");
  return eventType === "slot_state_change"
    || eventType === "slot_completion"
    || eventType === "middle_layer.timeline.slot_state"
    || eventType === "middle_layer.timeline.slot_state_changed";
}

const ACTION_LOG_LIMIT = 24;
const STABILIZATION_ACTION_SET = new Set([
  SEMANTIC_ACTIONS.REBALANCE_SUBJECT_MIX,
  SEMANTIC_ACTIONS.REPAIR_PROVENANCE_CHAIN,
  SEMANTIC_ACTIONS.REALIGN_WORKFLOW_STEP,
  SEMANTIC_ACTIONS.REGENERATE_CHAPTER_OUTLINE,
  SEMANTIC_ACTIONS.RESYNC_PUBLISHING_DIAGRAMS,
]);
const OPTIMIZATION_ACTION_SET = new Set([
  SEMANTIC_ACTIONS.REBALANCE_SUBJECT_LOAD,
  SEMANTIC_ACTIONS.OPTIMIZE_WORKFLOW_PATH,
  SEMANTIC_ACTIONS.IMPROVE_PUBLISHING_READINESS,
  SEMANTIC_ACTIONS.SHORTEN_WORKFLOW_PATH,
  SEMANTIC_ACTIONS.MERGE_SOP_STEPS,
  SEMANTIC_ACTIONS.REALIGN_SUBJECT_DISTRIBUTION,
  SEMANTIC_ACTIONS.AUTO_ASSEMBLE_CHAPTER_OUTLINE,
  SEMANTIC_ACTIONS.IMPROVE_SUBJECT_BALANCE,
  SEMANTIC_ACTIONS.RUN_SEMANTIC_IMPROVEMENT_CYCLE,
]);

export function normalizeBreadcrumbs(value) {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    if (typeof item === "string") {
      return item ? [item] : [];
    }

    if (item && typeof item === "object") {
      const pieces = [item.label, item.subject, item.phase].filter(Boolean);
      return pieces.length > 0 ? [pieces.join(" · ")] : [];
    }

    return [];
  });
}

export function dispatchSemanticNavigation(navigation = {}, source = "semantic-os") {
  const surface = String(navigation.surface || "");
  const businessId = Number(navigation.business_id);
  const compartmentId = Number(navigation.compartment_id);

  if (surface === "rr_dashboard") {
    if (Number.isFinite(businessId) && businessId > 0) {
      window.dispatchEvent(new CustomEvent("grassroots:rr-focus-node", { detail: { businessId, source } }));
    }
    if (Number.isFinite(compartmentId)) {
      window.dispatchEvent(
        new CustomEvent("grassroots:rr-focus-lane", {
          detail: { compartmentId, source },
        }),
      );
      window.dispatchEvent(
        new CustomEvent("grassroots:rr-focus-map-cell", {
          detail: { compartmentId, source },
        }),
      );
    }
    return;
  }

  if (surface === "rr_detail") {
    if (Number.isFinite(businessId) && businessId > 0) {
      window.dispatchEvent(new CustomEvent("grassroots:rr-focus-node", { detail: { businessId, source } }));
    }
    window.dispatchEvent(new CustomEvent("grassroots:semantic-panel-select", { detail: { panelId: "rr_detail" } }));
    return;
  }

  if (surface === "middle_layer") {
    window.dispatchEvent(
      new CustomEvent("grassroots:rr-open-middle-layer", {
        detail: {
          businessId: Number.isFinite(businessId) ? businessId : undefined,
          source,
        },
      }),
    );
    return;
  }

  if (surface === "workflow_swimlanes" || surface === "rr_workflows") {
    window.dispatchEvent(new CustomEvent("grassroots:rr-open-workflow", { detail: { source } }));
    window.dispatchEvent(new CustomEvent("grassroots:semantic-panel-select", { detail: { panelId: "rr_workflows" } }));
    return;
  }

  if (surface === "publishing_layer" || surface === "rr_publishing") {
    window.dispatchEvent(new CustomEvent("grassroots:semantic-panel-select", { detail: { panelId: "rr_publishing" } }));
    return;
  }

  if (surface === "va_guidance" || surface === "rr_va") {
    window.dispatchEvent(new CustomEvent("grassroots:semantic-panel-select", { detail: { panelId: "rr_va" } }));
    return;
  }

  if (surface === "rr_industry_map") {
    window.dispatchEvent(new CustomEvent("grassroots:semantic-panel-select", { detail: { panelId: "rr_industry_map" } }));
  }
}

export function normalizeTimelineGroups(groups) {
  if (!Array.isArray(groups)) {
    return [];
  }

  return groups
    .map((group) => ({
      ...group,
      items: Array.isArray(group?.items) ? group.items : [],
      navigation_targets: Array.isArray(group?.navigation_targets) ? group.navigation_targets : [],
    }))
    .sort((left, right) => {
      const leftCount = Number(left?.count || 0);
      const rightCount = Number(right?.count || 0);
      if (rightCount !== leftCount) {
        return rightCount - leftCount;
      }
      const leftLabel = `${left?.subject || ""} ${left?.phase || ""}`;
      const rightLabel = `${right?.subject || ""} ${right?.phase || ""}`;
      return leftLabel.localeCompare(rightLabel);
    });
}

export function normalizeSemanticActionLogEntry(entry, index = 0) {
  const next = entry && typeof entry === "object" ? entry : {};
  const timelineEntry = next.timeline_entry && typeof next.timeline_entry === "object" ? next.timeline_entry : {};
  const normalizedTimelineEntry = isTimelineSlotEventEnvelope(timelineEntry)
    ? normalizeTimelineSlotEventEnvelope(timelineEntry)
    : timelineEntry;
  const provenanceUpdate = next.provenance_update && typeof next.provenance_update === "object" ? next.provenance_update : {};
  const publishingSignal = next.publishing_signal && typeof next.publishing_signal === "object" ? next.publishing_signal : {};
  const workflowStepResult = next.workflow_step_result && typeof next.workflow_step_result === "object" ? next.workflow_step_result : {};
  const compartmentId = Number(next.compartment_id);
  return {
    id: String(next.recorded_at || timelineEntry.label || `action-${index}`),
    recorded_at: next.recorded_at || "",
    action: String(next.action || "unknown_action"),
    status: String(next.status || "unknown"),
    source_surface: String(next.source_surface || "semantic_os"),
    business_id: next.business_id,
    compartment_id: Number.isFinite(compartmentId) ? compartmentId : null,
    subject: String(next.subject || "Unknown"),
    phase: String(next.phase || "Unknown"),
    breadcrumbs: normalizeBreadcrumbs(next.breadcrumbs || timelineEntry.breadcrumbs || []),
    timeline_entry: normalizedTimelineEntry,
    provenance_update: provenanceUpdate,
    publishing_signal: publishingSignal,
    workflow_step_result: workflowStepResult,
  };
}

export function mergeSemanticActionHistory(existingEntries = [], incomingEntries = []) {
  const mergedMap = new Map();
  [...existingEntries, ...incomingEntries].forEach((entry, index) => {
    const normalized = normalizeSemanticActionLogEntry(entry, index);
    const key = `${normalized.recorded_at || normalized.id}-${normalized.action}-${normalized.business_id || "x"}-${normalized.compartment_id || "x"}`;
    mergedMap.set(key, normalized);
  });

  return Array.from(mergedMap.values())
    .sort((left, right) => String(left.recorded_at || "").localeCompare(String(right.recorded_at || "")))
    .slice(-ACTION_LOG_LIMIT);
}

export function groupWorkflowActionsBySubjectPhase(actionLog = []) {
  const map = new Map();
  actionLog.forEach((entry) => {
    const item = normalizeSemanticActionLogEntry(entry);
    const key = `${item.subject}::${item.phase}`;
    const current = map.get(key) || {
      subject: item.subject,
      phase: item.phase,
      count: 0,
      actions: [],
      statuses: {},
    };
    current.count += 1;
    current.actions.push(item.action);
    current.statuses[item.status] = (current.statuses[item.status] || 0) + 1;
    map.set(key, current);
  });
  return Array.from(map.values()).sort((left, right) => right.count - left.count);
}

export function buildSemanticActionFeedback({ actionLog = [], semanticHealth = {} } = {}) {
  const grouped = groupWorkflowActionsBySubjectPhase(actionLog);
  const recent = actionLog.slice(-8);
  const failed = recent.filter((item) => String(item.status) === "failed").length;
  const blocked = recent.filter((item) => String(item.status) === "blocked").length;
  const driftDetected = failed >= 2 || blocked >= 3;
  const adaptiveHints = [];

  if (grouped.length > 0) {
    adaptiveHints.push(`Focus next action in ${grouped[0].subject} (${grouped[0].phase}) to keep flow coherent.`);
  }
  if (driftDetected) {
    adaptiveHints.push("Action drift detected. Route through RR provenance chain before workflow execution.");
  }
  if (!semanticHealth?.ready) {
    adaptiveHints.push("Semantic OS is not fully ready. Resolve readiness checks before publishing automation.");
  }

  return {
    grouped_actions: grouped,
    drift_detected: driftDetected,
    recent_failures: failed,
    recent_blocked: blocked,
    adaptive_hints: adaptiveHints,
    drift_detection: {
      severity: driftDetected ? "medium" : "low",
      score: driftDetected ? failed + blocked : 0,
      workflow_stalled: false,
      subject_imbalance: grouped.length > 0 && grouped[0].count >= 4,
      provenance_gaps: 0,
      timeline_cluster_pressure: grouped.length > 0 ? grouped[0].count : 0,
      publishing_gap: false,
      subject_drift_chips: grouped.slice(0, 3).map((item) => ({
        subject: item.subject,
        phase: item.phase,
        severity: item.count >= 3 ? "warn" : "monitor",
        reason: "Repeated semantic actions in this subject-phase lane.",
        count: item.count,
      })),
    },
    stabilization_loop: {
      status: driftDetected ? "active" : "monitor",
      progress: {
        total_recommendations: driftDetected ? 1 : 0,
        executed_corrections: 0,
        pending_corrections: driftDetected ? 1 : 0,
      },
      recommendations: driftDetected
        ? [{ action: SEMANTIC_ACTIONS.REPAIR_PROVENANCE_CHAIN, label: "Repair provenance chain", reason: "Fallback drift correction suggestion." }]
        : [],
    },
    optimization_loop: {
      status: driftDetected ? "active" : "monitor",
      signals: {
        subject_mix_score: driftDetected ? 72 : 100,
        workflow_efficiency_score: driftDetected ? 74 : 100,
        publishing_readiness_score: driftDetected ? 76 : 100,
        optimization_pressure: driftDetected ? 28 : 0,
        trend: driftDetected ? "monitor" : "improving",
        dominant_subject: grouped[0]?.subject || null,
        provenance_depth_ready: Boolean(semanticHealth?.partial_hydration?.provenance),
      },
      progress: {
        total_recommendations: driftDetected ? 1 : 0,
        executed_optimizations: 0,
        pending_optimizations: driftDetected ? 1 : 0,
        improvement_cycles: 0,
      },
      auto_balancing: {
        required: driftDetected,
        target_subject: grouped[0]?.subject || null,
        target_compartment_id: grouped[0]?.compartment_id || null,
        message: "Fallback optimization monitoring from local action history.",
      },
      recommendations: driftDetected
        ? [{ action: SEMANTIC_ACTIONS.OPTIMIZE_WORKFLOW_PATH, label: "Optimize workflow path", reason: "Fallback optimization recommendation." }]
        : [],
    },
    drift_alerts: driftDetected
      ? [{ type: "semantic_action_drift", severity: "warn", message: "Action drift detected from local history fallback." }]
      : [],
  };
}

export function normalizeSemanticFeedbackLoop(feedbackLoop = {}, fallbackOptions = {}) {
  if (feedbackLoop && typeof feedbackLoop === "object" && feedbackLoop.drift_detection) {
    const driftDetection = feedbackLoop.drift_detection || {};
    const stabilizationLoop = feedbackLoop.stabilization_loop || {};
    const optimizationLoop = feedbackLoop.optimization_loop || {};
    return {
      adaptive_hints: Array.isArray(feedbackLoop.adaptive_hints) ? feedbackLoop.adaptive_hints : [],
      stability_signals: feedbackLoop.stability_signals || {},
      drift_alerts: Array.isArray(feedbackLoop.drift_alerts) ? feedbackLoop.drift_alerts : [],
      drift_detected: Boolean((feedbackLoop.stability_signals || {}).drift_detected),
      recent_failures: Number((feedbackLoop.stability_signals || {}).recent_failures || 0),
      recent_blocked: Number((feedbackLoop.stability_signals || {}).recent_blocked || 0),
      drift_detection: {
        severity: String(driftDetection.severity || "low"),
        score: Number(driftDetection.score || 0),
        workflow_stalled: Boolean(driftDetection.workflow_stalled),
        subject_imbalance: Boolean(driftDetection.subject_imbalance),
        provenance_gaps: Number(driftDetection.provenance_gaps || 0),
        timeline_cluster_pressure: Number(driftDetection.timeline_cluster_pressure || 0),
        publishing_gap: Boolean(driftDetection.publishing_gap),
        subject_drift_chips: Array.isArray(driftDetection.subject_drift_chips) ? driftDetection.subject_drift_chips : [],
      },
      stabilization_loop: {
        status: String(stabilizationLoop.status || "monitor"),
        progress: stabilizationLoop.progress || { total_recommendations: 0, executed_corrections: 0, pending_corrections: 0 },
        recommendations: Array.isArray(stabilizationLoop.recommendations) ? stabilizationLoop.recommendations : [],
      },
      optimization_loop: {
        status: String(optimizationLoop.status || "monitor"),
        signals: optimizationLoop.signals || {
          subject_mix_score: 100,
          workflow_efficiency_score: 100,
          publishing_readiness_score: 100,
          optimization_pressure: 0,
          trend: "monitor",
          dominant_subject: null,
          provenance_depth_ready: false,
        },
        progress: optimizationLoop.progress || {
          total_recommendations: 0,
          executed_optimizations: 0,
          pending_optimizations: 0,
          improvement_cycles: 0,
        },
        auto_balancing: optimizationLoop.auto_balancing || {
          required: false,
          target_subject: null,
          target_compartment_id: null,
          message: "Optimization loop is monitoring baseline state.",
        },
        recommendations: Array.isArray(optimizationLoop.recommendations) ? optimizationLoop.recommendations : [],
      },
    };
  }

  return buildSemanticActionFeedback(fallbackOptions);
}

export function buildDriftReflection(feedbackLoop = {}) {
  const normalized = normalizeSemanticFeedbackLoop(feedbackLoop);
  const drift = normalized.drift_detection || {};
  return {
    severity: String(drift.severity || "low"),
    score: Number(drift.score || 0),
    warnings: normalized.drift_alerts || [],
    subjectChips: Array.isArray(drift.subject_drift_chips) ? drift.subject_drift_chips : [],
    stabilization: normalized.stabilization_loop || { status: "monitor", progress: {}, recommendations: [] },
    statusLine: normalized.drift_detected
      ? `Drift detected (${String(drift.severity || "medium")}, score ${Number(drift.score || 0)}).`
      : "No semantic drift detected.",
  };
}

export function buildOptimizationReflection(feedbackLoop = {}) {
  const normalized = normalizeSemanticFeedbackLoop(feedbackLoop);
  const optimization = normalized.optimization_loop || {};
  const signals = optimization.signals || {};
  const progress = optimization.progress || {};
  const recommendations = Array.isArray(optimization.recommendations) ? optimization.recommendations : [];
  const pressure = Number(signals.optimization_pressure || 0);
  return {
    status: String(optimization.status || "monitor"),
    subjectMixScore: Number(signals.subject_mix_score || 0),
    workflowEfficiencyScore: Number(signals.workflow_efficiency_score || 0),
    publishingReadinessScore: Number(signals.publishing_readiness_score || 0),
    optimizationPressure: pressure,
    trend: String(signals.trend || "monitor"),
    dominantSubject: signals.dominant_subject || "Unknown",
    provenanceDepthReady: Boolean(signals.provenance_depth_ready),
    autoBalancing: optimization.auto_balancing || { required: false },
    progress: {
      totalRecommendations: Number(progress.total_recommendations || 0),
      executedOptimizations: Number(progress.executed_optimizations || 0),
      pendingOptimizations: Number(progress.pending_optimizations || 0),
      improvementCycles: Number(progress.improvement_cycles || 0),
    },
    recommendations,
    statusLine: pressure >= 30
      ? `Optimization pressure ${pressure}. Prioritize subject balancing and workflow path improvement.`
      : `Optimization pressure ${pressure}. Semantic OS optimization remains stable.`,
  };
}

export function isStabilizationAction(action) {
  return STABILIZATION_ACTION_SET.has(String(action || ""));
}

export function isOptimizationAction(action) {
  return OPTIMIZATION_ACTION_SET.has(String(action || ""));
}

export async function executeSemanticAction({
  action,
  request = {},
  source = "semantic-os",
  semanticHealth = {},
} = {}) {
  const checks = Array.isArray(semanticHealth?.checks) ? semanticHealth.checks : [];
  const blockedBy = checks.filter((item) => item?.status !== "pass").map((item) => item?.surface).filter(Boolean);
  const isReady = Boolean(semanticHealth?.ready);
  const stabilizationAction = isStabilizationAction(action);
  const optimizationAction = isOptimizationAction(action);

  if (!isReady && !stabilizationAction && !optimizationAction) {
    const blockedResult = {
      status: "blocked",
      detail: "Semantic OS health checks are not ready for automation.",
      blocked_by: blockedBy,
    };
    window.dispatchEvent(new CustomEvent("grassroots:semantic-action-result", { detail: blockedResult }));
    return blockedResult;
  }

  const payload = {
    action,
    surface: source,
    ...request,
  };
  const result = await executeRrSemanticAction(payload);

  if (result?.status === "executed") {
    const timelineNavigation = {
      surface: result?.timeline_entry?.surface,
      business_id: result?.timeline_entry?.business_id,
      compartment_id: result?.timeline_entry?.compartment_id,
    };
    dispatchSemanticNavigation(timelineNavigation, "semantic-action-engine");
  }

  window.dispatchEvent(new CustomEvent("grassroots:semantic-action-result", { detail: result }));

  return result;
}
