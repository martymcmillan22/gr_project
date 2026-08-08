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
    timeline_entry: timelineEntry,
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
