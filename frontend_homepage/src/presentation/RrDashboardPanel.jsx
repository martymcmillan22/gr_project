import { useEffect, useMemo, useState } from "react";

import { fetchPreferences, fetchRrDashboard, fetchRrNodeDetail, saveViewState } from "../api/homepageApi";
import RrNodeCard from "./RrNodeCard";

const STORAGE_KEY = "grassroots.rr.dashboard.state.v1";
const DEFAULT_PHASE_DISTRIBUTION = { Idea: 0, Seed: 0, Project: 0, Archived: 0 };

const PHASE_FILTERS = [
  { label: "All", value: "" },
  { label: "Idea", value: "RAW" },
  { label: "Seed", value: "SEED" },
  { label: "Project", value: "PROJECT" },
  { label: "Archived", value: "BUSINESS" },
];

export default function RrDashboardPanel({ panelId = "rr-dashboard-panel", onDataChange }) {
  const [phaseFilter, setPhaseFilter] = useState("");
  const [selectedLane, setSelectedLane] = useState(null);
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);
  const [detailPayload, setDetailPayload] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw);
      if (typeof parsed.phaseFilter === "string") {
        setPhaseFilter(parsed.phaseFilter);
      }
      if (Number.isFinite(Number(parsed.selectedLane))) {
        setSelectedLane(Number(parsed.selectedLane));
      }
    } catch (_error) {
      // Ignore malformed persisted state.
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetchPreferences()
      .then((payload) => {
        if (!active) {
          return;
        }
        const preference = Array.isArray(payload?.results) ? payload.results[0] : null;
        const serverState = preference?.view_state?.rr_dashboard;
        if (serverState) {
          if (typeof serverState.phase_filter === "string") {
            setPhaseFilter(serverState.phase_filter);
          }
          if (Number.isFinite(Number(serverState.selected_lane))) {
            setSelectedLane(Number(serverState.selected_lane));
          }
        }
      })
      .catch(() => {
        // Local storage handles offline fallback.
      })
      .finally(() => {
        if (active) {
          setIsHydrated(true);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    const state = {
      phaseFilter,
      selectedLane,
    };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    saveViewState({ rr_dashboard: state }).catch(() => {
      // Local storage remains the fallback.
    });
  }, [isHydrated, phaseFilter, selectedLane]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    fetchRrDashboard({ phase: phaseFilter, limit: 6 })
      .then((nextPayload) => {
        if (!active) {
          return;
        }
        setPayload(nextPayload);
        if (typeof onDataChange === "function") {
          onDataChange(nextPayload);
        }
      })
      .catch((err) => {
        if (!active) {
          return;
        }
        setError(err?.message || "Unable to load RR dashboard");
        setPayload(null);
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [onDataChange, phaseFilter]);

  useEffect(() => {
    const handleFocusLane = (event) => {
      const next = Number(event?.detail?.compartmentId);
      if (Number.isFinite(next)) {
        setSelectedLane(next);
      }
    };

    const handleFocusNode = (event) => {
      const businessId = Number(event?.detail?.businessId);
      if (!Number.isFinite(businessId) || businessId <= 0) {
        return;
      }
      setDetailLoading(true);
      setDetailError("");
      fetchRrNodeDetail(businessId)
        .then((nextPayload) => {
          setDetailPayload(nextPayload);
          const laneId = Number(nextPayload?.node?.card_color_spec?.compartment_tag?.compartment_id);
          if (Number.isFinite(laneId)) {
            setSelectedLane(laneId);
          }
        })
        .catch((err) => {
          setDetailError(err?.message || "Unable to load RR node detail");
          setDetailPayload(null);
        })
        .finally(() => {
          setDetailLoading(false);
        });
    };

    window.addEventListener("grassroots:rr-focus-lane", handleFocusLane);
    window.addEventListener("grassroots:rr-focus-node", handleFocusNode);
    return () => {
      window.removeEventListener("grassroots:rr-focus-lane", handleFocusLane);
      window.removeEventListener("grassroots:rr-focus-node", handleFocusNode);
    };
  }, []);

  const lanes = useMemo(() => (Array.isArray(payload?.lanes) ? payload.lanes : []), [payload]);
  const selectedLanePayload = useMemo(() => {
    if (!Number.isFinite(Number(selectedLane))) {
      return null;
    }
    return lanes.find((lane) => Number(lane.compartment_id) === Number(selectedLane)) || null;
  }, [lanes, selectedLane]);

  const openNodeDetail = (businessId) => {
    window.dispatchEvent(new CustomEvent("grassroots:rr-focus-node", { detail: { businessId, source: "rr-dashboard" } }));
  };

  const openMiddleLayer = (businessId, compartmentId) => {
    window.dispatchEvent(
      new CustomEvent("grassroots:rr-open-middle-layer", {
        detail: { businessId, compartmentId, source: "rr-dashboard" },
      }),
    );
  };

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">RR Dashboard UI</p>
          <h2>Subject Lanes</h2>
        </div>
        <label className="semantic-select-field">
          Phase Filter
          <select value={phaseFilter} onChange={(event) => setPhaseFilter(event.target.value)}>
            {PHASE_FILTERS.map((item) => (
              <option key={item.label} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading ? <p className="status-line">Loading RR lanes...</p> : null}
      {error ? <p className="status-line">{error}</p> : null}

      {payload ? (
        <>
          <div className="rr-status-band-grid">
            <div>Idea <strong>{payload.status_bands?.Idea ?? 0}</strong></div>
            <div>Seed <strong>{payload.status_bands?.Seed ?? 0}</strong></div>
            <div>Project <strong>{payload.status_bands?.Project ?? 0}</strong></div>
            <div>Archived <strong>{payload.status_bands?.Archived ?? 0}</strong></div>
          </div>
          <p className="status-line">
            Integrity strip: ok {payload.integrity_strip?.ok ?? 0} | mismatch {payload.integrity_strip?.mismatch ?? 0} | unavailable {payload.integrity_strip?.unavailable ?? 0}
          </p>

          <div className="rr-lane-grid" role="list" aria-label="RR subject lanes">
            {lanes.map((lane) => {
              const anchor = lane.display_anchor_band || { r: [80], g: [80], b: [80] };
              const anchorColor = `rgb(${anchor.r?.[0] ?? 80}, ${anchor.g?.[0] ?? 80}, ${anchor.b?.[0] ?? 80})`;
              const laneIsSelected = Number(selectedLane) === Number(lane.compartment_id);
              const phaseDistribution = lane.phase_distribution || DEFAULT_PHASE_DISTRIBUTION;
              return (
                <article key={lane.compartment_id} className={`rr-lane ${laneIsSelected ? "is-selected" : ""}`} role="listitem">
                  <header style={{ borderTopColor: anchorColor }}>
                    <h3>{lane.subject}</h3>
                    <span>C{lane.compartment_id}</span>
                  </header>
                  <p className="status-line">{lane.phase} · Nodes {lane.node_count}</p>
                  <p className="status-line">Integrity ok {lane.integrity?.ok ?? 0} / mismatch {lane.integrity?.mismatch ?? 0}</p>
                  <div className="rr-lane-phase-strip" role="list" aria-label={`Phase distribution for ${lane.subject}`}>
                    {Object.entries(phaseDistribution).map(([phaseName, count]) => (
                      <button
                        key={`${lane.compartment_id}-${phaseName}`}
                        type="button"
                        className="rr-lane-phase-pill"
                        onClick={() => setSelectedLane(lane.compartment_id)}
                        role="listitem"
                      >
                        {phaseName} {count}
                      </button>
                    ))}
                  </div>
                  <div className="rr-lane-cards">
                    {(lane.cards || []).slice(0, 3).map((card) => (
                      <RrNodeCard
                        key={card.business_id}
                        card={card}
                        compact
                        onOpenDetail={openNodeDetail}
                        onOpenMiddleLayer={openMiddleLayer}
                        showSemanticChips
                        showProvenanceChips
                      />
                    ))}
                    {(!lane.cards || lane.cards.length === 0) ? <p className="status-line">No nodes in this lane.</p> : null}
                  </div>
                  <div className="rr-lane-actions">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedLane(lane.compartment_id);
                        window.dispatchEvent(
                          new CustomEvent("grassroots:rr-focus-map-cell", {
                            detail: { compartmentId: lane.compartment_id, source: "rr-dashboard" },
                          }),
                        );
                      }}
                    >
                      Open in map
                    </button>
                  </div>
                </article>
              );
            })}
          </div>

          <section className="rr-node-detail-panel">
            <div className="semantic-stack-head">
              <div>
                <p className="eyebrow">Node Detail</p>
                <h3>{selectedLanePayload ? `${selectedLanePayload.subject} Focus` : "Select a lane"}</h3>
              </div>
            </div>
            {detailLoading ? <p className="status-line">Loading RR node detail...</p> : null}
            {detailError ? <p className="status-line">{detailError}</p> : null}
            {detailPayload?.node ? (
              <>
                <RrNodeCard
                  card={detailPayload.node}
                  mode="expanded"
                  showSemanticChips
                  showProvenanceChips
                  onOpenDetail={openNodeDetail}
                  onOpenMiddleLayer={openMiddleLayer}
                />
                <div className="rr-history-list">
                  {(detailPayload.integrity_history || []).map((event) => (
                    <article key={`${event.event}-${event.timestamp}`}>
                      <strong>{event.event}</strong>
                      <p>{event.detail}</p>
                      <span>{event.timestamp}</span>
                    </article>
                  ))}
                </div>
              </>
            ) : (
              <p className="status-line">Select any RR node to inspect identity and integrity history.</p>
            )}
          </section>
        </>
      ) : null}
    </section>
  );
}
