// @vitest-environment jsdom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import SquareRootTimelineGrid from "./SquareRootTimelineGrid";
import { fetchProjectMiddleLayerCalculusTimeline } from "../api/homepageApi";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

let runtimeResponse = null;

const runtimeMock = vi.fn((payload = {}) => Promise.resolve(runtimeResponse || buildRuntimePayload({ selectedSlot: Number(payload?.selected_slot || 1) })));

vi.mock("../api/homepageApi", () => ({
  fetchProjectMiddleLayerCalculusTimeline: (...args) => runtimeMock(...args),
}));

function buildRuntimePayload({ lockedFrom = 5, selectedSlot = 1 } = {}) {
  const slots = [];
  for (let index = 1; index <= 16; index += 1) {
    const temporalAlignment = ["past", "present-past", "present-future", "future"][(index - 1) % 4];
    const calculusOperation = ["Integral", "Continuity", "Limit", "Derivative"][(index - 1) % 4];
    const locked = index >= lockedFrom;
    slots.push({
      slot_index: index,
      temporal_alignment: temporalAlignment,
      calculus_operation: calculusOperation,
      gate: {
        locked,
        reason: locked ? "locked" : "unlocked",
      },
      completed: false,
      state: {
        drift_score: 0.2,
        stability_score: 0.8,
        alignment_score: 0.8,
        semantic_tags: ["temporal:past"],
        micro_signals: [],
      },
      industry_metadata: {
        sector_name: "Primary (Create Phase)",
        group_name: index === 2 ? "Language" : "Math",
        industry: index === 2 ? "Software" : "Capital Markets",
        sub_industry:
          index === 2
            ? "Enterprise Operating System Architecture"
            : "Algorithmic Trading Systems & Quantitative Analysis",
      },
      event: {
        event_type: "middle_layer.timeline.slot_state",
        slot_index: index,
      },
    });
  }

  return {
    mode: "calculus_temporal_timeline_runtime",
    timeline: {
      slot_count: 16,
      phase_count: 4,
      temporal_alignments: ["past", "present-past", "present-future", "future"],
      calculus_operations: ["Integral", "Continuity", "Limit", "Derivative"],
    },
    deterministic_progression: {
      completed_slots: [],
      phase_gates: [
        { phase: "Ideas", locked: false },
        { phase: "Seeds", locked: true },
        { phase: "Projects", locked: true },
        { phase: "MVP", locked: true },
      ],
    },
    selected_slot: selectedSlot,
    selected_slot_state: slots[selectedSlot - 1],
    slots,
    events: [],
  };
}

async function flushEffects() {
  await act(async () => {
    await Promise.resolve();
  });
}

describe("SquareRootTimelineGrid runtime integration", () => {
  let container;
  let root;

  afterEach(async () => {
    if (root) {
      await act(async () => {
        root.unmount();
      });
    }
    if (container && container.parentNode) {
      container.parentNode.removeChild(container);
    }
    container = null;
    root = null;
    runtimeResponse = null;
    runtimeMock.mockClear();
    vi.clearAllMocks();
  });

  it("renders 16 slots and enforces deterministic lock states", async () => {
    runtimeResponse = buildRuntimePayload({ lockedFrom: 5, selectedSlot: 1 });
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root.render(<SquareRootTimelineGrid initialLatticeIndex={1} onCellSelect={() => {}} />);
    });
    await flushEffects();

    const allCells = container.querySelectorAll(".srl-cell");
    expect(allCells.length).toBe(16);

    const lockedCells = container.querySelectorAll(".srl-cell.is-locked");
    expect(lockedCells.length).toBe(12);

    const unlockedCell = container.querySelector(".srl-cell:not(.is-locked)");
    expect(unlockedCell).not.toBeNull();
    expect(unlockedCell.disabled).toBe(false);
  });

  it("emits middle-layer slot state events with calculus, temporal, and industry metadata", async () => {
    runtimeResponse = buildRuntimePayload({ lockedFrom: 5, selectedSlot: 1 });
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    const events = [];
    const onSlotEvent = (event) => {
      events.push(event.detail);
    };
    window.addEventListener("grassroots:middle-layer-slot-state-change", onSlotEvent);

    const onCellSelect = vi.fn();
    try {
      await act(async () => {
        root.render(<SquareRootTimelineGrid initialLatticeIndex={1} onCellSelect={onCellSelect} />);
      });
      await flushEffects();

      expect(onCellSelect).toHaveBeenCalled();
      const lastSelect = onCellSelect.mock.calls[onCellSelect.mock.calls.length - 1]?.[0];
      expect(lastSelect?.latticeIndex).toBe(1);
      expect(events.length).toBeGreaterThan(0);

      const lastEvent = events[events.length - 1];
      expect(lastEvent.event_version).toBe("v1");
      expect(lastEvent.source).toBe("frontend.timeline.grid");
      expect(lastEvent.event_type).toBe("slot_state_change");
      expect(lastEvent.slot_index).toBe(1);
      expect(lastEvent.temporal_alignment).toBe("past");
      expect(lastEvent.calculus_operation).toBe("Integral");
      expect(lastEvent.industry_metadata.group_name).toBe("Math");
      expect(lastEvent.industry_metadata.industry).toBe("Capital Markets");
      expect(lastEvent.semantic_state).toBeTruthy();
    } finally {
      window.removeEventListener("grassroots:middle-layer-slot-state-change", onSlotEvent);
    }
  });

  it("emits deterministic slot completion event once under rapid repeated clicks", async () => {
    runtimeResponse = buildRuntimePayload({ lockedFrom: 5, selectedSlot: 1 });
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    const events = [];
    const onSlotEvent = (event) => {
      events.push(event.detail);
    };
    window.addEventListener("grassroots:middle-layer-slot-state-change", onSlotEvent);

    try {
      await act(async () => {
        root.render(<SquareRootTimelineGrid initialLatticeIndex={1} onCellSelect={() => {}} />);
      });
      await flushEffects();

      const completeButton = Array.from(container.querySelectorAll("button")).find((button) =>
        String(button.textContent || "").includes("Mark Slot Complete"),
      );
      expect(completeButton).not.toBeNull();

      await act(async () => {
        completeButton.click();
        completeButton.click();
        completeButton.click();
      });
      await flushEffects();

      const completionEvents = events.filter((item) => item?.event_type === "slot_completion");
      expect(completionEvents.length).toBe(1);
      expect(completionEvents[0].slot_index).toBe(1);
      expect(completionEvents[0].slot_completed).toBe(true);
      expect(completionEvents[0].completed_slots).toEqual([1]);
      expect(runtimeMock).toHaveBeenCalled();
    } finally {
      window.removeEventListener("grassroots:middle-layer-slot-state-change", onSlotEvent);
    }
  });
});
