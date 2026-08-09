import { useEffect, useMemo, useRef, useState } from "react";

import { fetchProjectMiddleLayerCalculusTimeline } from "../api/homepageApi";
import { normalizeTimelineSlotEventEnvelope } from "./semanticOsHelpers";
import { getCellsByPhase, TIMELINE_PHASES } from "./squareRootTimelineModel";

function buildSlotEventDetail(cell, eventType) {
  return normalizeTimelineSlotEventEnvelope({
    event_type: eventType,
    event_version: "v1",
    source: "frontend.timeline.grid",
    slot_index: cell?.latticeIndex || 0,
    phase: cell?.timelineLabel || "",
    temporal_alignment: String(cell?.temporalAlignment || "").toLowerCase(),
    calculus_operation: cell?.calculusOperation || "",
    gate_locked: Boolean(cell?.isLocked),
    slot_completed: Boolean(cell?.isCompleted),
    industry_metadata: cell?.industryMetadata || {},
    semantic_state: cell?.semanticState || {},
  });
}

export default function SquareRootTimelineGrid({ onCellSelect, initialLatticeIndex = 1 }) {
  const [activeLatticeIndex, setActiveLatticeIndex] = useState(Number(initialLatticeIndex || 1));
  const [completedSlots, setCompletedSlots] = useState([]);
  const [runtimePayload, setRuntimePayload] = useState(null);
  const [runtimeError, setRuntimeError] = useState("");
  const completedSlotsRef = useRef([]);

  useEffect(() => {
    completedSlotsRef.current = completedSlots;
  }, [completedSlots]);

  useEffect(() => {
    const normalized = Number(initialLatticeIndex || 1);
    if (Number.isFinite(normalized) && normalized !== activeLatticeIndex) {
      setActiveLatticeIndex(normalized);
    }
  }, [activeLatticeIndex, initialLatticeIndex]);

  useEffect(() => {
    let active = true;
    fetchProjectMiddleLayerCalculusTimeline({
      selected_slot: activeLatticeIndex,
      completed_slots: completedSlots,
    })
      .then((payload) => {
        if (!active) {
          return;
        }
        setRuntimePayload(payload || null);
        setRuntimeError("");
      })
      .catch((error) => {
        if (!active) {
          return;
        }
        setRuntimePayload(null);
        setRuntimeError(error?.message || "Unable to load timeline runtime");
      });

    return () => {
      active = false;
    };
  }, [activeLatticeIndex, completedSlots]);

  const runtimeByIndex = useMemo(() => {
    const map = new Map();
    const slots = runtimePayload?.slots || [];
    for (const slot of slots) {
      const index = Number(slot?.slot_index || 0);
      if (index > 0) {
        map.set(index, slot);
      }
    }
    return map;
  }, [runtimePayload]);

  const phaseRows = useMemo(() => {
    return TIMELINE_PHASES.map((phase, index) => ({
      ...phase,
      cells: getCellsByPhase(index + 1),
    }));
  }, []);

  const activeCell = useMemo(() => {
    for (const phase of phaseRows) {
      const match = phase.cells.find((cell) => cell.latticeIndex === activeLatticeIndex);
      if (match) {
        return match;
      }
    }
    return phaseRows[0]?.cells?.[0] || null;
  }, [activeLatticeIndex, phaseRows]);

  const enrichedActiveCell = useMemo(() => {
    if (!activeCell) {
      return null;
    }
    const runtimeSlot = runtimeByIndex.get(Number(activeCell.latticeIndex || 0));
    return {
      ...activeCell,
      runtimeSlot: runtimeSlot || null,
      isLocked: Boolean(runtimeSlot?.gate?.locked),
      isCompleted: Boolean(runtimeSlot?.completed),
      temporalAlignment: runtimeSlot?.temporal_alignment || activeCell.temporalAlignment,
      calculusOperation: runtimeSlot?.calculus_operation || activeCell.calculusOperation,
      industryMetadata: runtimeSlot?.industry_metadata || null,
      semanticState: runtimeSlot?.state || null,
    };
  }, [activeCell, runtimeByIndex]);

  useEffect(() => {
    if (!enrichedActiveCell) {
      return;
    }
    onCellSelect?.(enrichedActiveCell);
    window.dispatchEvent(
      new CustomEvent("grassroots:middle-layer-slot-state-change", {
        detail: buildSlotEventDetail(enrichedActiveCell, "slot_state_change"),
      }),
    );
  }, [enrichedActiveCell, onCellSelect]);

  const markActiveSlotCompleted = () => {
    if (!enrichedActiveCell || enrichedActiveCell.isLocked) {
      return;
    }
    const slotIndex = Number(enrichedActiveCell.latticeIndex || 0);
    if (!slotIndex) {
      return;
    }
    if (completedSlotsRef.current.includes(slotIndex)) {
      return;
    }
    const nextCompletedSlots = [...completedSlotsRef.current, slotIndex].sort((left, right) => left - right);
    completedSlotsRef.current = nextCompletedSlots;
    setCompletedSlots(nextCompletedSlots);
    window.dispatchEvent(
      new CustomEvent("grassroots:middle-layer-slot-state-change", {
        detail: {
          ...buildSlotEventDetail(
            {
              ...enrichedActiveCell,
              isCompleted: true,
            },
            "slot_completion",
          ),
          completed_slots: nextCompletedSlots,
        },
      }),
    );
  };

  return (
    <section className="panel srl-timeline-panel" aria-label="Square Root Lattice timeline grid">
      <p className="eyebrow">Phase 6A</p>
      <h2>16-Slot Calculus Temporal Timeline Grid</h2>
      <p className="status-line">
        Deterministic 4x4 map for Ideas, Seeds, Projects, and MVP aligned to calculus operations, temporal alignment, and industry context.
      </p>
      {runtimeError ? <p className="status-line">{runtimeError}</p> : null}

      <div className="srl-timeline-grid" role="grid" aria-label="Calculus temporal 16-slot timeline">
        {phaseRows.map((phase) => (
          <div className="srl-row" role="row" key={phase.id}>
            <div className="srl-row-label">
              <strong>{phase.timelineLabel}</strong>
              <span>{phase.cpwState}</span>
            </div>
            <div className="srl-row-cells">
              {phase.cells.map((cell) => {
                const slotRuntime = runtimeByIndex.get(Number(cell.latticeIndex || 0));
                const isActive = cell.latticeIndex === enrichedActiveCell?.latticeIndex;
                const isLocked = Boolean(slotRuntime?.gate?.locked);
                const isCompleted = Boolean(slotRuntime?.completed);
                return (
                  <button
                    key={cell.latticeIndex}
                    type="button"
                    role="gridcell"
                    className={`srl-cell${isActive ? " is-active" : ""}${isLocked ? " is-locked" : ""}${isCompleted ? " is-complete" : ""}`}
                    onClick={() => {
                      if (isLocked) {
                        return;
                      }
                      setActiveLatticeIndex(cell.latticeIndex);
                    }}
                    style={{ "--srl-color": cell.colorHex }}
                    aria-pressed={isActive}
                    title={`${cell.presetId}${isLocked ? " (locked)" : ""}`}
                    disabled={isLocked}
                  >
                    <span className="srl-cell-index">{cell.latticeIndex}</span>
                    <span className="srl-cell-subject">{cell.mlasSubject}</span>
                    <span className="srl-cell-color">{slotRuntime?.calculus_operation || cell.calculusOperation}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {enrichedActiveCell ? (
        <div className="srl-cell-detail" aria-live="polite">
          <div>
            <p className="eyebrow">Selected Compartment</p>
            <h3>
              {enrichedActiveCell.timelineLabel} {enrichedActiveCell.colSlot} - Slot {enrichedActiveCell.latticeIndex}
            </h3>
          </div>
          <ul>
            <li>Phase State: {enrichedActiveCell.cpwState}</li>
            <li>Preset: {enrichedActiveCell.presetId}</li>
            <li>MLAS Subject: {enrichedActiveCell.mlasSubject}</li>
            <li>Semantic Intent: {enrichedActiveCell.semanticIntentId}</li>
            <li>Temporal Alignment: {enrichedActiveCell.temporalAlignment || "n/a"}</li>
            <li>Calculus Operation: {enrichedActiveCell.calculusOperation || "n/a"}</li>
            <li>Slot Locked: {enrichedActiveCell.isLocked ? "yes" : "no"}</li>
            <li>Completed: {enrichedActiveCell.isCompleted ? "yes" : "no"}</li>
            <li>Drift Score: {enrichedActiveCell.semanticState?.drift_score ?? "n/a"}</li>
            <li>Stability Score: {enrichedActiveCell.semanticState?.stability_score ?? "n/a"}</li>
            <li>Alignment Score: {enrichedActiveCell.semanticState?.alignment_score ?? "n/a"}</li>
            <li>Industry Group: {enrichedActiveCell.industryMetadata?.group_name || "n/a"}</li>
            <li>Industry: {enrichedActiveCell.industryMetadata?.industry || "n/a"}</li>
            <li>Sub-Industry: {enrichedActiveCell.industryMetadata?.sub_industry || "n/a"}</li>
            <li>Sector: {enrichedActiveCell.industryMetadata?.sector_name || "n/a"}</li>
            <li>SVEM Link: {enrichedActiveCell.links?.svemId}</li>
            <li>CCCP Link: {enrichedActiveCell.links?.cccpId}</li>
            <li>DCHD Link: {enrichedActiveCell.links?.dchdId}</li>
          </ul>
          <div className="action-grid">
            <button type="button" onClick={markActiveSlotCompleted} disabled={enrichedActiveCell.isLocked || enrichedActiveCell.isCompleted}>
              {enrichedActiveCell.isCompleted ? "Completed" : "Mark Slot Complete"}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}