import { useState } from "react";
import ArtifactTagDisplay from "./ArtifactTagDisplay";
import QPUTower from "./QPUTower";
import WorkPanel from "./WorkPanel";
import type { CompartmentViewMode, ProfileKind, ProjectRecord, TemporalGroup, Tier, ViewType } from "../types";

interface PhaseSectionWorkProps {
  profile: ProfileKind;
  compartmentName: string;
  compartmentIndex: number;
  tier: Tier;
  temporalGroup: TemporalGroup;
  view: ViewType;
  color: string;
  showQPUTower: boolean;
  viewMode?: CompartmentViewMode;
  project: ProjectRecord | null;
  onProjectUpdate: (project: ProjectRecord) => void;
}

export default function PhaseSectionWork({
  profile,
  compartmentName,
  compartmentIndex,
  tier,
  temporalGroup,
  view,
  color,
  showQPUTower,
  viewMode = "pipeline",
  project,
  onProjectUpdate,
}: PhaseSectionWorkProps) {
  const [selectedFloor, setSelectedFloor] = useState(1);
  const isDashboard = viewMode === "dashboard";

  return (
    <section className="phase-section phase-work" data-color={color}>
      <h2>Work</h2>
      <p>Temporal Group: {temporalGroup}</p>
      <p>View: {view}</p>
      <ArtifactTagDisplay label="Work Project Tags" tags={project?.artifact_tags} />
      {isDashboard ? (
        <>
          <h3>Work Panel (Garden lens)</h3>
          <ul>
            <li>Work artifacts: {project?.work_artifacts?.length || 0}</li>
            <li>Active floor: {selectedFloor}</li>
          </ul>
        </>
      ) : null}
      <WorkPanel
        profile={profile}
        compartmentName={compartmentName}
        compartmentIndex={compartmentIndex}
        temporalGroup={temporalGroup}
        tier={tier}
        phaseColor={color}
        project={project}
        selectedFloor={selectedFloor}
        onFloorSelect={setSelectedFloor}
        onUpdate={onProjectUpdate}
        readOnly={isDashboard}
      />
      {showQPUTower ? (
        <QPUTower
          compartmentIndex={compartmentIndex}
          project={project}
          selectedFloor={selectedFloor}
          onFloorSelect={setSelectedFloor}
          interactive={!isDashboard}
        />
      ) : (
        <p>Tower hidden for this tier.</p>
      )}
    </section>
  );
}
