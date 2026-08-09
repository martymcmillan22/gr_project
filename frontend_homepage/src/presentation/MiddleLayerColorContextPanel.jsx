import { useEffect, useState } from "react";

import { fetchProjectMiddleLayerActivation } from "../api/homepageApi";
import { buildUnifiedPlatformIntelligenceState, dispatchSemanticNavigation, normalizeBreadcrumbs } from "./semanticOsHelpers";

export default function MiddleLayerColorContextPanel({ panelId = "middle-layer-panel", semanticIntelligence, timelineSignalState, unifiedIntelligenceState }) {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeBusinessId, setActiveBusinessId] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    fetchProjectMiddleLayerActivation()
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
        setError(err?.message || "Unable to load Middle Layer color context");
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

  const rrContext = payload?.rr_color_context || {};
  const dominant = Array.isArray(rrContext?.dominant_lanes) ? rrContext.dominant_lanes : [];
  const imbalanceLanes = dominant.filter((lane) => Number(lane?.integrity?.mismatch || 0) > Number(lane?.integrity?.ok || 0));
  const semanticChecks = semanticIntelligence?.semantic_os_unification?.consistency_checks || [];
  const semanticBreadcrumbs = semanticIntelligence?.semantic_os_unification?.timeline_breadcrumbs || [];
  const semanticHealth = semanticIntelligence?.semantic_os_health || {};
  const latestTimelineEvent = timelineSignalState?.latest_event || null;
  const timelinePhaseGates = Array.isArray(timelineSignalState?.phase_gates) ? timelineSignalState.phase_gates : [];
  const completedTimelineSlots = Array.isArray(timelineSignalState?.completed_slots) ? timelineSignalState.completed_slots : [];
  const resolvedIntelligenceState = (unifiedIntelligenceState && typeof unifiedIntelligenceState === "object")
    ? unifiedIntelligenceState
    : buildUnifiedPlatformIntelligenceState(timelineSignalState || {});
  const mbspSurface = resolvedIntelligenceState?.synthesis?.mbsp_surface || { surface_phase: "n/a", surface_tiers: {} };

  const openLane = (lane) => {
    dispatchSemanticNavigation({ surface: "rr_dashboard", compartment_id: lane.compartment_id }, "middle-layer");
  };

  const openMismatchNode = (lane) => {
    const first = Array.isArray(lane.cards) ? lane.cards.find((card) => card.integrity_state === "mismatch") : null;
    if (!first?.business_id) {
      return;
    }
    window.dispatchEvent(
      new CustomEvent("grassroots:rr-focus-node", {
        detail: { businessId: first.business_id, source: "middle-layer" },
      }),
    );
  };

  useEffect(() => {
    const handleOpenMiddleLayer = (event) => {
      const businessId = Number(event?.detail?.businessId);
      if (Number.isFinite(businessId) && businessId > 0) {
        setActiveBusinessId(businessId);
      }
    };

    window.addEventListener("grassroots:rr-open-middle-layer", handleOpenMiddleLayer);
    return () => {
      window.removeEventListener("grassroots:rr-open-middle-layer", handleOpenMiddleLayer);
    };
  }, []);

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">Middle Layer Dashboard</p>
          <h2>RR Color Context</h2>
        </div>
      </div>

      {loading ? <p className="status-line">Loading Middle Layer context...</p> : null}
      {error ? <p className="status-line">{error}</p> : null}

      {payload ? (
        <>
          {activeBusinessId ? <p className="status-line">Focused from RR node #{activeBusinessId}.</p> : null}
          <div className="rr-status-band-grid">
            <div>Lanes <strong>{rrContext.lane_count ?? 0}</strong></div>
            <div>Integrity OK <strong>{rrContext.integrity_strip?.ok ?? 0}</strong></div>
            <div>Mismatch <strong>{rrContext.integrity_strip?.mismatch ?? 0}</strong></div>
            <div>Unavailable <strong>{rrContext.integrity_strip?.unavailable ?? 0}</strong></div>
          </div>
          <div className="rr-node-chip-row">
            {(semanticHealth.checks || []).filter((item) => item.surface === "middle_layer" || item.surface === "semantic_os").map((item) => (
              <span key={`${item.surface}-${item.status}`}>{item.surface}: {item.status}</span>
            ))}
          </div>
          <div className="rr-node-chip-row">
            <span>Timeline slots {completedTimelineSlots.length}/16 complete</span>
            <span>Latest slot {latestTimelineEvent?.slot_index || "n/a"}</span>
            <span>Phase {latestTimelineEvent?.phase || "n/a"}</span>
            <span>Gate {latestTimelineEvent?.gate_locked ? "locked" : "unlocked"}</span>
          </div>
          <div className="rr-node-chip-row">
            <span>Drift {latestTimelineEvent?.semantic_state?.drift_score ?? "n/a"}</span>
            <span>Stability {latestTimelineEvent?.semantic_state?.stability_score ?? "n/a"}</span>
            <span>Alignment {latestTimelineEvent?.semantic_state?.alignment_score ?? "n/a"}</span>
            <span>{latestTimelineEvent?.industry_metadata?.group_name || "n/a"}</span>
            <span>{latestTimelineEvent?.industry_metadata?.industry || "n/a"}</span>
          </div>
          <div className="rr-node-chip-row">
            <span data-intelligence-mbsp-phase={mbspSurface?.surface_phase || "n/a"}>MBSP phase {mbspSurface?.surface_phase || "n/a"}</span>
            <span data-intelligence-mbsp-studio={mbspSurface?.surface_tiers?.studio?.active ? "active" : mbspSurface?.surface_tiers?.studio?.unlocked ? "unlocked" : "locked"}>Studio {mbspSurface?.surface_tiers?.studio?.active ? "active" : mbspSurface?.surface_tiers?.studio?.unlocked ? "unlocked" : "locked"}</span>
            <span data-intelligence-mbsp-enterprise={mbspSurface?.surface_tiers?.enterprise?.active ? "active" : mbspSurface?.surface_tiers?.enterprise?.unlocked ? "unlocked" : "locked"}>Enterprise {mbspSurface?.surface_tiers?.enterprise?.active ? "active" : mbspSurface?.surface_tiers?.enterprise?.unlocked ? "unlocked" : "locked"}</span>
          </div>

          <div className="middle-layer-clusters">
            {dominant.map((lane) => {
              const band = lane.display_anchor_band || { r: [80], g: [80], b: [80] };
              const accent = `rgb(${band.r?.[0] ?? 80}, ${band.g?.[0] ?? 80}, ${band.b?.[0] ?? 80})`;
              return (
                <article key={`${lane.compartment_id}-${lane.subject}`} style={{ borderLeftColor: accent }}>
                  <h3>{lane.subject}</h3>
                  <p>Phase {lane.phase} · C{lane.compartment_id}</p>
                  <p>Nodes {lane.node_count}</p>
                  <p>Integrity ok {lane.integrity?.ok ?? 0} / mismatch {lane.integrity?.mismatch ?? 0}</p>
                  <div className="rr-node-actions">
                    <button type="button" onClick={() => openLane(lane)}>Open lane</button>
                    <button type="button" onClick={() => openMismatchNode(lane)} disabled={Number(lane.integrity?.mismatch || 0) === 0}>
                      Open mismatch node
                    </button>
                  </div>
                </article>
              );
            })}
            {dominant.length === 0 ? <p className="status-line">No dominant lanes yet.</p> : null}
          </div>

          <section className="workflow-swimlanes">
            <h3>Workflow Swimlane Status</h3>
            <p className="status-line">Swimlanes are sourced from RR dominant lanes and integrity balance.</p>
            <div className="rr-breadcrumb-row" role="list" aria-label="Workflow lanes">
              {dominant.map((lane) => (
                <button key={`wf-${lane.compartment_id}`} type="button" onClick={() => openLane(lane)}>
                  C{lane.compartment_id} {lane.subject}
                </button>
              ))}
            </div>
            <div className="rr-node-chip-row">
              {timelinePhaseGates.map((gate) => (
                <span key={`phase-gate-${gate.phase}`}>{gate.phase}: {gate.locked ? "locked" : "open"}</span>
              ))}
            </div>
            {imbalanceLanes.length > 0 ? (
              <div className="rr-history-list">
                {imbalanceLanes.map((lane) => (
                  <article key={`imb-${lane.compartment_id}`}>
                    <strong>Imbalance detected</strong>
                    <p>{lane.subject}: mismatch {lane.integrity?.mismatch ?? 0} exceeds ok {lane.integrity?.ok ?? 0}.</p>
                    <button type="button" onClick={() => openLane(lane)}>Open lane + map</button>
                  </article>
                ))}
              </div>
            ) : (
              <p className="status-line">No severe imbalance detected.</p>
            )}
          </section>

          <section className="rr-node-detail-panel">
            <h3>Semantic Breadcrumbs</h3>
            <div className="rr-node-chip-row">
              {semanticBreadcrumbs.slice(0, 4).map((crumbs, index) => (
                <span key={`crumb-${index}`}>{normalizeBreadcrumbs(crumbs).join(" → ") || String(crumbs)}</span>
              ))}
            </div>
            <div className="rr-node-chip-row">
              {semanticChecks.map((item) => (
                <span key={`${item.surface}-${item.status}`}>{item.surface}: {item.status}</span>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </section>
  );
}
