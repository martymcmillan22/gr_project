import { useMemo, useState } from "react";
import { buildArtifactTags, formatArtifactTags } from "../logic/artifactTagging";
import { canCreateProject, getProjectGeometryMode } from "../logic/pipelineLogic";
import { applyManualSliceAdjustments, buildQpuPlan } from "../logic/qpuEngine";
import type { ProfileKind, ProjectRecord, RRQuadrant, SeedRecord, TemporalGroup, Tier, WorkspaceMode } from "../types";
const QPU_SLICES: RRQuadrant[] = ["language", "arts", "math", "science"];

interface ProjectCreatorProps {
  profile: ProfileKind;
  compartmentName: string;
  compartmentIndex: number;
  temporalGroup: TemporalGroup;
  tier: Tier;
  phaseColor: string;
  seed: SeedRecord | null;
  existingProject: ProjectRecord | null;
  workspaceMode?: WorkspaceMode;
  onCreate: (project: ProjectRecord) => void;
}

export default function ProjectCreator({
  profile,
  compartmentName,
  compartmentIndex,
  temporalGroup,
  tier,
  phaseColor,
  seed,
  existingProject,
  workspaceMode = "default",
  onCreate,
}: ProjectCreatorProps) {
  const [workState, setWorkState] = useState(existingProject?.work_state || "prepared");
  const [artifactsInput, setArtifactsInput] = useState(existingProject?.artifacts.join(", ") || "");
  const [manualSlices, setManualSlices] = useState<Record<RRQuadrant, number>>({
    language: 0,
    arts: 0,
    math: 0,
    science: 0,
  });

  const canCreate = canCreateProject(tier);
  const geometryMode = getProjectGeometryMode();
  const qpuPlanPreview = useMemo(
    () =>
      buildQpuPlan({
        tier,
        compartmentIndex,
        temporalGroup,
        rrSelection: seed?.rr_selection,
        workspaceMode,
      }),
    [compartmentIndex, seed?.rr_selection, temporalGroup, tier, workspaceMode],
  );
  const manualTotal = useMemo(
    () => QPU_SLICES.reduce((sum, slice) => sum + (Number.isFinite(manualSlices[slice]) ? manualSlices[slice] : 0), 0),
    [manualSlices],
  );
  const manualOverCap = manualTotal > qpuPlanPreview.adjusted_count;
  const effectiveQpuPlan = useMemo(() => {
    if (manualTotal <= 0) {
      return qpuPlanPreview;
    }
    return applyManualSliceAdjustments(qpuPlanPreview, manualSlices);
  }, [manualSlices, manualTotal, qpuPlanPreview]);
  const projectTagPreview = useMemo(
    () =>
      buildArtifactTags({
        profile,
        compartmentName,
        compartmentIndex,
        phase: "post",
        temporalGroup,
        tier,
        rrRoute: seed?.rr_route || seed?.seed_route,
        rrSelection: seed?.rr_selection,
        qpuPlanId: effectiveQpuPlan.qpu_plan_id,
        workspaceMode,
      }),
    [
      compartmentIndex,
      compartmentName,
      effectiveQpuPlan.qpu_plan_id,
      profile,
      seed?.rr_route,
      seed?.rr_selection,
      seed?.seed_route,
      temporalGroup,
      tier,
      workspaceMode,
    ],
  );

  const gateMessage = useMemo(() => {
    if (!canCreate) {
      return "Project creation is available only for Studio and Enterprise tiers.";
    }
    if (workspaceMode === "studio") {
      return "Studio workspace enforces scaled QPU up to compartment 8 (no tower orchestration).";
    }
    if (tier === "studio") {
      return "Studio project uses scaled QPU up to compartment 8.";
    }
    return "Enterprise project uses full QPU coverage and tower-capable orchestration.";
  }, [canCreate, tier, workspaceMode]);

  const createProject = () => {
    if (!seed || !canCreate) {
      return;
    }

    const artifacts = artifactsInput
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    const project: ProjectRecord = {
      project_id: `project-${Date.now()}`,
      seed_id: seed.seed_id,
      qpu_allocation: effectiveQpuPlan.adjusted_count,
      qpu_plan: effectiveQpuPlan,
      temporal_group: temporalGroup,
      phase: "post",
      tier,
      work_state: workState,
      tower_level: workspaceMode === "studio" ? undefined : tier === "enterprise" ? Math.max(1, compartmentIndex - 4) : undefined,
      artifacts,
      geometry_mode: geometryMode,
      artifact_tags: buildArtifactTags({
        profile,
        compartmentName,
        compartmentIndex,
        phase: "post",
        temporalGroup,
        tier,
        rrRoute: seed.rr_route || seed.seed_route,
        rrSelection: seed.rr_selection,
        qpuPlanId: effectiveQpuPlan.qpu_plan_id,
        workspaceMode,
      }),
    };

    onCreate(project);
  };

  return (
    <article className="pipeline-card" data-color={phaseColor}>
      <h3>Project Formation</h3>
      <p>{gateMessage}</p>
      <p>Geometry mode: {geometryMode}</p>
      <p>QPU allocation: {qpuPlanPreview.adjusted_count}</p>
      <p>QPU mode: {qpuPlanPreview.orchestration_mode}</p>
      <p>QPU plan id: {effectiveQpuPlan.qpu_plan_id}</p>
      <p>Auto slice mix: {qpuPlanPreview.auto_slices.map((slice) => `${slice.slice}:${slice.count}`).join(" | ")}</p>
      <p>
        Effective slice mix: {effectiveQpuPlan.slices.map((slice) => `${slice.slice}:${slice.count}`).join(" | ")} ({manualTotal > 0 ? "manual override active" : "auto"})
      </p>
      {qpuPlanPreview.notes.length > 0 ? <p>Plan notes: {qpuPlanPreview.notes.join(" ")}</p> : null}
      <p>Artifact tags: {formatArtifactTags(projectTagPreview)}</p>

      <fieldset disabled={!canCreate || !seed}>
        <legend>Manual slice redistribution (cannot exceed adjusted QPU)</legend>
        {QPU_SLICES.map((slice) => (
          <label key={slice}>
            {slice}
            <input
              type="number"
              min={0}
              value={manualSlices[slice]}
              onChange={(event) => {
                const value = Number.parseInt(event.target.value, 10);
                setManualSlices((current) => ({
                  ...current,
                  [slice]: Number.isFinite(value) ? Math.max(0, value) : 0,
                }));
              }}
            />
          </label>
        ))}
        <p>
          Manual total: {manualTotal} / {qpuPlanPreview.adjusted_count}
        </p>
        {manualOverCap ? <p>Manual overrides exceed adjusted QPU and cannot be applied.</p> : null}
      </fieldset>

      <label>
        Work State
        <input value={workState} onChange={(event) => setWorkState(event.target.value)} disabled={!canCreate || !seed} />
      </label>

      <label>
        Artifacts (comma-separated)
        <input
          value={artifactsInput}
          onChange={(event) => setArtifactsInput(event.target.value)}
          disabled={!canCreate || !seed}
          placeholder="artifact.a, artifact.b"
        />
      </label>

      <button type="button" onClick={createProject} disabled={!canCreate || !seed || manualOverCap}>
        Activate Project
      </button>
    </article>
  );
}
