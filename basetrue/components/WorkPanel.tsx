import { useState } from "react";
import ArtifactTagDisplay from "./ArtifactTagDisplay";
import { buildArtifactTags } from "../logic/artifactTagging";
import { canUseQPUTower } from "../logic/pipelineLogic";
import { buildQpuFloorPlans, buildWorkOrchestrationSteps } from "../logic/qpuEngine";
import type { ProfileKind, ProjectRecord, TemporalGroup, Tier, WorkRecord, WorkspaceMode } from "../types";

interface WorkPanelProps {
  profile: ProfileKind;
  compartmentName: string;
  compartmentIndex: number;
  temporalGroup: TemporalGroup;
  tier: Tier;
  phaseColor: string;
  project: ProjectRecord | null;
  selectedFloor?: number;
  onFloorSelect?: (floor: number) => void;
  onUpdate: (project: ProjectRecord) => void;
  readOnly?: boolean;
  simplifiedMode?: boolean;
  workspaceMode?: WorkspaceMode;
}

export default function WorkPanel({
  profile,
  compartmentName,
  compartmentIndex,
  temporalGroup,
  tier,
  phaseColor,
  project,
  selectedFloor,
  onFloorSelect,
  onUpdate,
  readOnly = false,
  simplifiedMode = false,
  workspaceMode = "default",
}: WorkPanelProps) {
  const [workStateInput, setWorkStateInput] = useState(project?.work_state || "active");
  const hasTower = simplifiedMode ? false : canUseQPUTower(tier);
  const orchestrationSteps = project ? buildWorkOrchestrationSteps(project.qpu_plan) : [];
  const floorPlans = project && !simplifiedMode ? buildQpuFloorPlans(project.qpu_plan) : [];
  const activeFloor = floorPlans.find((floor) => floor.floor === selectedFloor) || floorPlans[0] || null;
  const effectiveFloor = simplifiedMode ? null : activeFloor;
  const persistedSteps = simplifiedMode ? orchestrationSteps : activeFloor?.steps || [];
  const workTagPreview = project
    ? buildArtifactTags({
        profile,
        compartmentName,
        compartmentIndex,
        phase: "work",
        temporalGroup,
        tier,
        rrSelection: project.qpu_plan.rr_influence,
        qpuPlanId: project.qpu_plan.qpu_plan_id,
        floor: effectiveFloor?.floor,
        workspaceMode,
      })
    : null;

  const saveWorkState = () => {
    if (!project) {
      return;
    }

    onUpdate({
      ...project,
      phase: "work",
      work_state: workStateInput.trim() || "active",
      work_artifacts: persistedSteps.map((step, index) => {
        const workTags = buildArtifactTags({
          profile,
          compartmentName,
          compartmentIndex,
          phase: "work",
          temporalGroup,
          tier,
          rrSelection: project.qpu_plan.rr_influence,
          qpuPlanId: project.qpu_plan.qpu_plan_id,
          floor: effectiveFloor?.floor,
          workspaceMode,
        });

        const workRecord: WorkRecord = {
          work_id: `work-${project.project_id}-${effectiveFloor?.floor || 1}-${index + 1}`,
          project_id: project.project_id,
          floor: effectiveFloor?.floor || 1,
          task: step,
          temporal_group: temporalGroup,
          phase: "work",
          tier,
          artifact_tags: workTags,
        };

        return workRecord;
      }),
      artifact_tags: buildArtifactTags({
        profile,
        compartmentName,
        compartmentIndex,
        phase: "work",
        temporalGroup,
        tier,
        rrSelection: project.qpu_plan.rr_influence,
        qpuPlanId: project.qpu_plan.qpu_plan_id,
        floor: effectiveFloor?.floor,
        workspaceMode,
      }),
    });
  };

  return (
    <article className="pipeline-card" data-color={phaseColor}>
      <h3>Work Phase</h3>
      <p>Temporal group: {temporalGroup}</p>
      <p>Tower mode: {hasTower ? "enabled" : "disabled"}</p>
      {simplifiedMode ? <p>Studio mode: flat work orchestration (no floor drill-down).</p> : null}
      <ArtifactTagDisplay label="Work Project Tags" tags={project?.artifact_tags} />
      <ArtifactTagDisplay label="Work Artifact Tags" tags={workTagPreview} />
      {project ? (
        <>
          <ul>
            {orchestrationSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>

          {floorPlans.length > 0 ? (
            <section>
              <h4>Enterprise floor drill-down</h4>
              <div>
                {floorPlans.map((floor) => (
                  <button
                    key={floor.floor}
                    type="button"
                    onClick={() => onFloorSelect?.(floor.floor)}
                    aria-pressed={activeFloor?.floor === floor.floor}
                    disabled={readOnly}
                  >
                    Floor {floor.floor} ({floor.total_count})
                  </button>
                ))}
              </div>
              {activeFloor ? (
                <>
                  <p>
                    Active floor: {activeFloor.floor} | Slices:{" "}
                    {activeFloor.slices.map((slice) => `${slice.slice}:${slice.count}`).join(" | ")}
                  </p>
                  <ul>
                    {activeFloor.steps.map((step) => (
                      <li key={`${activeFloor.floor}-${step}`}>{step}</li>
                    ))}
                  </ul>
                </>
              ) : null}
            </section>
          ) : null}
        </>
      ) : null}

      <label>
        Work State
        <input value={workStateInput} onChange={(event) => setWorkStateInput(event.target.value)} disabled={!project || readOnly} />
      </label>

      <button type="button" onClick={saveWorkState} disabled={!project || readOnly}>
        Enter Work Phase
      </button>
    </article>
  );
}
