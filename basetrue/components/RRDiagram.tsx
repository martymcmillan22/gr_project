import { getTransitionMode } from "../logic/geometryMode";
import { RR_LOGIC_MODES, RR_QUADRANTS, RR_SUBNODE_MEANINGS, RR_SUBNODES, getRrDiagramMode } from "../logic/rrRouter";
import { emitDeterministicTelemetry } from "../../frontend_homepage/src/ui/deterministicTelemetry";
import type { RRLogicMode, RRQuadrant, RRSubnode, TemporalGroup, Tier } from "../types";

const LOGIC_MODE_COLORS: Record<RRLogicMode, string> = {
  hierarchical: "#d14343",
  network: "#2a4ecb",
  object: "#d4b117",
  relational: "#2f9b4b",
};

const TEMPORAL_OVERLAY_COLORS: Record<TemporalGroup, string> = {
  past: "#d14343",
  present_past: "#2a4ecb",
  present_future: "#d4b117",
  future: "#2f9b4b",
};

interface RRDiagramProps {
  isLargeScreen: boolean;
  tier: Tier;
  temporalGroup: TemporalGroup;
  selectedQuadrant?: RRQuadrant;
  selectedSubnode?: RRSubnode;
  selectedLogicMode?: RRLogicMode;
  onSelectQuadrant?: (quadrant: RRQuadrant) => void;
  onSelectSubnode?: (subnode: RRSubnode) => void;
  onSelectLogicMode?: (logicMode: RRLogicMode) => void;
  routingEnabled?: boolean;
  interactive?: boolean;
}

export default function RRDiagram({
  isLargeScreen,
  tier,
  temporalGroup,
  selectedQuadrant,
  selectedSubnode,
  selectedLogicMode,
  onSelectQuadrant,
  onSelectSubnode,
  onSelectLogicMode,
  routingEnabled = false,
  interactive = true,
}: RRDiagramProps) {
  const emitRrTelemetry = (eventName: string, payload: Record<string, unknown> = {}) => {
    emitDeterministicTelemetry({
      eventName,
      tier,
      surface: "pipeline",
      payload,
    });
  };

  const mode = getRrDiagramMode(tier);
  const transition = getTransitionMode(isLargeScreen);

  return (
    <section
      className="rr-diagram"
      data-shape="circle"
      data-mode={mode}
      data-transition={transition}
      style={{
        border: `2px solid ${TEMPORAL_OVERLAY_COLORS[temporalGroup]}`,
        borderRadius: "16px",
        padding: "12px",
      }}
    >
      <h3>Repository Relay</h3>
      <p>Shape: circle</p>
      <p>Mode: {mode}</p>
      <p>Temporal overlay: {temporalGroup}</p>
      <p>{routingEnabled ? "Routing: active" : "Routing: preview only"}</p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", margin: "8px 0" }}>
        {RR_QUADRANTS.map((quadrant) => {
          const active = selectedQuadrant === quadrant;
          return (
            <button
              key={quadrant}
              type="button"
              onClick={() => {
                if (interactive) {
                  onSelectQuadrant?.(quadrant);
                  emitRrTelemetry("rr.quadrant.selected", {
                    quadrant,
                    temporalGroup,
                  });
                }
              }}
              disabled={!interactive}
              style={{
                padding: "10px",
                borderRadius: "10px",
                border: active ? "2px solid #3a66ff" : "1px solid #8ca0ba",
                boxShadow: active ? "0 0 14px rgba(58,102,255,0.45)" : "none",
                background: active ? "rgba(58,102,255,0.08)" : "transparent",
                textTransform: "capitalize",
                cursor: interactive ? "pointer" : "default",
              }}
            >
              {quadrant}
            </button>
          );
        })}
      </div>

      <div style={{ margin: "8px 0" }}>
        <strong>Subnodes ({selectedQuadrant || "select a quadrant"}):</strong>
        <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
          {RR_SUBNODES.map((subnode) => {
            const active = selectedSubnode === subnode;
            return (
              <button
                key={subnode}
                type="button"
                title={RR_SUBNODE_MEANINGS[subnode]}
                onClick={() => {
                  if (interactive) {
                    onSelectSubnode?.(subnode);
                    emitRrTelemetry("rr.subnode.selected", {
                      subnode,
                      temporalGroup,
                    });
                  }
                }}
                disabled={!interactive}
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "999px",
                  border: active ? "2px solid #3a66ff" : "1px solid #8ca0ba",
                  boxShadow: active ? "0 0 12px rgba(58,102,255,0.45)" : "none",
                  background: active ? "rgba(58,102,255,0.12)" : "transparent",
                  cursor: interactive ? "pointer" : "default",
                  fontWeight: 700,
                }}
              >
                {subnode}
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ margin: "8px 0" }}>
        <strong>Logic modes:</strong>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: "8px", marginTop: "6px" }}>
          {RR_LOGIC_MODES.map((logicMode) => {
            const active = selectedLogicMode === logicMode;
            return (
              <button
                key={logicMode}
                type="button"
                onClick={() => {
                  if (interactive) {
                    onSelectLogicMode?.(logicMode);
                    emitRrTelemetry("rr.logic_mode.selected", {
                      logicMode,
                      temporalGroup,
                    });
                  }
                }}
                disabled={!interactive}
                style={{
                  padding: "8px",
                  borderRadius: "10px",
                  border: active ? `2px solid ${LOGIC_MODE_COLORS[logicMode]}` : "1px solid #8ca0ba",
                  background: active ? `${LOGIC_MODE_COLORS[logicMode]}22` : "transparent",
                  color: active ? "#102235" : "inherit",
                  cursor: interactive ? "pointer" : "default",
                  textTransform: "capitalize",
                }}
              >
                {logicMode}
              </button>
            );
          })}
        </div>
      </div>

      <p>
        Selection: {selectedQuadrant || "-"}.{selectedSubnode || "-"}.{selectedLogicMode || "-"}.{temporalGroup}
      </p>
    </section>
  );
}
