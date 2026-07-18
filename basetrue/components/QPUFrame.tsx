import { useEffect, useMemo, useState } from "react";
import ArtifactTagDisplay from "./ArtifactTagDisplay";
import { getTierConfig } from "../logic/tierLogic";
import { buildQpuPlan } from "../logic/qpuEngine";
import { emitDeterministicTelemetry } from "../../frontend_homepage/src/ui/deterministicTelemetry";
import type { GeometryMode, ProjectRecord, SeedRecord, TemporalGroup, Tier, WorkspaceMode } from "../types";

interface QPUFrameProps {
  compartmentIndex: number;
  tier: Tier;
  temporalGroup: TemporalGroup;
  seed?: SeedRecord | null;
  project?: ProjectRecord | null;
  isLargeScreen?: boolean;
  scaledOnly?: boolean;
  workspaceMode?: WorkspaceMode;
}

const TEMPORAL_GEOMETRY_MAP: Record<Exclude<TemporalGroup, "future">, GeometryMode> = {
  past: "flat",
  present_past: "layered",
  present_future: "architectural",
};

export default function QPUFrame({
  compartmentIndex,
  tier,
  temporalGroup,
  seed,
  project,
  isLargeScreen,
  scaledOnly = false,
  workspaceMode = "default",
}: QPUFrameProps) {
  const [screenLarge, setScreenLarge] = useState(Boolean(isLargeScreen));
  const [futureCycleIndex, setFutureCycleIndex] = useState(0);

  useEffect(() => {
    if (typeof isLargeScreen === "boolean") {
      setScreenLarge(isLargeScreen);
      return;
    }
    if (typeof window === "undefined") {
      return;
    }

    const media = window.matchMedia("(min-width: 1024px)");
    setScreenLarge(media.matches);

    const onChange = (event: MediaQueryListEvent) => setScreenLarge(event.matches);
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [isLargeScreen]);

  useEffect(() => {
    if (temporalGroup !== "future" || !screenLarge) {
      setFutureCycleIndex(0);
      return;
    }

    const timer = window.setInterval(() => {
      setFutureCycleIndex((current) => (current + 1) % 3);
    }, 1800);

    return () => window.clearInterval(timer);
  }, [screenLarge, temporalGroup]);

  const transition = screenLarge ? "animated" : "snap";
  const tierCfg = getTierConfig(tier);
  const maxCompartment = tierCfg.qpu_max_compartment ?? 0;
  const qpuPlan =
    project?.qpu_plan ||
    buildQpuPlan({
      tier,
      compartmentIndex,
      temporalGroup,
      rrSelection: seed?.rr_selection,
      workspaceMode: scaledOnly ? "studio" : workspaceMode,
    });
  const temporalGeometryMode = useMemo<GeometryMode>(() => {
    if (temporalGroup !== "future") {
      return TEMPORAL_GEOMETRY_MAP[temporalGroup];
    }

    if (!screenLarge) {
      return "architectural";
    }

    const cycle: GeometryMode[] = ["flat", "layered", "architectural"];
    return cycle[futureCycleIndex] || "architectural";
  }, [futureCycleIndex, screenLarge, temporalGroup]);

  const hybridFutureLabel = temporalGroup === "future" ? "hybrid_cycle" : "single_mode";
  const isWithinTierLimit = maxCompartment > 0 && compartmentIndex <= maxCompartment;
  const displayCount = project ? qpuPlan.adjusted_count : isWithinTierLimit ? qpuPlan.adjusted_count : 0;
  const orchestrationLabel = scaledOnly ? "scaled" : qpuPlan.orchestration_mode;

  useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "qpu.frame.loaded",
      tier,
      surface: "qpu-frame",
      payload: {
        temporalGroup,
        workspaceMode,
        planId: qpuPlan.qpu_plan_id,
      },
    });
    // Deterministic mount telemetry is intentionally emitted once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "qpu.frame.updated",
      tier,
      surface: "qpu-frame",
      payload: {
        planId: qpuPlan.qpu_plan_id,
        geometry: temporalGeometryMode,
        qpuCount: displayCount,
      },
    });
  }, [displayCount, qpuPlan.qpu_plan_id, temporalGeometryMode, tier]);

  return (
    <section
      className="qpu-frame"
      data-shape="square"
      data-mode={temporalGeometryMode}
      data-transition={transition}
      data-temporal={temporalGroup}
      data-hybrid={hybridFutureLabel}
    >
      <h3>QPU Frame</h3>
      <p>Shape: square</p>
      <p>QPU count: {displayCount}</p>
      <p>Orchestration: {orchestrationLabel}</p>
      <p>QPU plan id: {qpuPlan.qpu_plan_id}</p>
      <p>Geometry emphasis: {temporalGeometryMode}</p>
      <p>Transition behavior: {transition}</p>
      <p>Plan geometry: {qpuPlan.geometry_mode}</p>
      <p>Slices: {qpuPlan.slices.map((slice) => `${slice.slice}:${slice.count}`).join(" | ")}</p>
      <ArtifactTagDisplay label="QPU Surface Tags" tags={project?.artifact_tags} />
      {qpuPlan.notes.length > 0 ? <p>Plan notes: {qpuPlan.notes.join(" ")}</p> : null}
    </section>
  );
}
