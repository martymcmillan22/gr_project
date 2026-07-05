import { useEffect, useMemo, useState } from "react";

import { getCellsByPhase, TIMELINE_PHASES } from "./squareRootTimelineModel";

export default function SquareRootTimelineGrid({ onCellSelect, initialLatticeIndex = 1 }) {
  const [activeLatticeIndex, setActiveLatticeIndex] = useState(Number(initialLatticeIndex || 1));

  useEffect(() => {
    const normalized = Number(initialLatticeIndex || 1);
    if (Number.isFinite(normalized) && normalized !== activeLatticeIndex) {
      setActiveLatticeIndex(normalized);
    }
  }, [activeLatticeIndex, initialLatticeIndex]);

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

  useEffect(() => {
    if (!activeCell) {
      return;
    }
    onCellSelect?.(activeCell);
  }, [activeCell, onCellSelect]);

  return (
    <section className="panel srl-timeline-panel" aria-label="Square Root Lattice timeline grid">
      <p className="eyebrow">Phase 6A</p>
      <h2>12-Compartment Timeline Grid</h2>
      <p className="status-line">
        Deterministic 3x4 map for Beginning, Middle, End aligned with the Square Root Lattice and MLAS color routing.
      </p>

      <div className="srl-timeline-grid" role="grid" aria-label="Square Root Lattice 12-cell timeline">
        {phaseRows.map((phase) => (
          <div className="srl-row" role="row" key={phase.id}>
            <div className="srl-row-label">
              <strong>{phase.timelineLabel}</strong>
              <span>{phase.cpwState}</span>
            </div>
            <div className="srl-row-cells">
              {phase.cells.map((cell) => {
                const isActive = cell.latticeIndex === activeCell?.latticeIndex;
                return (
                  <button
                    key={cell.latticeIndex}
                    type="button"
                    role="gridcell"
                    className={`srl-cell${isActive ? " is-active" : ""}`}
                    onClick={() => setActiveLatticeIndex(cell.latticeIndex)}
                    style={{ "--srl-color": cell.colorHex }}
                    aria-pressed={isActive}
                    title={`${cell.presetId}`}
                  >
                    <span className="srl-cell-index">{cell.latticeIndex}</span>
                    <span className="srl-cell-subject">{cell.mlasSubject}</span>
                    <span className="srl-cell-color">{cell.mlasColorToken}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {activeCell ? (
        <div className="srl-cell-detail" aria-live="polite">
          <div>
            <p className="eyebrow">Selected Compartment</p>
            <h3>
              {activeCell.timelineLabel} {activeCell.colSlot} - Lattice {activeCell.latticeIndex}
            </h3>
          </div>
          <ul>
            <li>Phase State: {activeCell.cpwState}</li>
            <li>Preset: {activeCell.presetId}</li>
            <li>MLAS Subject: {activeCell.mlasSubject}</li>
            <li>Semantic Intent: {activeCell.semanticIntentId}</li>
            <li>Color Token: {activeCell.mlasColorToken}</li>
            <li>SVEM Link: {activeCell.links?.svemId}</li>
            <li>CCCP Link: {activeCell.links?.cccpId}</li>
            <li>DCHD Link: {activeCell.links?.dchdId}</li>
          </ul>
        </div>
      ) : null}
    </section>
  );
}