import ArtifactTagDisplay from "./ArtifactTagDisplay";
import ProjectCreator from "./ProjectCreator";
import QPUFrame from "./QPUFrame";
import type { CompartmentViewMode, ProfileKind, ProjectRecord, SeedRecord, TemporalGroup, Tier, ViewType } from "../types";

interface PhaseSectionPostProps {
  profile: ProfileKind;
  compartmentName: string;
  compartmentIndex: number;
  tier: Tier;
  temporalGroup: TemporalGroup;
  view: ViewType;
  color: string;
  showQPU: boolean;
  viewMode?: CompartmentViewMode;
  seed: SeedRecord | null;
  project: ProjectRecord | null;
  onProjectCreate: (project: ProjectRecord) => void;
}

export default function PhaseSectionPost({
  profile,
  compartmentName,
  compartmentIndex,
  tier,
  temporalGroup,
  view,
  color,
  showQPU,
  viewMode = "pipeline",
  seed,
  project,
  onProjectCreate,
}: PhaseSectionPostProps) {
  const isDashboard = viewMode === "dashboard";

  return (
    <section className="phase-section phase-post" data-color={color}>
      <h2>Post</h2>
      <p>Temporal Group: {temporalGroup}</p>
      <p>View: {view}</p>
      <ArtifactTagDisplay label="Post Project Tags" tags={project?.artifact_tags} />
      {isDashboard ? (
        <>
          <h3>Post Panel (Museum lens)</h3>
          <ul>
            <li>
              Latest Project: {project ? `${project.project_id} (${project.qpu_plan.qpu_plan_id})` : "none"}
            </li>
            <li>
              RR Route: {project?.artifact_tags.rr_route || seed?.rr_route || seed?.seed_route || "none"}
            </li>
          </ul>
        </>
      ) : (
        <ProjectCreator
          profile={profile}
          compartmentName={compartmentName}
          compartmentIndex={compartmentIndex}
          temporalGroup={temporalGroup}
          tier={tier}
          phaseColor={color}
          seed={seed}
          existingProject={project}
          onCreate={onProjectCreate}
        />
      )}
      {showQPU ? (
        <QPUFrame compartmentIndex={compartmentIndex} tier={tier} temporalGroup={temporalGroup} seed={seed} project={project} />
      ) : (
        <p>QPU hidden for this tier.</p>
      )}
    </section>
  );
}
