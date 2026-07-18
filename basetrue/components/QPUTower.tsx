import { useEffect, useMemo, useRef } from "react";
import ArtifactTagDisplay from "./ArtifactTagDisplay";
import { buildQpuFloorPlans } from "../logic/qpuEngine";
import { getQPUCount } from "../logic/qpuGrowth";
import { STUDIO_ENTERPRISE_TOWER } from "../logic/baseTrueConstants";
import { emitDeterministicTelemetry } from "../../frontend_homepage/src/ui/deterministicTelemetry";
import type { ProjectRecord, RRQuadrant, TemporalGroup, WorkspaceMode } from "../types";

const TEMPORAL_RING: Record<TemporalGroup, string> = {
  past: "#8fa1b5",
  present_past: "#3f78b0",
  present_future: "#d5972d",
  future: "#2f9b4b",
};

const QUADRANT_COLORS: Record<RRQuadrant, string> = {
  language: "#d14343",
  arts: "#2a4ecb",
  math: "#d4b117",
  science: "#2f9b4b",
};

const LOGIC_HALO: Record<string, string> = {
  hierarchical: "rgba(209,67,67,0.4)",
  network: "rgba(42,78,203,0.4)",
  object: "rgba(212,177,23,0.4)",
  relational: "rgba(47,155,75,0.4)",
};

const TEMPORAL_ANIMATION: Record<TemporalGroup, string> = {
  past: "bt-floor-fade 900ms ease-out",
  present_past: "bt-floor-slide 850ms ease-out",
  present_future: "bt-floor-rise 850ms ease-out",
  future: "bt-floor-pulse-rise 1400ms ease-in-out infinite",
};

interface QPUTowerProps {
  compartmentIndex: number;
  project?: ProjectRecord | null;
  selectedFloor?: number;
  onFloorSelect?: (floor: number) => void;
  onFloorHover?: (floor: number | null) => void;
  interactive?: boolean;
  workspaceMode?: WorkspaceMode;
}

export default function QPUTower({
  compartmentIndex,
  project,
  selectedFloor,
  onFloorSelect,
  onFloorHover,
  interactive = true,
  workspaceMode = "default",
}: QPUTowerProps) {
  const qpuCount = project?.qpu_plan.adjusted_count ?? getQPUCount(compartmentIndex);
  const floors = project?.qpu_plan.tower_floors ?? 0;
  const interactiveTower = workspaceMode === "enterprise" ? true : interactive;
  const floorRefs = useRef<Record<number, HTMLButtonElement | null>>({});
  const floorPlans = useMemo(() => (project ? buildQpuFloorPlans(project.qpu_plan) : []), [project]);
  const temporalGroup = project?.qpu_plan.temporal_group;
  const rr = project?.qpu_plan.rr_influence;
  const hoverFloor = typeof selectedFloor === "number" ? selectedFloor : null;
  const hoverPlan = hoverFloor ? floorPlans.find((floor) => floor.floor === hoverFloor) : null;
  const floorsPerZone = STUDIO_ENTERPRISE_TOWER.floors_per_zone;

  useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "qpu.tower.loaded",
      tier: project?.tier || "enterprise",
      surface: "tower",
      payload: {
        workspaceMode,
        floors,
        qpuCount,
      },
    });
    // Deterministic mount telemetry is intentionally emitted once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "qpu.tower.floor.active",
      tier: project?.tier || "enterprise",
      surface: "tower",
      payload: {
        selectedFloor: typeof selectedFloor === "number" ? selectedFloor : 0,
      },
    });
  }, [project?.tier, selectedFloor]);

  const renderSemanticOverlay = (floor: number) => {
    const plan = floorPlans.find((item) => item.floor === floor);
    if (!plan) {
      return null;
    }

    const total = Math.max(1, plan.total_count);
    let offset = 0;
    const bands = plan.slices.map((slice) => {
      const width = (slice.count / total) * 100;
      const x = offset;
      offset += width;
      return {
        slice: slice.slice,
        x,
        width,
      };
    });

    return (
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        style={{ position: "absolute", inset: 0, opacity: 0.22, pointerEvents: "none", borderRadius: "10px" }}
        aria-hidden="true"
      >
        {bands.map((band) => (
          <rect key={`${floor}-${band.slice}`} x={band.x} y="0" width={Math.max(0, band.width)} height="100" fill={QUADRANT_COLORS[band.slice]} />
        ))}
      </svg>
    );
  };

  return (
    <section className="qpu-tower" data-shape="vertical_stack" data-workspace={workspaceMode}>
      <style>
        {`@keyframes bt-floor-fade { from { opacity: 0.35; filter: saturate(60%); } to { opacity: 1; filter: saturate(100%); } }
          @keyframes bt-floor-slide { from { transform: translateX(-10px); opacity: 0.45; } to { transform: translateX(0); opacity: 1; } }
          @keyframes bt-floor-rise { from { transform: translateY(10px); opacity: 0.4; } to { transform: translateY(0); opacity: 1; } }
          @keyframes bt-floor-pulse-rise { 0% { transform: translateY(8px) scale(0.98); opacity: 0.55; } 50% { transform: translateY(0) scale(1.01); opacity: 1; } 100% { transform: translateY(8px) scale(0.98); opacity: 0.55; } }`}
      </style>
      <h3>QPU Tower</h3>
      <div className="enterprise-tower-stats">
        <p>Shape: vertical stack</p>
        <p>QPU count: {qpuCount}</p>
        <p>Floors: {floors}</p>
      </div>
      {project?.qpu_plan ? <p>QPU plan id: {project.qpu_plan.qpu_plan_id}</p> : null}
      {workspaceMode === "enterprise" ? <p>Workspace mode: enterprise tower control</p> : null}
      {typeof selectedFloor === "number" ? <p>Selected floor: {selectedFloor}</p> : null}
      <ArtifactTagDisplay
        label="Tower Surface Tags"
        tags={project?.artifact_tags}
        workspaceMode={workspaceMode}
        semanticMix={project?.qpu_plan.slices.map((slice) => `${slice.slice}:${slice.count}`)}
      />
      {hoverPlan && rr ? (
        <div className="enterprise-floor-preview">
          <strong>Floor {hoverPlan.floor} Preview</strong>
          <p>Units: {hoverPlan.total_count}</p>
          <p>
            Semantic: {hoverPlan.slices.map((slice) => `${slice.slice}:${slice.count}`).join(" | ")}
          </p>
          <p>
            RR: {rr.quadrant}.{rr.subnode}.{rr.logic_mode} | Temporal: {rr.temporal_group}
          </p>
        </div>
      ) : null}
      {floors > 0 ? (
        <div className="tower-floor-selector" id="enterprise-tower">
          {Array.from({ length: floors }, (_, index) => {
            const floor = index + 1;
            const active = selectedFloor === floor;
            const zone = Math.max(1, Math.ceil(floor / floorsPerZone));
            const haloColor = LOGIC_HALO[rr?.logic_mode || "hierarchical"];
            const temporalColor = temporalGroup ? TEMPORAL_RING[temporalGroup] : "#6f8298";
            return (
              <button
                type="button"
                key={floor}
                className={`enterprise-floor-button${active ? " is-active" : ""}`}
                ref={(node) => {
                  floorRefs.current[floor] = node;
                }}
                onClick={() => {
                  if (interactiveTower) {
                    floorRefs.current[floor]?.scrollIntoView({ behavior: "smooth", block: "nearest" });
                    onFloorSelect?.(floor);
                    emitDeterministicTelemetry({
                      eventName: "qpu.tower.floor.click",
                      tier: project?.tier || "enterprise",
                      surface: "tower",
                      payload: {
                        floor,
                        zone,
                      },
                    });
                  }
                }}
                onMouseEnter={() => {
                  if (interactiveTower) {
                    onFloorHover?.(floor);
                  }
                }}
                onMouseLeave={() => {
                  if (interactiveTower) {
                    onFloorHover?.(null);
                  }
                }}
                aria-pressed={selectedFloor === floor}
                disabled={!interactiveTower}
                style={{
                  border: active ? `2px solid ${temporalColor}` : "1px solid #70859c",
                  boxShadow: active ? `0 0 16px ${haloColor}` : "none",
                  background: active ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.02)",
                  animation: temporalGroup ? TEMPORAL_ANIMATION[temporalGroup] : undefined,
                }}
              >
                {renderSemanticOverlay(floor)}
                <span className="enterprise-floor-label">Floor {floor}</span>
                <div className="enterprise-floor-badges">
                  <span className="enterprise-floor-id" style={{ borderColor: temporalColor }}>
                    #{String(floor).padStart(2, "0")}
                  </span>
                  <span className="enterprise-zone-id">Z{zone}</span>
                  {rr ? <span className="enterprise-rr-id">{rr.subnode}.{rr.logic_mode}</span> : null}
                </div>
              </button>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
