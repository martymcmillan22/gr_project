import { useEffect, useMemo, useState } from "react";

import { fetchPreferences, fetchRrCardSpec, fetchRrIndustryMap, saveViewState } from "../api/homepageApi";
import RrNodeCard from "./RrNodeCard";

const STORAGE_KEY = "grassroots.rr.industry-map.state.v1";

const PHASE_FILTERS = [
  { label: "All", value: "" },
  { label: "Idea", value: "RAW" },
  { label: "Seed", value: "SEED" },
  { label: "Project", value: "PROJECT" },
  { label: "Archived", value: "BUSINESS" },
];

function buildPreviewCardFromSpec(specCard, detail) {
  if (!specCard) {
    return null;
  }
  const accent = specCard.spec?.accent_rgb || { r: 80, g: 80, b: 80 };
  const firstIndustry = Array.isArray(detail?.drilldown?.industries) ? detail.drilldown.industries[0] : null;
  const firstSub = firstIndustry?.subindustries?.[0] || "Subindustry";
  return {
    business_id: `preview-${specCard.compartment_id}`,
    seed_id: "-",
    title: `${specCard.subject} Preview Node`,
    subject: specCard.subject,
    phase: specCard.phase,
    display_rgb: accent,
    integrity_state: "ok",
    card_color_spec: {
      compartment_tag: {
        compartment_id: specCard.compartment_id,
      },
      integrity_indicator: specCard.spec?.integrity_indicator,
    },
    industry_path: [detail?.drilldown?.sector, detail?.subject, firstIndustry?.industry, firstSub].filter(Boolean),
  };
}

export default function RrIndustryMapPanel({ panelId = "rr-industry-map-panel" }) {
  const [phaseFilter, setPhaseFilter] = useState("");
  const [payload, setPayload] = useState(null);
  const [specPayload, setSpecPayload] = useState(null);
  const [selectedKey, setSelectedKey] = useState("");
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [selectedSubindustry, setSelectedSubindustry] = useState("");
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [drillDepth, setDrillDepth] = useState("industry");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);

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
      if (typeof parsed.selectedKey === "string") {
        setSelectedKey(parsed.selectedKey);
      }
      if (typeof parsed.selectedIndustry === "string") {
        setSelectedIndustry(parsed.selectedIndustry);
      }
      if (typeof parsed.selectedSubindustry === "string") {
        setSelectedSubindustry(parsed.selectedSubindustry);
      }
      if (typeof parsed.drillDepth === "string") {
        setDrillDepth(parsed.drillDepth);
      }
      if (Number.isFinite(Number(parsed.selectedNodeId))) {
        setSelectedNodeId(Number(parsed.selectedNodeId));
      }
    } catch (_error) {
      // Ignore malformed persisted map state.
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
        const serverState = preference?.view_state?.rr_industry_map;
        if (serverState) {
          if (typeof serverState.phase_filter === "string") {
            setPhaseFilter(serverState.phase_filter);
          }
          if (typeof serverState.selected_key === "string") {
            setSelectedKey(serverState.selected_key);
          }
          if (typeof serverState.selected_industry === "string") {
            setSelectedIndustry(serverState.selected_industry);
          }
          if (typeof serverState.selected_subindustry === "string") {
            setSelectedSubindustry(serverState.selected_subindustry);
          }
          if (typeof serverState.drill_depth === "string") {
            setDrillDepth(serverState.drill_depth);
          }
          if (Number.isFinite(Number(serverState.selected_node_id))) {
            setSelectedNodeId(Number(serverState.selected_node_id));
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
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        phaseFilter,
        selectedKey,
        selectedIndustry,
        selectedSubindustry,
        selectedNodeId,
        drillDepth,
      }),
    );
    saveViewState({
      rr_industry_map: {
        phase_filter: phaseFilter,
        selected_key: selectedKey,
        selected_industry: selectedIndustry,
        selected_subindustry: selectedSubindustry,
        selected_node_id: selectedNodeId,
        drill_depth: drillDepth,
      },
    }).catch(() => {
      // Local storage remains the fallback.
    });
  }, [drillDepth, isHydrated, phaseFilter, selectedIndustry, selectedKey, selectedNodeId, selectedSubindustry]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    Promise.all([fetchRrIndustryMap({ phase: phaseFilter }), fetchRrCardSpec()])
      .then(([nextPayload, nextSpec]) => {
        if (!active) {
          return;
        }
        setPayload(nextPayload);
        setSpecPayload(nextSpec);
      })
      .catch((err) => {
        if (!active) {
          return;
        }
        setError(err?.message || "Unable to load RR industry map");
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
  }, [phaseFilter]);

  const cells = useMemo(() => {
    const rows = Array.isArray(payload?.rows) ? payload.rows : [];
    return rows.flatMap((row) => (Array.isArray(row.cells) ? row.cells : []));
  }, [payload]);

  useEffect(() => {
    if (!selectedKey && cells.length > 0) {
      const first = cells[0];
      setSelectedKey(`${first.group_id}-${first.compartment_id}`);
    }
  }, [cells, selectedKey]);

  useEffect(() => {
    const handleFocusCell = (event) => {
      const groupId = Number(event?.detail?.groupId);
      const compartmentId = Number(event?.detail?.compartmentId);

      if (Number.isFinite(groupId) && Number.isFinite(compartmentId)) {
        setSelectedKey(`${groupId}-${compartmentId}`);
        return;
      }

      if (Number.isFinite(compartmentId)) {
        const match = cells.find((item) => Number(item.compartment_id) === compartmentId);
        if (match) {
          setSelectedKey(`${match.group_id}-${match.compartment_id}`);
        }
      }
    };

    const handleFocusNode = (event) => {
      const businessId = Number(event?.detail?.businessId);
      if (!Number.isFinite(businessId) || businessId <= 0) {
        return;
      }
      const owner = cells.find((cell) => Array.isArray(cell.nodes) && cell.nodes.some((node) => Number(node.business_id) === businessId));
      if (owner) {
        setSelectedKey(`${owner.group_id}-${owner.compartment_id}`);
        setSelectedNodeId(businessId);
        setDrillDepth("nodes");
      }
    };

    window.addEventListener("grassroots:rr-focus-map-cell", handleFocusCell);
    window.addEventListener("grassroots:rr-focus-node", handleFocusNode);

    return () => {
      window.removeEventListener("grassroots:rr-focus-map-cell", handleFocusCell);
      window.removeEventListener("grassroots:rr-focus-node", handleFocusNode);
    };
  }, [cells]);

  const selectedCell = useMemo(
    () => cells.find((cell) => `${cell.group_id}-${cell.compartment_id}` === selectedKey) || null,
    [cells, selectedKey],
  );

  const selectedSpec = useMemo(() => {
    const cards = Array.isArray(specPayload?.cards) ? specPayload.cards : [];
    if (!selectedCell) {
      return null;
    }
    return cards.find((item) => Number(item.compartment_id) === Number(selectedCell.compartment_id)) || null;
  }, [selectedCell, specPayload]);

  const previewCard = useMemo(() => buildPreviewCardFromSpec(selectedSpec, selectedCell), [selectedCell, selectedSpec]);
  const industryOptions = useMemo(
    () => (Array.isArray(selectedCell?.drilldown?.industries) ? selectedCell.drilldown.industries : []),
    [selectedCell],
  );
  const subindustryOptions = useMemo(() => {
    const currentIndustry = industryOptions.find((item) => item.industry === selectedIndustry) || industryOptions[0] || null;
    return Array.isArray(currentIndustry?.subindustries) ? currentIndustry.subindustries : [];
  }, [industryOptions, selectedIndustry]);
  const nodeOptions = useMemo(() => {
    const nodes = Array.isArray(selectedCell?.nodes) ? selectedCell.nodes : [];
    return nodes.filter((node) => {
      const industryMatch = selectedIndustry ? String(node.industry || "") === String(selectedIndustry) : true;
      const subindustryMatch = selectedSubindustry ? String(node.subindustry || "") === String(selectedSubindustry) : true;
      return industryMatch && subindustryMatch;
    });
  }, [selectedCell, selectedIndustry, selectedSubindustry]);
  const selectedNode = useMemo(() => {
    if (!Number.isFinite(Number(selectedNodeId))) {
      return nodeOptions[0] || null;
    }
    return nodeOptions.find((node) => Number(node.business_id) === Number(selectedNodeId)) || nodeOptions[0] || null;
  }, [nodeOptions, selectedNodeId]);

  const setCellWithReset = (nextKey) => {
    setSelectedKey(nextKey);
    setSelectedIndustry("");
    setSelectedSubindustry("");
    setSelectedNodeId(null);
    setDrillDepth("industry");
  };

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">RR Industry Map UI</p>
          <h2>Sector x Industry Group Grid</h2>
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

      {loading ? <p className="status-line">Loading RR industry map...</p> : null}
      {error ? <p className="status-line">{error}</p> : null}

      {payload ? (
        <>
          <div className="rr-map-grid" role="list" aria-label="RR sector by subject map">
            {(payload.rows || []).map((row) => (
              <section key={`${row.sector_id}-${row.phase}`} className="rr-map-row" role="listitem">
                <header>
                  <h3>Sector {row.sector_id}</h3>
                  <span>{row.phase}</span>
                </header>
                <div className="rr-map-cells">
                  {(row.cells || []).map((cell) => {
                    const anchor = cell.anchor_band || { r: [80], g: [80], b: [80] };
                    const r = anchor.r?.[0] ?? 80;
                    const g = anchor.g?.[0] ?? 80;
                    const b = anchor.b?.[0] ?? 80;
                    const selected = selectedKey === `${cell.group_id}-${cell.compartment_id}`;
                    const alpha = 0.18 + Math.max(0, Math.min(1, Number(cell.intensity || 0))) * 0.7;
                    const background = `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(3)})`;
                    return (
                      <button
                        key={`${cell.group_id}-${cell.compartment_id}`}
                        type="button"
                        className={`rr-map-cell ${selected ? "is-selected" : ""}`}
                        style={{ backgroundColor: background }}
                        onClick={() => setCellWithReset(`${cell.group_id}-${cell.compartment_id}`)}
                      >
                        <strong>{cell.subject}</strong>
                        <span>G{cell.group_id} · C{cell.compartment_id}</span>
                        <span>Density {cell.rr_node_count}</span>
                        <span>Mismatch {cell.integrity_mismatch_count}</span>
                        <span>
                          I {cell.phase_distribution?.Idea ?? 0} | S {cell.phase_distribution?.Seed ?? 0} | P {cell.phase_distribution?.Project ?? 0}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </section>
            ))}
          </div>

          {selectedCell ? (
            <section className="rr-map-drilldown">
              <div>
                <p className="eyebrow">Drill-down</p>
                <h3>{selectedCell.subject}</h3>
                <div className="rr-breadcrumb-row" role="list" aria-label="Map drill depth">
                  <button type="button" className={drillDepth === "industry" ? "is-active" : ""} onClick={() => setDrillDepth("industry")}>Industry</button>
                  <button type="button" className={drillDepth === "subindustry" ? "is-active" : ""} onClick={() => setDrillDepth("subindustry")}>Subindustry</button>
                  <button type="button" className={drillDepth === "nodes" ? "is-active" : ""} onClick={() => setDrillDepth("nodes")}>Nodes</button>
                </div>

                <div className="rr-drill-options">
                  <p className="status-line">Sector: {selectedCell.drilldown?.sector || "n/a"}</p>
                  <p className="status-line">Subject: {selectedCell.drilldown?.subject || "n/a"}</p>
                  {drillDepth === "industry" ? (
                    <ul>
                      {industryOptions.map((industry) => (
                        <li key={industry.industry}>
                          <button
                            type="button"
                            className={selectedIndustry === industry.industry ? "is-active" : ""}
                            onClick={() => {
                              setSelectedIndustry(industry.industry);
                              setSelectedSubindustry("");
                              setDrillDepth("subindustry");
                            }}
                          >
                            {industry.industry}
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {drillDepth === "subindustry" ? (
                    <ul>
                      {subindustryOptions.map((sub) => (
                        <li key={`${selectedIndustry || "*"}-${sub}`}>
                          <button
                            type="button"
                            className={selectedSubindustry === sub ? "is-active" : ""}
                            onClick={() => {
                              setSelectedSubindustry(sub);
                              setDrillDepth("nodes");
                            }}
                          >
                            {sub}
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </div>
              <div>
                <p className="eyebrow">Card + Node Preview</p>
                {selectedNode ? (
                  <RrNodeCard
                    card={selectedNode}
                    showSemanticChips
                    showProvenanceChips
                    onOpenDetail={(businessId) => {
                      setSelectedNodeId(businessId);
                      window.dispatchEvent(new CustomEvent("grassroots:rr-focus-node", { detail: { businessId, source: "rr-map" } }));
                    }}
                    onOpenMiddleLayer={(businessId, compartmentId) => {
                      window.dispatchEvent(
                        new CustomEvent("grassroots:rr-open-middle-layer", {
                          detail: { businessId, compartmentId, source: "rr-map" },
                        }),
                      );
                    }}
                  />
                ) : (
                  <RrNodeCard card={previewCard} />
                )}
                {drillDepth === "nodes" ? (
                  <div className="rr-drill-node-list">
                    {nodeOptions.length > 0 ? nodeOptions.map((node) => (
                      <button
                        key={node.business_id}
                        type="button"
                        className={Number(selectedNode?.business_id) === Number(node.business_id) ? "is-active" : ""}
                        onClick={() => setSelectedNodeId(node.business_id)}
                      >
                        {node.title} (#{node.business_id})
                      </button>
                    )) : <p className="status-line">No nodes in this path selection.</p>}
                  </div>
                ) : null}
              </div>
            </section>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
