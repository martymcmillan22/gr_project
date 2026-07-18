import { useMemo, useState } from "react";
import ArtifactTagDisplay from "./ArtifactTagDisplay";
import { buildArtifactTags } from "../logic/artifactTagging";
import { buildQpuFloorPlans } from "../logic/qpuEngine";
import { buildSeedRoute } from "../logic/rrRouter";
import type { ProjectRecord, QpuPlan, RRQuadrant, WorkRecord } from "../types";

type ExecutionState = "planned" | "in_progress" | "completed";

interface TimelineRow {
  id: string;
  floor: number;
  step: string;
  quadrants: RRQuadrant[];
}

interface TowerExecutionTimelineProps {
  activeProject?: ProjectRecord | null;
  qpuPlan?: QpuPlan | null;
  workArtifacts?: WorkRecord[];
  activeFloor?: number;
  executionStateMap?: Record<string, ExecutionState>;
  onAdvanceState?: (rowId: string, current: ExecutionState) => void;
}

function resolveArtifactCompletion(artifacts: WorkRecord[] | undefined, floor: number, step: string): boolean {
  if (!artifacts?.length) {
    return false;
  }
  return artifacts.some((artifact) => artifact.floor === floor && artifact.task === step);
}

export default function TowerExecutionTimeline({
  activeProject,
  qpuPlan,
  workArtifacts,
  activeFloor,
  executionStateMap,
  onAdvanceState,
}: TowerExecutionTimelineProps) {
  const [floorFilter, setFloorFilter] = useState<string>("all");
  const [temporalFilter, setTemporalFilter] = useState<string>("all");
  const [quadrantFilter, setQuadrantFilter] = useState<string>("all");

  const floorPlans = useMemo(() => {
    if (!qpuPlan) {
      return [];
    }
    return buildQpuFloorPlans(qpuPlan);
  }, [qpuPlan]);

  const rows = useMemo<TimelineRow[]>(() => {
    return floorPlans.flatMap((floor) =>
      floor.steps.map((step, index) => ({
        id: `${qpuPlan?.qpu_plan_id || "none"}-f${floor.floor}-s${index + 1}`,
        floor: floor.floor,
        step,
        quadrants: floor.slices.filter((slice) => slice.count > 0).map((slice) => slice.slice),
      })),
    );
  }, [floorPlans, qpuPlan?.qpu_plan_id]);

  const filteredRows = useMemo(() => {
    return rows.filter((row) => {
      if (floorFilter !== "all" && row.floor !== Number(floorFilter)) {
        return false;
      }
      if (temporalFilter !== "all" && activeProject?.temporal_group !== temporalFilter) {
        return false;
      }
      if (quadrantFilter !== "all" && !row.quadrants.includes(quadrantFilter as RRQuadrant)) {
        return false;
      }
      return true;
    });
  }, [activeProject?.temporal_group, floorFilter, quadrantFilter, rows, temporalFilter]);

  const rrRoute = qpuPlan?.rr_influence
    ? buildSeedRoute({
        quadrant: qpuPlan.rr_influence.quadrant,
        subnode: qpuPlan.rr_influence.subnode,
        logicMode: qpuPlan.rr_influence.logic_mode,
        temporalGroup: qpuPlan.rr_influence.temporal_group,
      })
    : undefined;

  return (
    <section id="enterprise-timeline" className="tower-execution-timeline" style={{ display: "grid", gap: "10px" }}>
      <div className="routing-controls">
        <label>
          Floor
          <select value={floorFilter} onChange={(event) => setFloorFilter(event.target.value)}>
            <option value="all">all</option>
            {floorPlans.map((floor) => (
              <option key={floor.floor} value={floor.floor}>
                floor {floor.floor}
              </option>
            ))}
          </select>
        </label>
        <label>
          Temporal
          <select value={temporalFilter} onChange={(event) => setTemporalFilter(event.target.value)}>
            <option value="all">all</option>
            <option value="past">past</option>
            <option value="present_past">present_past</option>
            <option value="present_future">present_future</option>
            <option value="future">future</option>
          </select>
        </label>
        <label>
          RR Quadrant
          <select value={quadrantFilter} onChange={(event) => setQuadrantFilter(event.target.value)}>
            <option value="all">all</option>
            <option value="language">language</option>
            <option value="arts">arts</option>
            <option value="math">math</option>
            <option value="science">science</option>
          </select>
        </label>
      </div>

      <ArtifactTagDisplay
        label="Tower Timeline Tags"
        tags={
          activeProject
            ? buildArtifactTags({
                profile: activeProject.artifact_tags.profile,
                compartmentName: activeProject.artifact_tags.compartment_name,
                compartmentIndex: activeProject.artifact_tags.compartment_index,
                phase: "work",
                temporalGroup: activeProject.temporal_group,
                tier: activeProject.tier,
                rrRoute,
                qpuPlanId: qpuPlan?.qpu_plan_id,
                floor: typeof activeFloor === "number" ? activeFloor : null,
                workspaceMode: "enterprise",
              })
            : null
        }
        workspaceMode="enterprise"
        semanticMix={qpuPlan?.slices.map((slice) => `${slice.slice}:${slice.count}`)}
      />

      <ul style={{ display: "grid", gap: "8px", listStyle: "none", padding: 0, margin: 0 }}>
        {filteredRows.map((row) => {
          const fallbackState: ExecutionState = resolveArtifactCompletion(workArtifacts, row.floor, row.step)
            ? "completed"
            : row.floor === activeFloor
              ? "in_progress"
              : "planned";
          const state = executionStateMap?.[row.id] || fallbackState;
          const stateColor = state === "completed" ? "#2f9b4b" : state === "in_progress" ? "#d4b117" : "#8fa1b5";

          return (
            <li
              key={row.id}
              style={{
                borderLeft: `4px solid ${stateColor}`,
                borderRadius: "8px",
                padding: "8px 10px",
                background: row.floor === activeFloor ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.03)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", alignItems: "center" }}>
                <strong>
                  Floor {row.floor} [{state}]
                </strong>
                <span style={{ fontSize: "12px" }}>{row.quadrants.join(" | ")}</span>
              </div>
              <p style={{ margin: "6px 0" }}>{row.step}</p>
              {onAdvanceState ? (
                <button type="button" onClick={() => onAdvanceState(row.id, state)}>
                  Advance State
                </button>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
