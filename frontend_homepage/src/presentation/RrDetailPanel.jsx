import { useEffect, useMemo, useState } from "react";

import { fetchPreferences, fetchRrNodeDetail, saveViewState } from "../api/homepageApi";
import { buildDriftReflection, buildOptimizationReflection, dispatchSemanticNavigation, executeSemanticAction, normalizeBreadcrumbs, normalizeSemanticFeedbackLoop, SEMANTIC_ACTIONS } from "./semanticOsHelpers";

const LOCAL_STORAGE_KEY = "grassroots.semantic-stack.view-state.v1";

function readPersistedState() {
  try {
    const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (_error) {
    return {};
  }
}

function writePersistedState(state) {
  try {
    window.localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(state));
  } catch (_error) {
    // Ignore storage quota or privacy restrictions.
  }
}

export default function RrDetailPanel({ panelId = "rr-detail-panel", semanticIntelligence, semanticActionFeedback }) {
  const [selectedBusinessId, setSelectedBusinessId] = useState(null);
  const [activeSurface, setActiveSurface] = useState("rr_dashboard");
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isHydrated, setIsHydrated] = useState(false);
  const [actionStatus, setActionStatus] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    let active = true;
    const persisted = readPersistedState();
    const semanticState = persisted?.semantic_stack || {};

    if (semanticState.active_surface) {
      setActiveSurface(semanticState.active_surface);
    }
    if (Number.isFinite(Number(semanticState.selected_business_id))) {
      setSelectedBusinessId(Number(semanticState.selected_business_id));
    }

    fetchPreferences()
      .then((listPayload) => {
        if (!active) {
          return;
        }
        const preference = Array.isArray(listPayload?.results) ? listPayload.results[0] : null;
        const serverState = preference?.view_state?.semantic_stack || {};
        if (serverState.active_surface) {
          setActiveSurface(serverState.active_surface);
        }
        if (Number.isFinite(Number(serverState.selected_business_id))) {
          setSelectedBusinessId(Number(serverState.selected_business_id));
        }
      })
      .catch(() => {
        if (!active) {
          return;
        }
      })
      .finally(() => {
        if (active) {
          setIsHydrated(true);
        }
      });

    const handleFocusNode = (event) => {
      const businessId = Number(event?.detail?.businessId);
      if (!Number.isFinite(businessId) || businessId <= 0) {
        return;
      }
      setSelectedBusinessId(businessId);
      if (event?.detail?.source) {
        setActiveSurface(String(event.detail.source));
      }
    };

    const handlePanelSelect = (event) => {
      const panelId = String(event?.detail?.panelId || "");
      if (panelId) {
        setActiveSurface(panelId);
      }
    };

    window.addEventListener("grassroots:rr-focus-node", handleFocusNode);
    window.addEventListener("grassroots:semantic-panel-select", handlePanelSelect);

    return () => {
      active = false;
      window.removeEventListener("grassroots:rr-focus-node", handleFocusNode);
      window.removeEventListener("grassroots:semantic-panel-select", handlePanelSelect);
    };
  }, []);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    const nextState = {
      semantic_stack: {
        active_surface: activeSurface,
        selected_business_id: selectedBusinessId,
      },
    };
    writePersistedState(nextState);
    saveViewState(nextState).catch(() => {
      // Local storage remains the fallback if the server write fails.
    });
  }, [activeSurface, isHydrated, selectedBusinessId]);

  useEffect(() => {
    if (!Number.isFinite(Number(selectedBusinessId)) || Number(selectedBusinessId) <= 0) {
      setPayload(null);
      return;
    }

    let active = true;
    setLoading(true);
    setError("");

    fetchRrNodeDetail(selectedBusinessId)
      .then((nextPayload) => {
        if (active) {
          setPayload(nextPayload);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err?.message || "Unable to load RR detail");
          setPayload(null);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedBusinessId]);

  const node = payload?.node || null;
  const identity = payload?.identity || {};
  const ontology = payload?.ontology || {};
  const history = Array.isArray(payload?.integrity_history) ? payload.integrity_history : [];
  const semanticHealth = semanticIntelligence?.semantic_os_health || {};
  const selectedChain = payload?.multi_hop_provenance || null;
  const sharedProvenanceChain =
    (Array.isArray(payload?.provenance_chain) && payload.provenance_chain.length > 0
      ? payload.provenance_chain
      : Array.isArray(semanticIntelligence?.workflow_intelligence?.provenance_chains)
        ? semanticIntelligence.workflow_intelligence.provenance_chains.find((item) => Number(item.compartment_id) === Number(node?.card_color_spec?.compartment_tag?.compartment_id))?.chain || []
        : []) || [];
  const semanticBreadcrumbs = payload?.semantic_breadcrumbs || (Array.isArray(semanticIntelligence?.workflow_intelligence?.provenance_chains)
    ? semanticIntelligence.workflow_intelligence.provenance_chains.find((item) => Number(item.compartment_id) === Number(node?.card_color_spec?.compartment_tag?.compartment_id))?.breadcrumbs || []
    : []);
  const semanticActions = Array.isArray(payload?.semantic_actions) ? payload.semantic_actions : [];
  const driftReflection = buildDriftReflection(
    normalizeSemanticFeedbackLoop(
      semanticActionFeedback || semanticIntelligence?.semantic_feedback_loop || {},
    ),
  );
  const optimizationReflection = buildOptimizationReflection(
    normalizeSemanticFeedbackLoop(
      semanticActionFeedback || semanticIntelligence?.semantic_feedback_loop || {},
    ),
  );
  const publishingReady = Array.isArray(payload?.publishing_ready_signals)
    ? payload.publishing_ready_signals.find((item) => item.signal === "publishing_ready")?.status === "ready"
    : false;

  const dispatchPanelSelect = (panelId) => {
    window.dispatchEvent(new CustomEvent("grassroots:semantic-panel-select", { detail: { panelId } }));
  };

  const dispatchLaneFocus = () => {
    const compartmentId = Number(node?.card_color_spec?.compartment_tag?.compartment_id);
    if (Number.isFinite(compartmentId)) {
      window.dispatchEvent(new CustomEvent("grassroots:rr-focus-lane", { detail: { compartmentId, source: "rr-detail" } }));
      window.dispatchEvent(new CustomEvent("grassroots:rr-focus-map-cell", { detail: { compartmentId, source: "rr-detail" } }));
    }
  };

  const breadcrumbs = useMemo(() => {
    const pieces = [ontology.sector, ontology.subject, ontology.industry, ontology.subindustry].filter(Boolean);
    return pieces;
  }, [ontology.industry, ontology.sector, ontology.subindustry, ontology.subject]);

  const runAction = async (action, request = {}) => {
    setActionLoading(true);
    setActionStatus("");
    try {
      const result = await executeSemanticAction({
        action,
        request,
        source: "rr_detail",
        semanticHealth,
      });
      if (result?.status === "executed") {
        setActionStatus(`Executed ${action}`);
      } else {
        setActionStatus(result?.detail || "Semantic action was not executed");
      }
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute semantic action");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <section id={panelId} className="panel semantic-stack-panel rr-detail-surface">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">RR Detail Surface</p>
          <h2>Unified node intelligence</h2>
        </div>
        <div className="rr-breadcrumb-row">
          <button type="button" onClick={() => dispatchPanelSelect("rr_dashboard")}>Dashboard</button>
          <button type="button" onClick={() => dispatchPanelSelect("rr_industry_map")}>Map</button>
          <button type="button" onClick={() => dispatchPanelSelect("rr_workflows")}>Workflow</button>
          <button type="button" onClick={() => dispatchPanelSelect("rr_publishing")}>Publishing</button>
        </div>
      </div>

      {loading ? <p className="status-line">Loading RR detail...</p> : null}
      {error ? <p className="status-line">{error}</p> : null}

      {node ? (
        <>
          <div className="rr-node-detail-panel">
            <div className="semantic-stack-head">
              <div>
                <p className="eyebrow">{node.subject}</p>
                <h3>{node.title}</h3>
              </div>
              <div className="rr-node-actions">
                <button type="button" onClick={dispatchLaneFocus}>Jump to lane</button>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => runAction(SEMANTIC_ACTIONS.ADVANCE_WORKFLOW_STEP, {
                    business_id: node.business_id,
                    compartment_id: node.card_color_spec?.compartment_tag?.compartment_id,
                    workflow_step: "deterministic_next",
                  })}
                >
                  Advance workflow step
                </button>
                <button
                  type="button"
                  disabled={actionLoading || !publishingReady}
                  onClick={() => runAction(SEMANTIC_ACTIONS.PREPARE_PUBLISHING_CHAPTER, {
                    business_id: node.business_id,
                    compartment_id: node.card_color_spec?.compartment_tag?.compartment_id,
                  })}
                >
                  Prepare chapter
                </button>
              </div>
            </div>
            {actionStatus ? <p className="status-line">{actionStatus}</p> : null}

            <div className="rr-node-chip-row">
              {(semanticHealth.checks || []).map((item) => (
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
              <span>Subject mix {optimizationReflection.subjectMixScore}</span>
              <span>Workflow {optimizationReflection.workflowEfficiencyScore}</span>
              <span>Publishing {optimizationReflection.publishingReadinessScore}</span>
            </div>
            <div className="rr-node-chip-row">
              {(driftReflection.subjectChips || []).slice(0, 3).map((chip, index) => (
                <span key={`rr-drift-chip-${index}`}>{chip.subject} {chip.phase} · {chip.severity}</span>
              ))}
            </div>

            <div className="rr-node-chip-row">
              {breadcrumbs.map((crumb, index) => (
                <button
                  key={crumb}
                  type="button"
                  className="rr-breadcrumb-chip"
                  onClick={() => {
                    if (index === 0) {
                      dispatchPanelSelect("rr_dashboard");
                    } else if (index === 1) {
                      dispatchPanelSelect("rr_industry_map");
                    } else if (index >= 2) {
                      dispatchPanelSelect("rr_workflows");
                    }
                  }}
                >
                  {crumb}
                </button>
              ))}
            </div>

            <div className="rr-node-chip-row">
              {normalizeBreadcrumbs(semanticBreadcrumbs).map((crumb, index) => (
                <span key={`${crumb}-${index}`}>{crumb}</span>
              ))}
            </div>

            <div className="rr-node-chip-row">
              <span>Color code {identity.color_code ?? "n/a"}</span>
              <span>C{identity.compartment_id ?? "?"}</span>
              <span>rgb({identity.display_rgb?.r ?? 0}, {identity.display_rgb?.g ?? 0}, {identity.display_rgb?.b ?? 0})</span>
              <span>Integrity {identity.integrity_state || "unavailable"}</span>
            </div>

            <p className="rr-node-path">{breadcrumbs.join(" -> ") || "No ontology path recorded"}</p>

            <div className="rr-history-list">
              {history.map((event) => (
                <article key={`${event.event}-${event.timestamp}`}>
                  <strong>{event.event}</strong>
                  <p>{event.detail}</p>
                  <span>{event.timestamp}</span>
                </article>
              ))}
            </div>
          </div>

          <section className="rr-node-detail-panel">
            <h3>Provenance + Workflow Links</h3>
            {selectedChain ? <p className="status-line">Provenance depth: {selectedChain.depth}</p> : null}
            <div className="rr-node-chip-row">
              {sharedProvenanceChain.map((item) => (
                <button
                  key={`${item.surface}-${item.label}`}
                  type="button"
                  onClick={() => {
                    runAction(SEMANTIC_ACTIONS.OPEN_RR_PROVENANCE_CHAIN, {
                      business_id: node?.business_id,
                      compartment_id: node?.card_color_spec?.compartment_tag?.compartment_id,
                    });
                    dispatchSemanticNavigation(item.navigation || { surface: item.surface, compartment_id: node?.card_color_spec?.compartment_tag?.compartment_id, business_id: node?.business_id }, "rr-detail");
                  }}
                >
                  {item.label}
                </button>
              ))}
              {semanticActions.map((item) => (
                <button
                  key={`${item.action}-${item.label}`}
                  type="button"
                  disabled={actionLoading || (item.action === SEMANTIC_ACTIONS.PREPARE_PUBLISHING_CHAPTER && !publishingReady)}
                  onClick={() => runAction(item.action, item.request || {})}
                >
                  {item.label}
                </button>
              ))}
              {(node?.provenance?.workflow_refs || []).map((item) => (
                <button
                  key={item.workflow_id || item.phase || "workflow"}
                  type="button"
                  onClick={() => dispatchPanelSelect("rr_workflows")}
                >
                  Workflow {item.workflow_id || item.phase || "ref"}
                </button>
              ))}
              {(node?.provenance?.sop_refs || []).map((item) => (
                <button
                  key={item.sop_id || item.title || "sop"}
                  type="button"
                  onClick={() => dispatchPanelSelect("rr_workflows")}
                >
                  SOP {item.sop_id || item.title || "ref"}
                </button>
              ))}
            </div>
          </section>
        </>
      ) : (
        <p className="status-line">Select a node from the RR dashboard, map, VA, or workflow surfaces.</p>
      )}
    </section>
  );
}