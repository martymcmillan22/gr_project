import { buildDriftReflection, buildOptimizationReflection, buildUnifiedPlatformIntelligenceState, normalizeSemanticActionLogEntry, normalizeSemanticFeedbackLoop } from "./semanticOsHelpers";

function renderHintText(hint) {
  if (typeof hint === "string") {
    return hint;
  }
  if (hint && typeof hint === "object") {
    return String(hint.message || hint.type || "semantic hint");
  }
  return "semantic hint";
}

function chipColorForEntry(entry) {
  const compartment = Number(entry?.compartment_id);
  const base = Number.isFinite(compartment) ? compartment % 4 : 0;
  if (base === 0) {
    return "rgba(220, 38, 38, 0.15)";
  }
  if (base === 1) {
    return "rgba(37, 99, 235, 0.15)";
  }
  if (base === 2) {
    return "rgba(22, 163, 74, 0.15)";
  }
  return "rgba(245, 158, 11, 0.16)";
}

export default function SemanticActionLogPanel({
  panelId = "semantic-action-log-panel",
  actionHistory,
  feedbackLoop,
  timelineSignalState,
  unifiedIntelligenceState,
}) {
  const history = Array.isArray(actionHistory) ? actionHistory : [];
  const feedback = normalizeSemanticFeedbackLoop(feedbackLoop || {}, { actionLog: history });
  const driftReflection = buildDriftReflection(feedback);
  const optimizationReflection = buildOptimizationReflection(feedback);
  const resolvedIntelligenceState = (unifiedIntelligenceState && typeof unifiedIntelligenceState === "object")
    ? unifiedIntelligenceState
    : buildUnifiedPlatformIntelligenceState(timelineSignalState || {});
  const mbspSurface = resolvedIntelligenceState?.synthesis?.mbsp_surface || { surface_phase: "n/a", surface_tiers: {} };
  const latestTimelineEvent = timelineSignalState?.latest_event || null;
  const completedTimelineSlots = Array.isArray(timelineSignalState?.completed_slots) ? timelineSignalState.completed_slots : [];

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">Semantic Action Log</p>
          <h2>Recent action execution history</h2>
        </div>
      </div>

      <div className="rr-node-chip-row">
        <span>Recent failures {feedback.recent_failures || 0}</span>
        <span>Recent blocked {feedback.recent_blocked || 0}</span>
        <span>Drift {feedback.drift_detected ? "detected" : "clear"}</span>
        <span>Severity {driftReflection.severity}</span>
        <span>Score {driftReflection.score}</span>
      </div>
      <div className="rr-node-chip-row">
        <span>Timeline slots {completedTimelineSlots.length}/16</span>
        <span>Slot {latestTimelineEvent?.slot_index || "n/a"}</span>
        <span>Phase {latestTimelineEvent?.phase || "n/a"}</span>
        <span>{latestTimelineEvent?.industry_metadata?.group_name || "n/a"}</span>
        <span>{latestTimelineEvent?.industry_metadata?.industry || "n/a"}</span>
      </div>
      <div className="rr-node-chip-row">
        <span data-intelligence-mbsp-phase={mbspSurface?.surface_phase || "n/a"}>MBSP phase {mbspSurface?.surface_phase || "n/a"}</span>
        <span data-intelligence-mbsp-studio={mbspSurface?.surface_tiers?.studio?.active ? "active" : mbspSurface?.surface_tiers?.studio?.unlocked ? "unlocked" : "locked"}>Studio {mbspSurface?.surface_tiers?.studio?.active ? "active" : mbspSurface?.surface_tiers?.studio?.unlocked ? "unlocked" : "locked"}</span>
        <span data-intelligence-mbsp-enterprise={mbspSurface?.surface_tiers?.enterprise?.active ? "active" : mbspSurface?.surface_tiers?.enterprise?.unlocked ? "unlocked" : "locked"}>Enterprise {mbspSurface?.surface_tiers?.enterprise?.active ? "active" : mbspSurface?.surface_tiers?.enterprise?.unlocked ? "unlocked" : "locked"}</span>
      </div>
      <div className="rr-node-chip-row">
        {(driftReflection.subjectChips || []).slice(0, 4).map((chip, index) => (
          <span key={`subject-drift-chip-${index}`}>{chip.subject} {chip.phase} · {chip.severity}</span>
        ))}
      </div>

      <div className="semantic-intelligence-list">
        {history.length > 0 ? history.slice().reverse().map((entry, index) => {
          const item = normalizeSemanticActionLogEntry(entry, index);
          return (
            <article key={`${item.id}-${index}`} className="rr-node-detail-panel" style={{ borderLeftColor: chipColorForEntry(item) }}>
              <div className="semantic-stack-head">
                <strong>{item.action}</strong>
                <span>{item.status}</span>
              </div>
              <div className="rr-node-chip-row">
                <span>{item.subject}</span>
                <span>{item.phase}</span>
                <span>{item.source_surface}</span>
                <span>C{item.compartment_id ?? "?"}</span>
              </div>
              <div className="rr-node-chip-row">
                {item.breadcrumbs.slice(0, 4).map((crumb, crumbIndex) => (
                  <span key={`${item.id}-crumb-${crumbIndex}`}>{crumb}</span>
                ))}
              </div>
              <div className="rr-node-chip-row">
                <span>Timeline {item.timeline_entry?.event_type || "n/a"}</span>
                <span>Provenance depth {item.provenance_update?.depth ?? "n/a"}</span>
                <span>Publishing {item.publishing_signal?.status || "n/a"}</span>
                <span>Workflow {item.workflow_step_result?.status || "n/a"}</span>
              </div>
            </article>
          );
        }) : <p className="status-line">No semantic actions have been logged yet.</p>}
      </div>

      <div className="rr-node-chip-row">
        {(feedback.adaptive_hints || []).slice(0, 3).map((hint, index) => (
          <span key={`hint-${index}`}>{renderHintText(hint)}</span>
        ))}
      </div>
      <div className="rr-node-chip-row">
        <span>Stabilization {driftReflection.stabilization?.status || "monitor"}</span>
        <span>Executed {driftReflection.stabilization?.progress?.executed_corrections || 0}</span>
        <span>Pending {driftReflection.stabilization?.progress?.pending_corrections || 0}</span>
      </div>
      <div className="rr-node-chip-row">
        <span>Optimization {optimizationReflection.status}</span>
        <span>Pressure {optimizationReflection.optimizationPressure}</span>
        <span>Executed {optimizationReflection.progress.executedOptimizations}</span>
        <span>Pending {optimizationReflection.progress.pendingOptimizations}</span>
      </div>
      <div className="semantic-intelligence-list">
        {(driftReflection.stabilization?.recommendations || []).slice(0, 3).map((item, index) => (
          <span key={`stabilize-rec-${index}`}>{item.label || item.action}</span>
        ))}
      </div>
      <div className="semantic-intelligence-list">
        {(optimizationReflection.recommendations || []).slice(0, 3).map((item, index) => (
          <span key={`optimize-rec-${index}`}>{item.label || item.action}</span>
        ))}
      </div>
    </section>
  );
}
