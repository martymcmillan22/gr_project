import { useCallback, useEffect, useMemo, useState } from "react";

import {
  deleteSemanticPresetStore,
  fetchSemanticPresetsStore,
  fetchSemanticStoryClusters,
  fetchSemanticStoryDiff,
  fetchSemanticStorySearch,
  saveSemanticPresetStore,
} from "../api/homepageApi";

export default function SemanticOperationsPanel({ timelineSelection }) {
  const [filters, setFilters] = useState({
    mlas_color: timelineSelection?.mlasColorToken || "",
    timeline_cell: timelineSelection?.timelineLabel || "",
    semantic_intent: timelineSelection?.semanticIntentId || "",
    scaffold_version: "",
    dchd_atom: "",
    status: "",
    semantic_path: "",
  });
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const [clusterBy, setClusterBy] = useState("mlas");
  const [clusters, setClusters] = useState([]);
  const [isClusterLoading, setIsClusterLoading] = useState(false);
  const [searchSortKey, setSearchSortKey] = useState("entry_id");
  const [heatmapRows, setHeatmapRows] = useState([]);
  const [isHeatmapLoading, setIsHeatmapLoading] = useState(false);
  const [selectedHeatmapKey, setSelectedHeatmapKey] = useState("");

  const [presets, setPresets] = useState([]);
  const [searchPresetId, setSearchPresetId] = useState("");
  const [clusterPresetId, setClusterPresetId] = useState("");
  const [searchPresetName, setSearchPresetName] = useState("");
  const [clusterPresetName, setClusterPresetName] = useState("");
  const [isPresetSaving, setIsPresetSaving] = useState(false);

  const [diffSourceId, setDiffSourceId] = useState(8);
  const [diffTargetId, setDiffTargetId] = useState(9);
  const [diffPayload, setDiffPayload] = useState(null);
  const [isDiffing, setIsDiffing] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    setFilters((current) => ({
      ...current,
      mlas_color: timelineSelection?.mlasColorToken || current.mlas_color,
      timeline_cell: timelineSelection?.timelineLabel || current.timeline_cell,
      semantic_intent: timelineSelection?.semanticIntentId || current.semantic_intent,
    }));
  }, [timelineSelection]);

  const runSearch = useCallback(async () => {
    setIsSearching(true);
    setError("");
    try {
      const payload = await fetchSemanticStorySearch(filters);
      setSearchResults(Array.isArray(payload?.results) ? payload.results : []);
    } catch (err) {
      setError(err.message || "Could not run semantic search");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [filters]);

  const runClusters = useCallback(async () => {
    setIsClusterLoading(true);
    setError("");
    try {
      const payload = await fetchSemanticStoryClusters(clusterBy);
      setClusters(Array.isArray(payload?.clusters) ? payload.clusters : []);
    } catch (err) {
      setError(err.message || "Could not load semantic clusters");
      setClusters([]);
    } finally {
      setIsClusterLoading(false);
    }
  }, [clusterBy]);

  const runDiff = useCallback(async () => {
    setIsDiffing(true);
    setError("");
    try {
      const payload = await fetchSemanticStoryDiff(diffSourceId, diffTargetId);
      setDiffPayload(payload || null);
    } catch (err) {
      setError(err.message || "Could not compute semantic diff");
      setDiffPayload(null);
    } finally {
      setIsDiffing(false);
    }
  }, [diffSourceId, diffTargetId]);

  const runHeatmap = useCallback(async () => {
    setIsHeatmapLoading(true);
    setError("");
    try {
      const payload = await fetchSemanticStorySearch({});
      setHeatmapRows(Array.isArray(payload?.results) ? payload.results : []);
    } catch (err) {
      setError(err.message || "Could not build semantic heatmap");
      setHeatmapRows([]);
    } finally {
      setIsHeatmapLoading(false);
    }
  }, []);

  const loadPresets = useCallback(async () => {
    try {
      const payload = await fetchSemanticPresetsStore();
      setPresets(Array.isArray(payload?.results) ? payload.results : []);
    } catch (_err) {
      setPresets([]);
    }
  }, []);

  useEffect(() => {
    runSearch();
    runClusters();
    runDiff();
    runHeatmap();
  }, [runClusters, runDiff, runHeatmap, runSearch]);

  useEffect(() => {
    loadPresets();
  }, [loadPresets]);

  const clusterPreview = useMemo(() => clusters.slice(0, 6), [clusters]);
  const searchPresets = useMemo(() => presets.filter((item) => item.preset_type === "search"), [presets]);
  const clusterPresets = useMemo(() => presets.filter((item) => item.preset_type === "cluster"), [presets]);

  const sortedSearchResults = useMemo(() => {
    const rows = [...searchResults];
    rows.sort((left, right) => {
      if (searchSortKey === "scaffold_version") {
        return Number(right?.scaffold_version || -1) - Number(left?.scaffold_version || -1);
      }
      if (searchSortKey === "entry_id") {
        return Number(left?.entry_id || 0) - Number(right?.entry_id || 0);
      }
      return String(left?.[searchSortKey] || "").localeCompare(String(right?.[searchSortKey] || ""));
    });
    return rows;
  }, [searchResults, searchSortKey]);

  const normalizeTimelinePhase = useCallback((rawValue) => {
    const token = String(rawValue || "").trim().toLowerCase().replace(/_/g, "-");
    if (token === "present-past" || token === "present to past" || token === "present/past") {
      return "present-past";
    }
    if (token === "present-future" || token === "present to future" || token === "present/future") {
      return "present-future";
    }
    if (token === "past") {
      return "past";
    }
    if (token === "future") {
      return "future";
    }
    if (token === "present") {
      return "present-past";
    }
    if (token.includes("present") && token.includes("past")) {
      return "present-past";
    }
    if (token.includes("present") && token.includes("future")) {
      return "present-future";
    }
    if (token.includes("past")) {
      return "past";
    }
    if (token.includes("future")) {
      return "future";
    }
    return "unknown";
  }, []);

  const heatmapPhases = useMemo(() => ["past", "present-past", "present-future", "future"], []);

  const heatmapMlasOrder = useMemo(() => {
    const preferred = [
      "RED",
      "BLUE",
      "YELLOW",
      "GREEN",
      "PURPLE",
      "TEAL",
      "ORANGE",
      "LIME",
      "PINK",
      "CYAN",
      "AMBER",
      "GREEN_LIME",
      "unknown",
    ];
    const discovered = new Set(
      (heatmapRows || []).map((row) => String(row?.mlas_color || "unknown").toUpperCase() || "unknown"),
    );
    return preferred.filter((token) => discovered.has(token) || token === "unknown");
  }, [heatmapRows]);

  const heatmapCells = useMemo(() => {
    const stats = {};

    const ensureCell = (mlas, phase) => {
      const key = `${mlas}::${phase}`;
      if (!stats[key]) {
        stats[key] = {
          mlas,
          phase,
          density: 0,
          semanticPaths: new Set(),
          semanticIntents: new Set(),
          versions: [],
          dchdAtomCount: 0,
          nodeKeys: new Set(),
        };
      }
      return stats[key];
    };

    for (const row of heatmapRows || []) {
      const mlas = String(row?.mlas_color || "unknown").toUpperCase() || "unknown";
      const phase = normalizeTimelinePhase(row?.timeline_cell || row?.timeline_phase);
      const cell = ensureCell(mlas, phase);
      if (!heatmapPhases.includes(phase)) {
        continue;
      }
      cell.density += 1;
      if (row?.semantic_path) {
        cell.semanticPaths.add(String(row.semantic_path));
      }
      if (row?.semantic_intent) {
        cell.semanticIntents.add(String(row.semantic_intent));
      }
      if (row?.hierarchy_node_key) {
        cell.nodeKeys.add(String(row.hierarchy_node_key));
      }
      if (Number.isFinite(Number(row?.scaffold_version))) {
        cell.versions.push(Number(row.scaffold_version));
      }
      const atomCount = Array.isArray(row?.dchd_atoms) ? row.dchd_atoms.length : 0;
      cell.dchdAtomCount += atomCount;
    }

    const matrix = [];
    for (const mlas of heatmapMlasOrder) {
      for (const phase of heatmapPhases) {
        const cell = ensureCell(mlas, phase);
        const drift = cell.density ? Number((cell.semanticPaths.size / cell.density).toFixed(2)) : 0;
        const hotspot = cell.semanticIntents.size + cell.nodeKeys.size;
        const avgDchd = cell.density ? Number((cell.dchdAtomCount / cell.density).toFixed(2)) : 0;
        const versionMin = cell.versions.length ? Math.min(...cell.versions) : null;
        const versionMax = cell.versions.length ? Math.max(...cell.versions) : null;
        matrix.push({
          key: `${mlas}::${phase}`,
          mlas,
          phase,
          density: cell.density,
          semanticDrift: drift,
          hotspot,
          versionRange: versionMin === null ? "-" : versionMin === versionMax ? `${versionMin}` : `${versionMin}-${versionMax}`,
          avgDchd,
        });
      }
    }
    return matrix;
  }, [heatmapMlasOrder, heatmapPhases, heatmapRows, normalizeTimelinePhase]);

  const heatmapMaxDensity = useMemo(() => {
    return heatmapCells.reduce((max, cell) => Math.max(max, Number(cell?.density || 0)), 0) || 1;
  }, [heatmapCells]);

  const transitionalDeltaRows = useMemo(() => {
    const cellByKey = {};
    for (const cell of heatmapCells) {
      cellByKey[cell.key] = cell;
    }

    const toVersionSpan = (rangeLabel) => {
      const token = String(rangeLabel || "-");
      if (!token || token === "-") {
        return 0;
      }
      if (!token.includes("-")) {
        return 0;
      }
      const parts = token.split("-").map((part) => Number(part.trim()));
      if (parts.length !== 2 || !Number.isFinite(parts[0]) || !Number.isFinite(parts[1])) {
        return 0;
      }
      return Math.max(0, parts[1] - parts[0]);
    };

    return heatmapMlasOrder.map((mlas) => {
      const presentPast = cellByKey[`${mlas}::present-past`] || {
        density: 0,
        semanticDrift: 0,
        hotspot: 0,
        avgDchd: 0,
        versionRange: "-",
      };
      const presentFuture = cellByKey[`${mlas}::present-future`] || {
        density: 0,
        semanticDrift: 0,
        hotspot: 0,
        avgDchd: 0,
        versionRange: "-",
      };

      const deltaDensity = Number((Number(presentFuture.density || 0) - Number(presentPast.density || 0)).toFixed(2));
      const deltaDrift = Number((Number(presentFuture.semanticDrift || 0) - Number(presentPast.semanticDrift || 0)).toFixed(2));
      const deltaHotspot = Number((Number(presentFuture.hotspot || 0) - Number(presentPast.hotspot || 0)).toFixed(2));
      const deltaDchd = Number((Number(presentFuture.avgDchd || 0) - Number(presentPast.avgDchd || 0)).toFixed(2));
      const versionSpreadDelta = toVersionSpan(presentFuture.versionRange) - toVersionSpan(presentPast.versionRange);

      const trend = deltaDensity > 0
        ? "future-leaning"
        : deltaDensity < 0
          ? "past-leaning"
          : "balanced";

      return {
        key: `delta::${mlas}`,
        mlas,
        trend,
        deltaDensity,
        deltaDrift,
        deltaHotspot,
        deltaDchd,
        versionSpreadDelta,
      };
    });
  }, [heatmapCells, heatmapMlasOrder]);

  const formatSigned = useCallback((value) => {
    const numeric = Number(value || 0);
    if (!Number.isFinite(numeric)) {
      return "0";
    }
    const sign = numeric > 0 ? "+" : "";
    return `${sign}${numeric}`;
  }, []);

  const applyHeatmapCellContext = useCallback(async (cell) => {
    if (!cell) {
      return;
    }

    const toRowMlas = (value) => String(value || "unknown").toUpperCase() || "unknown";
    const toRowPhase = (timelineCell, timelinePhase) => normalizeTimelinePhase(timelineCell || timelinePhase);

    const normalizedMlas = String(cell?.mlas || "unknown").toUpperCase();
    const normalizedPhase = normalizeTimelinePhase(cell?.phase);
    const nextFilters = {
      ...filters,
      mlas_color: normalizedMlas === "unknown" ? "" : normalizedMlas,
      timeline_cell: normalizedPhase,
      semantic_intent: "",
      scaffold_version: "",
      dchd_atom: "",
      status: "",
      semantic_path: "",
    };

    setSelectedHeatmapKey(cell.key);
    setFilters(nextFilters);
    setClusterBy("timeline_phase");
    setError("");

    const matchingRows = (heatmapRows || [])
      .filter((row) => {
        const rowMlas = toRowMlas(row?.mlas_color);
        const rowPhase = toRowPhase(row?.timeline_cell, row?.timeline_phase);
        return rowMlas === normalizedMlas && rowPhase === normalizedPhase;
      })
      .sort((left, right) => {
        const versionDelta = Number(right?.scaffold_version || -1) - Number(left?.scaffold_version || -1);
        if (versionDelta !== 0) {
          return versionDelta;
        }
        return Number(right?.entry_id || 0) - Number(left?.entry_id || 0);
      });

    const nextSourceId = Number(matchingRows[0]?.entry_id || 0);
    const nextTargetId = Number(matchingRows[1]?.entry_id || 0);

    if (nextSourceId) {
      setDiffSourceId(nextSourceId);
    }
    if (nextTargetId) {
      setDiffTargetId(nextTargetId);
    }

    setIsSearching(true);
    try {
      const payload = await fetchSemanticStorySearch(nextFilters);
      setSearchResults(Array.isArray(payload?.results) ? payload.results : []);
    } catch (err) {
      setError(err.message || "Could not run semantic search");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }

    setIsClusterLoading(true);
    try {
      const payload = await fetchSemanticStoryClusters("timeline_phase");
      setClusters(Array.isArray(payload?.clusters) ? payload.clusters : []);
    } catch (err) {
      setError(err.message || "Could not load semantic clusters");
      setClusters([]);
    } finally {
      setIsClusterLoading(false);
    }

    if (nextSourceId && nextTargetId && nextSourceId !== nextTargetId) {
      setIsDiffing(true);
      try {
        const payload = await fetchSemanticStoryDiff(nextSourceId, nextTargetId);
        setDiffPayload(payload || null);
      } catch (err) {
        setError(err.message || "Could not compute semantic diff");
        setDiffPayload(null);
      } finally {
        setIsDiffing(false);
      }
    } else {
      setDiffPayload(null);
    }
  }, [filters, heatmapRows, normalizeTimelinePhase]);

  const saveSearchPreset = useCallback(async () => {
    const name = String(searchPresetName || "").trim();
    if (!name) {
      setError("Search preset name is required");
      return;
    }
    setIsPresetSaving(true);
    setError("");
    try {
      await saveSemanticPresetStore({
        name,
        preset_type: "search",
        payload: { filters },
      });
      setSearchPresetName("");
      await loadPresets();
    } catch (err) {
      setError(err.message || "Could not save search preset");
    } finally {
      setIsPresetSaving(false);
    }
  }, [filters, loadPresets, searchPresetName]);

  const saveClusterPreset = useCallback(async () => {
    const name = String(clusterPresetName || "").trim();
    if (!name) {
      setError("Cluster preset name is required");
      return;
    }
    setIsPresetSaving(true);
    setError("");
    try {
      await saveSemanticPresetStore({
        name,
        preset_type: "cluster",
        payload: { cluster_by: clusterBy },
      });
      setClusterPresetName("");
      await loadPresets();
    } catch (err) {
      setError(err.message || "Could not save cluster preset");
    } finally {
      setIsPresetSaving(false);
    }
  }, [clusterBy, clusterPresetName, loadPresets]);

  const applySearchPreset = useCallback(() => {
    const preset = searchPresets.find((item) => String(item.id) === String(searchPresetId));
    if (!preset) {
      return;
    }
    const nextFilters = preset?.payload?.filters;
    if (nextFilters && typeof nextFilters === "object") {
      setFilters((current) => ({ ...current, ...nextFilters }));
    }
  }, [searchPresetId, searchPresets]);

  const applyClusterPreset = useCallback(() => {
    const preset = clusterPresets.find((item) => String(item.id) === String(clusterPresetId));
    if (!preset) {
      return;
    }
    const nextClusterBy = String(preset?.payload?.cluster_by || "");
    if (nextClusterBy) {
      setClusterBy(nextClusterBy);
    }
  }, [clusterPresetId, clusterPresets]);

  const deleteSelectedPreset = useCallback(async (presetId) => {
    if (!presetId) {
      return;
    }
    setIsPresetSaving(true);
    setError("");
    try {
      await deleteSemanticPresetStore(presetId);
      if (String(searchPresetId) === String(presetId)) {
        setSearchPresetId("");
      }
      if (String(clusterPresetId) === String(presetId)) {
        setClusterPresetId("");
      }
      await loadPresets();
    } catch (err) {
      setError(err.message || "Could not delete preset");
    } finally {
      setIsPresetSaving(false);
    }
  }, [clusterPresetId, loadPresets, searchPresetId]);

  const assignDiffPair = useCallback((entryId) => {
    const normalized = Number(entryId || 0);
    if (!normalized) {
      return;
    }
    setDiffSourceId((current) => {
      if (!current || Number(current) === Number(diffTargetId)) {
        return normalized;
      }
      return current;
    });
    setDiffTargetId((current) => {
      if (!current || Number(current) === Number(normalized)) {
        return diffSourceId || normalized;
      }
      return current;
    });
  }, [diffSourceId, diffTargetId]);

  const setAsDiffSource = useCallback((entryId) => {
    setDiffSourceId(Number(entryId || 0));
  }, []);

  const setAsDiffTarget = useCallback((entryId) => {
    setDiffTargetId(Number(entryId || 0));
  }, []);

  return (
    <section className="semantic-ops" aria-label="Semantic intelligence dashboard">
      {error ? <p className="routing-error">{error}</p> : null}

      <div className="semantic-ops-grid">
        <div className="semantic-ops-card">
          <h4>Semantic Search Table</h4>
          <div className="semantic-preset-row">
            <select value={searchPresetId} onChange={(event) => setSearchPresetId(event.target.value)}>
              <option value="">Select search preset</option>
              {searchPresets.map((preset) => (
                <option key={preset.id} value={preset.id}>{preset.name}</option>
              ))}
            </select>
            <button type="button" onClick={applySearchPreset}>Load</button>
            <button type="button" onClick={() => deleteSelectedPreset(searchPresetId)} disabled={!searchPresetId || isPresetSaving}>Delete</button>
          </div>
          <div className="semantic-filters-grid">
            <label>
              MLAS Color
              <input
                value={filters.mlas_color}
                onChange={(event) => setFilters((current) => ({ ...current, mlas_color: event.target.value }))}
              />
            </label>
            <label>
              Timeline Cell
              <input
                value={filters.timeline_cell}
                onChange={(event) => setFilters((current) => ({ ...current, timeline_cell: event.target.value }))}
              />
            </label>
            <label>
              Semantic Intent
              <input
                value={filters.semantic_intent}
                onChange={(event) => setFilters((current) => ({ ...current, semantic_intent: event.target.value }))}
              />
            </label>
            <label>
              Scaffold Version
              <input
                value={filters.scaffold_version}
                onChange={(event) => setFilters((current) => ({ ...current, scaffold_version: event.target.value }))}
              />
            </label>
            <label>
              DCHD Atom
              <input
                value={filters.dchd_atom}
                onChange={(event) => setFilters((current) => ({ ...current, dchd_atom: event.target.value }))}
              />
            </label>
            <label>
              Status
              <input
                placeholder="pending/in_progress/complete"
                value={filters.status}
                onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}
              />
            </label>
          </div>
          <button type="button" onClick={runSearch} disabled={isSearching}>
            {isSearching ? "Searching..." : "Run Semantic Search"}
          </button>
          <div className="semantic-preset-row">
            <input
              placeholder="Save search preset"
              value={searchPresetName}
              onChange={(event) => setSearchPresetName(event.target.value)}
            />
            <button type="button" onClick={saveSearchPreset} disabled={isPresetSaving}>
              {isPresetSaving ? "Saving..." : "Save Preset"}
            </button>
          </div>
          <div className="semantic-table-controls">
            <p className="status-line">Results: {searchResults.length}</p>
            <label>
              Sort
              <select value={searchSortKey} onChange={(event) => setSearchSortKey(event.target.value)}>
                <option value="entry_id">Entry ID</option>
                <option value="scaffold_version">Scaffold Version</option>
                <option value="mlas_color">MLAS</option>
                <option value="status">Status</option>
              </select>
            </label>
          </div>
          <div className="semantic-table-wrap">
            <table className="semantic-table">
              <thead>
                <tr>
                  <th>Entry</th>
                  <th>Status</th>
                  <th>MLAS</th>
                  <th>Timeline</th>
                  <th>Intent</th>
                  <th>Node</th>
                  <th>Version</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedSearchResults.map((item) => (
                  <tr key={item.entry_id}>
                    <td>#{item.entry_id} {item.title}</td>
                    <td>{item.status || "-"}</td>
                    <td>{item.mlas_color || "-"}</td>
                    <td>{item.timeline_cell || "-"}</td>
                    <td>{item.semantic_intent || "-"}</td>
                    <td>{item.hierarchy_node_key || "-"}</td>
                    <td>{item.scaffold_version || "-"}</td>
                    <td>
                      <div className="semantic-row-actions">
                        <button type="button" onClick={() => setAsDiffSource(item.entry_id)}>Source</button>
                        <button type="button" onClick={() => setAsDiffTarget(item.entry_id)}>Target</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="semantic-ops-card">
          <h4>Constellation Cluster Cards</h4>
          <div className="semantic-preset-row">
            <select value={clusterPresetId} onChange={(event) => setClusterPresetId(event.target.value)}>
              <option value="">Select cluster preset</option>
              {clusterPresets.map((preset) => (
                <option key={preset.id} value={preset.id}>{preset.name}</option>
              ))}
            </select>
            <button type="button" onClick={applyClusterPreset}>Load</button>
            <button type="button" onClick={() => deleteSelectedPreset(clusterPresetId)} disabled={!clusterPresetId || isPresetSaving}>Delete</button>
          </div>
          <label>
            Cluster By
            <select value={clusterBy} onChange={(event) => setClusterBy(event.target.value)}>
              <option value="mlas">MLAS</option>
              <option value="timeline_phase">Timeline Phase</option>
              <option value="semantic_path">Semantic Path</option>
              <option value="scaffold_version">Scaffold Version</option>
              <option value="dchd_cluster">DCHD Cluster</option>
            </select>
          </label>
          <button type="button" onClick={runClusters} disabled={isClusterLoading}>
            {isClusterLoading ? "Loading..." : "Build Constellation"}
          </button>
          <div className="semantic-preset-row">
            <input
              placeholder="Save cluster preset"
              value={clusterPresetName}
              onChange={(event) => setClusterPresetName(event.target.value)}
            />
            <button type="button" onClick={saveClusterPreset} disabled={isPresetSaving}>
              {isPresetSaving ? "Saving..." : "Save Preset"}
            </button>
          </div>
          <div className="semantic-cluster-grid">
            {clusterPreview.map((cluster) => (
              <article key={cluster.cluster_key} className="semantic-cluster-card">
                <header>
                  <strong>{cluster.cluster_key || "unknown"}</strong>
                  <span>{cluster.count} entries</span>
                </header>
                <ul className="semantic-inline-list">
                  {(cluster.entries || []).slice(0, 4).map((entry) => (
                    <li key={`${cluster.cluster_key}_${entry.entry_id}`}>
                      <button type="button" onClick={() => assignDiffPair(entry.entry_id)}>
                        #{entry.entry_id} {entry.title}
                      </button>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </div>

        <div className="semantic-ops-card semantic-diff-card">
          <h4>Side-by-Side Semantic Diff Viewer</h4>
          <div className="semantic-diff-controls">
            <label>
              Source ID
              <input
                type="number"
                min="1"
                value={diffSourceId}
                onChange={(event) => setDiffSourceId(Number(event.target.value || 0))}
              />
            </label>
            <label>
              Target ID
              <input
                type="number"
                min="1"
                value={diffTargetId}
                onChange={(event) => setDiffTargetId(Number(event.target.value || 0))}
              />
            </label>
          </div>
          <button type="button" onClick={runDiff} disabled={isDiffing}>
            {isDiffing ? "Diffing..." : "Run Semantic Diff"}
          </button>
          {diffPayload?.diff ? (
            <>
              <div className="semantic-diff-sides">
                <div className="semantic-diff-pane">
                  <h5>Source</h5>
                  <p className="status-line">#{diffPayload.source?.entry_id} {diffPayload.source?.title}</p>
                  <p className="status-line">Version: {diffPayload.source?.scaffold_version || "-"}</p>
                  <p className="status-line">Chapters: {diffPayload.source?.chapter_count || 0}</p>
                </div>
                <div className="semantic-diff-pane">
                  <h5>Target</h5>
                  <p className="status-line">#{diffPayload.target?.entry_id} {diffPayload.target?.title}</p>
                  <p className="status-line">Version: {diffPayload.target?.scaffold_version || "-"}</p>
                  <p className="status-line">Chapters: {diffPayload.target?.chapter_count || 0}</p>
                </div>
              </div>
              <div className="semantic-diff-grid">
                <div>
                  <h5>Metadata Changes</h5>
                  <ul className="semantic-inline-list">
                    {(diffPayload.diff.semantic_metadata_changes || []).length ? (
                      (diffPayload.diff.semantic_metadata_changes || []).map((change) => (
                        <li key={change.key}>{change.key}: {change.source || "-"} {"->"} {change.target || "-"}</li>
                      ))
                    ) : (
                      <li>No semantic metadata changes.</li>
                    )}
                  </ul>
                </div>
                <div>
                  <h5>Chapter Structure</h5>
                  <ul className="semantic-inline-list">
                    <li>Delta: {diffPayload.diff.chapter_structure_changes?.chapter_count_delta || 0}</li>
                    <li>Added: {(diffPayload.diff.chapter_structure_changes?.added_titles || []).join(" | ") || "none"}</li>
                    <li>Removed: {(diffPayload.diff.chapter_structure_changes?.removed_titles || []).join(" | ") || "none"}</li>
                  </ul>
                </div>
                <div>
                  <h5>DCHD Shifts</h5>
                  <ul className="semantic-inline-list">
                    <li>Added: {(diffPayload.diff.dchd_atom_shifts?.added || []).join(" | ") || "none"}</li>
                    <li>Removed: {(diffPayload.diff.dchd_atom_shifts?.removed || []).join(" | ") || "none"}</li>
                    <li>Stable: {(diffPayload.diff.dchd_atom_shifts?.unchanged || []).join(" | ") || "none"}</li>
                  </ul>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>

      <div className="semantic-ops-card semantic-heatmap-card">
        <h4>Semantic Heatmap Panel</h4>
        <div className="semantic-table-controls">
          <p className="status-line">Universe entries: {heatmapRows.length}</p>
          <p className="status-line">
            Focus: {selectedHeatmapKey ? selectedHeatmapKey.replace("::", " x ") : "none"}
          </p>
          <button type="button" onClick={runHeatmap} disabled={isHeatmapLoading}>
            {isHeatmapLoading ? "Refreshing..." : "Refresh Heatmap"}
          </button>
        </div>
        <div className="semantic-heatmap-grid">
          {heatmapCells.map((cell) => {
            const intensity = Math.min(1, Number(cell.density || 0) / heatmapMaxDensity);
            const background = `linear-gradient(135deg, rgba(20,111,75,${0.08 + intensity * 0.32}), rgba(30,136,229,${0.06 + intensity * 0.24}))`;
            return (
              <article
                key={cell.key}
                className={`semantic-heatmap-cell ${selectedHeatmapKey === cell.key ? "is-selected" : ""}`}
              >
                <button
                  type="button"
                  className="semantic-heatmap-cell-button"
                  style={{ background }}
                  onClick={() => applyHeatmapCellContext(cell)}
                >
                  <header>
                    <strong>{cell.mlas}</strong>
                    <span>{cell.phase}</span>
                  </header>
                  <ul className="semantic-inline-list">
                    <li>Density: {cell.density}</li>
                    <li>Semantic Drift: {cell.semanticDrift}</li>
                    <li>Hotspot Score: {cell.hotspot}</li>
                    <li>Version Range: {cell.versionRange}</li>
                    <li>DCHD Avg: {cell.avgDchd}</li>
                  </ul>
                </button>
              </article>
            );
          })}
        </div>
        <div className="semantic-transition-strip">
          <h5>Transitional Delta Strip (present-past {"->"} present-future)</h5>
          <div className="semantic-transition-grid">
            {transitionalDeltaRows.map((row) => (
              <article key={row.key} className="semantic-transition-row">
                <header>
                  <strong>{row.mlas}</strong>
                  <span>{row.trend}</span>
                </header>
                <ul className="semantic-inline-list">
                  <li>Density Delta: {formatSigned(row.deltaDensity)}</li>
                  <li>Drift Delta: {formatSigned(row.deltaDrift)}</li>
                  <li>Hotspot Delta: {formatSigned(row.deltaHotspot)}</li>
                  <li>DCHD Delta: {formatSigned(row.deltaDchd)}</li>
                  <li>Version Spread Delta: {formatSigned(row.versionSpreadDelta)}</li>
                </ul>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
