import { useEffect, useMemo, useState } from "react";
import ArtifactTagDisplay from "./ArtifactTagDisplay";
import IdeaEditor from "./IdeaEditor";
import RRDiagram from "./RRDiagram";
import SeedEditor from "./SeedEditor";
import { buildSeedRoute } from "../logic/rrRouter";
import { canRouteRRInPipeline } from "../logic/pipelineLogic";
import type { CompartmentViewMode, IdeaRecord, ProfileKind, SeedRecord, TemporalGroup, Tier, ViewType } from "../types";

interface PhaseSectionCreateProps {
  profile: ProfileKind;
  compartmentName: string;
  compartmentIndex: number;
  tier: Tier;
  temporalGroup: TemporalGroup;
  view: ViewType;
  color: string;
  showRR: boolean;
  viewMode?: CompartmentViewMode;
  idea: IdeaRecord | null;
  seed: SeedRecord | null;
  onIdeaCreate: (idea: IdeaRecord) => void;
  onSeedCreate: (seed: SeedRecord) => void;
}

export default function PhaseSectionCreate({
  profile,
  compartmentName,
  compartmentIndex,
  tier,
  temporalGroup,
  view,
  color,
  showRR,
  viewMode = "pipeline",
  idea,
  seed,
  onIdeaCreate,
  onSeedCreate,
}: PhaseSectionCreateProps) {
  const [rrQuadrant, setRrQuadrant] = useState(seed?.rr_selection?.quadrant || "language");
  const [rrSubnode, setRrSubnode] = useState(seed?.rr_selection?.subnode || "A");
  const [rrLogicMode, setRrLogicMode] = useState(seed?.rr_selection?.logic_mode || "hierarchical");

  useEffect(() => {
    if (!seed?.rr_selection) {
      return;
    }
    setRrQuadrant(seed.rr_selection.quadrant);
    setRrSubnode(seed.rr_selection.subnode);
    setRrLogicMode(seed.rr_selection.logic_mode);
  }, [seed?.rr_selection]);

  const routingEnabled = canRouteRRInPipeline(tier);
  const isDashboard = viewMode === "dashboard";
  const rrRoutePreview = useMemo(
    () =>
      buildSeedRoute({
        quadrant: rrQuadrant,
        subnode: rrSubnode,
        logicMode: rrLogicMode,
        temporalGroup,
      }),
    [rrLogicMode, rrQuadrant, rrSubnode, temporalGroup],
  );

  return (
    <section className="phase-section phase-create" data-color={color}>
      <h2>Create</h2>
      <p>Temporal Group: {temporalGroup}</p>
      <p>View: {view}</p>
      <p>Seed route preview: {rrRoutePreview}</p>
      <ArtifactTagDisplay label="Create Idea Tags" tags={idea?.artifact_tags} />
      <ArtifactTagDisplay label="Create Seed Tags" tags={seed?.artifact_tags} emptyText="rr_route.pending" />
      {isDashboard ? (
        <>
          <h3>Create Panel (Corporation lens)</h3>
          <ul>
            <li>
              Latest Idea: {idea ? `${idea.title} (${idea.temporal_group})` : "none"}
            </li>
            <li>
              Latest Seed: {seed ? `${seed.seed_id} (${seed.rr_route || seed.seed_route || "rr_route.pending"})` : "none"}
            </li>
          </ul>
        </>
      ) : (
        <>
          <IdeaEditor
            profile={profile}
            compartmentName={compartmentName}
            compartmentIndex={compartmentIndex}
            temporalGroup={temporalGroup}
            tier={tier}
            phaseColor={color}
            onCreate={onIdeaCreate}
            existingIdea={idea}
          />
          <SeedEditor
            profile={profile}
            compartmentName={compartmentName}
            compartmentIndex={compartmentIndex}
            temporalGroup={temporalGroup}
            tier={tier}
            phaseColor={color}
            idea={idea}
            existingSeed={seed}
            onCreate={onSeedCreate}
            rrQuadrant={rrQuadrant}
            rrSubnode={rrSubnode}
            rrLogicMode={rrLogicMode}
            onRrQuadrantChange={setRrQuadrant}
            onRrSubnodeChange={setRrSubnode}
            onRrLogicModeChange={setRrLogicMode}
          />
        </>
      )}
      {showRR ? (
        <RRDiagram
          isLargeScreen={true}
          tier={tier}
          temporalGroup={temporalGroup}
          selectedQuadrant={rrQuadrant}
          selectedSubnode={rrSubnode}
          selectedLogicMode={rrLogicMode}
          onSelectQuadrant={setRrQuadrant}
          onSelectSubnode={setRrSubnode}
          onSelectLogicMode={setRrLogicMode}
          routingEnabled={isDashboard ? false : routingEnabled}
          interactive={!isDashboard}
        />
      ) : (
        <p>RR hidden for this tier.</p>
      )}
    </section>
  );
}
