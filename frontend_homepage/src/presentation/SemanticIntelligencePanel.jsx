import { useEffect, useMemo, useState } from "react";

import { fetchRrSemanticIntelligence } from "../api/homepageApi";
import { buildDriftReflection, buildOptimizationReflection, dispatchSemanticNavigation, executeSemanticAction, normalizeSemanticActionLogEntry, normalizeSemanticFeedbackLoop } from "./semanticOsHelpers";
import { normalizeBreadcrumbs } from "./semanticOsHelpers";
import { normalizeTimelineGroups } from "./semanticOsHelpers";

function toRgbString(color) {
  const band = color || { r: [80], g: [80], b: [80] };
  return `rgb(${band.r?.[0] ?? 80}, ${band.g?.[0] ?? 80}, ${band.b?.[0] ?? 80})`;
}

function renderHintText(hint) {
  if (typeof hint === "string") {
    return hint;
  }
  if (hint && typeof hint === "object") {
    return String(hint.message || hint.type || "semantic hint");
  }
  return "semantic hint";
}

export default function SemanticIntelligencePanel({
  panelId = "rr-intelligence-panel",
  semanticIntelligence,
  semanticIntelligenceLoading,
  semanticIntelligenceError,
  semanticActionHistory,
  semanticActionFeedback,
}) {
  const hasExternalPayload =
    semanticIntelligence !== undefined || semanticIntelligenceLoading !== undefined || semanticIntelligenceError !== undefined;
  const [internalPayload, setInternalPayload] = useState(null);
  const [internalError, setInternalError] = useState("");
  const [internalLoading, setInternalLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState("all");
  const [actionStatus, setActionStatus] = useState("");

  useEffect(() => {
    if (hasExternalPayload) {
      return;
    }

    let active = true;
    setInternalLoading(true);
    setInternalError("");

    fetchRrSemanticIntelligence()
      .then((nextPayload) => {
        if (active) {
          setInternalPayload(nextPayload);
        }
      })
      .catch((err) => {
        if (active) {
          setInternalError(err?.message || "Unable to load semantic intelligence");
        }
      })
      .finally(() => {
        if (active) {
          setInternalLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [hasExternalPayload]);

  const payload = hasExternalPayload ? semanticIntelligence : internalPayload;
  const error = hasExternalPayload ? semanticIntelligenceError || "" : internalError;
  const loading = hasExternalPayload ? Boolean(semanticIntelligenceLoading) : internalLoading;

  const analytics = payload?.rr_semantic_analytics || {};
  const recommendations = payload?.recommendation_engine?.recommendations || [];
  const timelineAwareRecommendations = payload?.recommendation_engine?.timeline_aware_recommendations || [];
  const bottlenecks = payload?.workflow_intelligence?.bottlenecks || [];
  const provenanceChains = payload?.workflow_intelligence?.provenance_chains || [];
  const consistencyChecks = payload?.semantic_os_unification?.consistency_checks || [];
  const semanticHealth = payload?.semantic_os_health || {};
  const chapterPreviews = payload?.publishing_intelligence?.chapter_previews || [];
  const chapterAssembly = payload?.publishing_intelligence?.chapter_assembly || [];
  const timeline = payload?.unified_timeline || [];
  const timelineGroups = normalizeTimelineGroups(payload?.timeline_groups || []);
  const subjectMix = Array.isArray(analytics?.subject_mix?.subjects) ? analytics.subject_mix.subjects : [];
  const actionEngine = payload?.semantic_action_engine || {};
  const actionBundles = Array.isArray(actionEngine?.action_bundles) ? actionEngine.action_bundles : [];
  const actionLogEntries = Array.isArray(semanticActionHistory) && semanticActionHistory.length > 0
    ? semanticActionHistory
    : payload?.semantic_action_log?.entries || [];
  const actionFeedback = normalizeSemanticFeedbackLoop(
    semanticActionFeedback && typeof semanticActionFeedback === "object"
      ? semanticActionFeedback
      : payload?.semantic_feedback_loop || {},
    {
      actionLog: actionLogEntries,
      semanticHealth,
    },
  );
  const driftReflection = buildDriftReflection(actionFeedback);
  const optimizationReflection = buildOptimizationReflection(actionFeedback);

  const filteredRecommendations = useMemo(() => {
    return recommendations.filter((item) => {
      if (activeFilter === "all") {
        return true;
      }
      if (activeFilter === "rr") {
        return String(item.type || "").includes("rr");
      }
      if (activeFilter === "workflow") {
        return String(item.type || "").includes("workflow");
      }
      if (activeFilter === "publishing") {
        return String(item.type || "").includes("publishing");
      }
      return true;
    });
  }, [activeFilter, recommendations]);

  const dispatchNavigation = (navigation = {}) => {
    dispatchSemanticNavigation(navigation, "semantic-intelligence");
  };

  const runBundleAction = async (bundle) => {
    const actions = Array.isArray(bundle?.actions) ? bundle.actions : [];
    const firstAction = actions[0];
    if (!firstAction) {
      return;
    }
    try {
      const result = await executeSemanticAction({
        action: firstAction,
        request: bundle?.default_request || {},
        source: "semantic_os",
        semanticHealth,
      });
      setActionStatus(result?.status === "executed" ? `Executed ${bundle.title}` : result?.detail || "Semantic action was not executed");
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute semantic action");
    }
  };

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">Semantic Intelligence</p>
          <h2>Recommendations, Bottlenecks, and Timeline</h2>
        </div>
        <label className="semantic-select-field">
          View Filter
          <select value={activeFilter} onChange={(event) => setActiveFilter(event.target.value)}>
            <option value="all">All</option>
            <option value="rr">RR</option>
            <option value="workflow">Workflow</option>
            <option value="publishing">Publishing</option>
          </select>
        </label>
      </div>

      {loading ? <p className="status-line">Loading semantic intelligence...</p> : null}
      {error ? <p className="status-line">{error}</p> : null}

      {payload ? (
        <>
          <div className="semantic-intelligence-grid">
            <article>
              <h3>RR Analytics</h3>
              <div className="rr-status-band-grid">
                <div>Lanes <strong>{analytics.lane_count ?? 0}</strong></div>
                <div>Active <strong>{analytics.active_lane_count ?? 0}</strong></div>
                <div>Ideas <strong>{analytics.status_bands?.Idea ?? 0}</strong></div>
                <div>Project <strong>{analytics.status_bands?.Project ?? 0}</strong></div>
              </div>
              <div className="rr-node-chip-row">
                {Object.entries(analytics.integrity_strip || {}).map(([key, value]) => (
                  <span key={key}>{key}: {value}</span>
                ))}
              </div>
              <div className="rr-node-chip-row">
                {(payload?.semantic_os_unification?.timeline_breadcrumbs || []).slice(0, 3).map((crumbs, index) => (
                  <span key={`breadcrumb-${index}`}>{normalizeBreadcrumbs(crumbs).join(" → ") || "timeline"}</span>
                ))}
              </div>
              <div className="rr-node-chip-row">
                {(semanticHealth.checks || []).slice(0, 3).map((item) => (
                  <span key={`health-${item.surface}`}>{item.surface}: {item.status}</span>
                ))}
              </div>
            </article>

            <article>
              <h3>Subject Mix</h3>
              <div className="semantic-intelligence-list">
                {subjectMix.map((item) => (
                  <button key={`${item.compartment_id}-${item.subject}`} type="button" onClick={() => dispatchNavigation({ surface: "rr_dashboard", compartment_id: item.compartment_id })}>
                    {item.subject} · {item.node_count} · {Math.round((item.node_share || 0) * 100)}%
                  </button>
                ))}
              </div>
            </article>

            <article>
              <h3>Workflow Bottlenecks</h3>
              <div className="semantic-intelligence-list">
                {bottlenecks.length > 0 ? bottlenecks.map((item) => (
                  <button key={`${item.compartment_id}-${item.subject}`} type="button" onClick={() => dispatchNavigation(item.navigation)}>
                    {item.subject} · pressure {item.pressure_score}
                  </button>
                )) : <p className="status-line">No bottlenecks detected.</p>}
              </div>
            </article>

            <article>
              <h3>Publishing Previews</h3>
              <div className="semantic-intelligence-list">
                {chapterPreviews.length > 0 ? chapterPreviews.map((item) => (
                  <button key={item.chapter_id} type="button" style={{ borderLeftColor: toRgbString(item.color) }} onClick={() => dispatchNavigation({ surface: "publishing_layer" })}>
                    {item.title}
                  </button>
                )) : <p className="status-line">No chapter previews available.</p>}
              </div>
            </article>

            <article>
              <h3>Provenance Chains</h3>
              <div className="semantic-intelligence-list">
                {provenanceChains.length > 0 ? provenanceChains.map((item) => (
                  <button key={`${item.compartment_id}-${item.subject}`} type="button" onClick={() => dispatchNavigation({ surface: "rr_detail", business_id: item.business_id, compartment_id: item.compartment_id })}>
                    {item.subject} · {Array.isArray(item.breadcrumbs) ? item.breadcrumbs.slice(-2).join(" → ") : "chain"}
                  </button>
                )) : <p className="status-line">No provenance chains available.</p>}
              </div>
            </article>

            <article>
              <h3>Optimization Loop</h3>
              <div className="rr-node-chip-row">
                <span>Status {optimizationReflection.status}</span>
                <span>Pressure {optimizationReflection.optimizationPressure}</span>
                <span>Trend {optimizationReflection.trend}</span>
              </div>
              <div className="rr-node-chip-row">
                <span>Subject mix {optimizationReflection.subjectMixScore}</span>
                <span>Workflow {optimizationReflection.workflowEfficiencyScore}</span>
                <span>Publishing {optimizationReflection.publishingReadinessScore}</span>
              </div>
              <div className="semantic-intelligence-list">
                {(optimizationReflection.recommendations || []).slice(0, 3).map((item, index) => (
                  <span key={`opt-rec-${item.action || index}`}>{item.label || item.action}</span>
                ))}
              </div>
            </article>
          </div>

          <section className="semantic-intelligence-panel">
            <h3>Recommendation Engine</h3>
            <div className="semantic-intelligence-list">
              {filteredRecommendations.map((item) => (
                <button key={`${item.type}-${item.compartment_id || item.phase || item.message}`} type="button" onClick={() => dispatchNavigation(item.navigation)}>
                  {item.message}
                </button>
              ))}
              {filteredRecommendations.length === 0 ? <p className="status-line">No recommendations for this filter.</p> : null}
            </div>
          </section>

          <section className="semantic-intelligence-panel">
            <h3>Adaptive Intelligence</h3>
            <div className="semantic-intelligence-list">
              {timelineAwareRecommendations.length > 0 ? timelineAwareRecommendations.map((item) => (
                <button key={`${item.type}-${item.message}`} type="button" onClick={() => dispatchNavigation(item.navigation)}>
                  {item.message}
                </button>
              )) : <p className="status-line">No adaptive suggestions yet.</p>}
              {consistencyChecks.length > 0 ? consistencyChecks.map((item) => (
                <span key={`${item.surface}-${item.status}`}>{item.surface}: {item.status}</span>
              )) : null}
            </div>
          </section>

          <section className="semantic-intelligence-panel">
            <h3>Semantic Action Bundles</h3>
            <div className="semantic-intelligence-list">
              {actionBundles.length > 0 ? actionBundles.map((bundle) => (
                <button key={bundle.bundle_id} type="button" onClick={() => runBundleAction(bundle)}>
                  {bundle.title}
                </button>
              )) : <p className="status-line">No action bundles available.</p>}
            </div>
            {actionStatus ? <p className="status-line">{actionStatus}</p> : null}
            <div className="rr-node-chip-row">
              <span>History {actionLogEntries.length}</span>
              <span>Drift {actionFeedback?.drift_detected ? "detected" : "clear"}</span>
              <span>Severity {driftReflection.severity}</span>
              <span>Score {driftReflection.score}</span>
              <span>Blocked {actionFeedback?.recent_blocked || 0}</span>
              <span>Failures {actionFeedback?.recent_failures || 0}</span>
            </div>
            <div className="rr-node-chip-row">
              {(actionFeedback?.adaptive_hints || []).slice(0, 2).map((hint, index) => (
                <span key={`adaptive-hint-${index}`}>{renderHintText(hint)}</span>
              ))}
            </div>
            <div className="rr-node-chip-row">
              {(driftReflection.subjectChips || []).slice(0, 3).map((chip, index) => (
                <span key={`drift-chip-${index}`}>{chip.subject} {chip.phase} · {chip.severity}</span>
              ))}
            </div>
            <div className="rr-node-chip-row">
              <span>Stabilization {driftReflection.stabilization?.status || "monitor"}</span>
              <span>Executed corrections {driftReflection.stabilization?.progress?.executed_corrections || 0}</span>
              <span>Pending corrections {driftReflection.stabilization?.progress?.pending_corrections || 0}</span>
            </div>
            <div className="semantic-intelligence-list">
              {(driftReflection.stabilization?.recommendations || []).slice(0, 4).map((item, index) => (
                <button key={`stabilization-${item.action || index}`} type="button" onClick={() => runBundleAction({ actions: [item.action], default_request: { compartment_id: subjectMix[0]?.compartment_id, surface: "semantic_os" }, title: item.label || item.action })}>
                  {item.label || item.action}
                </button>
              ))}
            </div>
            <div className="semantic-intelligence-list">
              {actionLogEntries.slice(-3).reverse().map((entry, index) => {
                const item = normalizeSemanticActionLogEntry(entry, index);
                return (
                  <span key={`${item.id}-${index}`}>
                    {item.action} · {item.status} · {item.subject} · {item.phase}
                  </span>
                );
              })}
            </div>
          </section>

          <section className="semantic-intelligence-panel">
            <h3>Unified Timeline</h3>
            <div className="semantic-intelligence-timeline">
              {(timelineGroups.length > 0 ? timelineGroups : timeline.map((item) => ({
                subject: item.subject || "Unknown",
                phase: item.phase || "Unknown",
                count: 1,
                items: [item],
                navigation_targets: [item.surface],
              }))).map((group) => (
                <article key={`${group.subject}-${group.phase}`}>
                  <div className="semantic-stack-head">
                    <div>
                      <p className="eyebrow">{group.subject}</p>
                      <h4>{group.phase}</h4>
                    </div>
                    <div className="rr-node-chip-row">
                      <span>{group.count} events</span>
                      {group.navigation_targets.slice(0, 3).map((surface) => <span key={`${group.subject}-${surface}`}>{surface}</span>)}
                    </div>
                  </div>
                  <div className="semantic-intelligence-list">
                    {group.items.map((item, index) => {
                      const chips = normalizeBreadcrumbs(item.breadcrumbs);
                      const timelineNavigation = item.navigation || { surface: item.surface, compartment_id: item.compartment_id };
                      return (
                        <button
                          key={`${item.event_type}-${item.compartment_id}-${index}`}
                          type="button"
                          style={{ borderLeftColor: toRgbString(item.color) }}
                          onClick={() => dispatchNavigation(timelineNavigation)}
                        >
                          <strong>{item.label}</strong>
                          <div className="rr-node-chip-row">
                            <span>{item.surface}</span>
                            <span>{item.event_type}</span>
                            <span>C{item.compartment_id ?? "?"}</span>
                          </div>
                          <div className="rr-node-chip-row">
                            {chips.slice(0, 3).map((crumb) => <span key={`${item.event_type}-${crumb}`}>{crumb}</span>)}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </section>
  );
}