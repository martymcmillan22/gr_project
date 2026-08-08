import { useEffect, useMemo, useState } from "react";

import { fetchRrVaGuidance } from "../api/homepageApi";
import { buildDriftReflection, buildOptimizationReflection, dispatchSemanticNavigation, executeSemanticAction, normalizeBreadcrumbs, normalizeSemanticFeedbackLoop, SEMANTIC_ACTIONS } from "./semanticOsHelpers";

export default function VaSemanticGuidancePanel({ panelId = "va-guidance-panel", semanticIntelligence, semanticActionFeedback }) {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    fetchRrVaGuidance()
      .then((nextPayload) => {
        if (!active) {
          return;
        }
        setPayload(nextPayload);
      })
      .catch((err) => {
        if (!active) {
          return;
        }
        setError(err?.message || "Unable to load VA semantic guidance");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const dominant = payload?.signals?.dominant_compartments || [];
  const hotspots = payload?.signals?.integrity_mismatch_hotspots || [];
  const semanticRecommendations = semanticIntelligence?.va_action_engine?.timeline_actions || [];
  const semanticCoaching = semanticIntelligence?.va_action_engine?.semantic_coaching || [];
  const semanticHealth = semanticIntelligence?.semantic_os_health || {};
  const recommendations = semanticRecommendations.length > 0 ? semanticRecommendations : payload?.recommendations || [];
  const driftReflection = buildDriftReflection(
    normalizeSemanticFeedbackLoop(semanticActionFeedback || semanticIntelligence?.semantic_feedback_loop || {}),
  );
  const optimizationReflection = buildOptimizationReflection(
    normalizeSemanticFeedbackLoop(semanticActionFeedback || semanticIntelligence?.semantic_feedback_loop || {}),
  );
  const [quickFilter, setQuickFilter] = useState("all");
  const [actionStatus, setActionStatus] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const filteredRecommendations = useMemo(() => recommendations.filter((item) => {
    if (quickFilter === "all") {
      return true;
    }
    if (quickFilter === "balance") {
      return String(item.type || "").includes("balance") || String(item.type || "").includes("imbalance");
    }
    if (quickFilter === "workflow") {
      return String(item.type || "").includes("workflow") || String(item.type || "").includes("sop");
    }
    return true;
  }), [quickFilter, recommendations]);

  const applyRecommendation = async (item) => {
    setActionLoading(true);
    setActionStatus("");
    try {
      const result = await executeSemanticAction({
        action: SEMANTIC_ACTIONS.ADVANCE_WORKFLOW_STEP,
        request: {
          business_id: item?.navigation?.business_id,
          compartment_id: item?.compartment_id || item?.navigation?.compartment_id,
          workflow_step: "deterministic_next",
        },
        source: "va_guidance",
        semanticHealth,
      });
      if (result?.status === "executed") {
        setActionStatus("Executed advance workflow step");
      } else {
        setActionStatus(result?.detail || "Semantic action was not executed");
      }
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute semantic action");
    } finally {
      setActionLoading(false);
      dispatchSemanticNavigation(item?.navigation || {}, "va-guidance");
    }
  };

  const executeRecommendationAction = async (recommendation = {}) => {
    const action = recommendation?.action || SEMANTIC_ACTIONS.ADVANCE_WORKFLOW_STEP;
    const request = {
      business_id: recommendation?.navigation?.business_id,
      compartment_id: recommendation?.compartment_id || recommendation?.navigation?.compartment_id,
      workflow_step: action === SEMANTIC_ACTIONS.ADVANCE_WORKFLOW_STEP ? "deterministic_next" : "optimize",
    };
    setActionLoading(true);
    setActionStatus("");
    try {
      const result = await executeSemanticAction({
        action,
        request,
        source: "va_guidance",
        semanticHealth,
      });
      if (result?.status === "executed") {
        setActionStatus(`Executed ${recommendation.label || action}`);
      } else {
        setActionStatus(result?.detail || "Semantic action was not executed");
      }
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute semantic action");
    } finally {
      setActionLoading(false);
      dispatchSemanticNavigation(recommendation?.navigation || {}, "va-guidance");
    }
  };

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">VA Guidance Mode</p>
          <h2>Semantic Color-Aware Guidance</h2>
        </div>
        <label className="semantic-select-field">
          Quick Filter
          <select value={quickFilter} onChange={(event) => setQuickFilter(event.target.value)}>
            <option value="all">All</option>
            <option value="balance">Balance</option>
            <option value="workflow">Workflow / SOP</option>
          </select>
        </label>
      </div>

      {loading ? <p className="status-line">Loading VA guidance...</p> : null}
      {error ? <p className="status-line">{error}</p> : null}

      {payload ? (
        <div className="va-guidance-layout">
          <article>
            <h3>Dominant Compartments</h3>
            <ul>
              {dominant.length > 0 ? dominant.map((item) => (
                <li key={`${item.compartment_id}-${item.subject}`}>
                  C{item.compartment_id} {item.subject} ({item.node_count})
                </li>
              )) : <li>No dominant lanes detected yet.</li>}
            </ul>
          </article>
          <article>
            <h3>Imbalance + Integrity Hotspots</h3>
            <ul>
              {hotspots.length > 0 ? hotspots.map((item) => (
                <li key={`${item.compartment_id}-${item.subject}`}>
                  {item.subject}: mismatch {item.mismatch_count}
                </li>
              )) : <li>No integrity hotspots detected.</li>}
            </ul>
          </article>
          <article>
            <h3>SOP + Workflow Recommendations</h3>
            <ul>
              {filteredRecommendations.length > 0 ? filteredRecommendations.map((item, index) => (
                <li key={`${item.type}-${index}`}>
                  <p>{item.message}</p>
                  <button type="button" disabled={actionLoading} onClick={() => applyRecommendation(item)}>Apply navigation</button>
                </li>
              )) : <li>No recommendations generated yet.</li>}
            </ul>
            {actionStatus ? <p className="status-line">{actionStatus}</p> : null}
            <div className="rr-node-chip-row">
              {(semanticHealth.checks || []).filter((item) => item.surface === "va" || item.surface === "semantic_os").map((item) => (
                <span key={`${item.surface}-${item.status}`}>{item.surface}: {item.status}</span>
              ))}
            </div>
            <div className="rr-node-chip-row">
              <span>Drift {driftReflection.severity}</span>
              <span>Score {driftReflection.score}</span>
              <span>Stabilization {driftReflection.stabilization?.status || "monitor"}</span>
            </div>
            <div className="rr-node-chip-row">
              <span>Optimization {optimizationReflection.status}</span>
              <span>Pressure {optimizationReflection.optimizationPressure}</span>
              <span>Workflow {optimizationReflection.workflowEfficiencyScore}</span>
              <span>Publishing {optimizationReflection.publishingReadinessScore}</span>
            </div>
            <div className="rr-node-chip-row">
              {(driftReflection.subjectChips || []).slice(0, 3).map((chip, index) => (
                <span key={`va-drift-chip-${index}`}>{chip.subject} {chip.phase} · {chip.severity}</span>
              ))}
            </div>
            <div className="rr-node-chip-row">
              <span>Balance suggestions</span>
              <span>Lane focus</span>
              <span>Workflow routing</span>
            </div>
            <div className="rr-node-chip-row">
              {semanticCoaching.slice(0, 3).map((item, index) => (
                <span key={`${item.subject}-${index}`}>{normalizeBreadcrumbs(item.breadcrumbs).join(" → ") || item.subject}</span>
              ))}
            </div>
            <div className="semantic-intelligence-list">
              {(driftReflection.stabilization?.recommendations || []).slice(0, 3).map((item, index) => (
                <button key={`va-stab-${item.action || index}`} type="button" disabled={actionLoading} onClick={() => executeRecommendationAction({ ...item, navigation: { surface: "rr_dashboard" } })}>
                  {item.label || item.action}
                </button>
              ))}
            </div>
            <div className="semantic-intelligence-list">
              {(optimizationReflection.recommendations || []).slice(0, 3).map((item, index) => (
                <button key={`va-opt-${item.action || index}`} type="button" disabled={actionLoading} onClick={() => executeRecommendationAction({ ...item, navigation: { surface: item.surface || "workflow_swimlanes" } })}>
                  {item.label || item.action}
                </button>
              ))}
            </div>
          </article>
        </div>
      ) : null}
    </section>
  );
}
