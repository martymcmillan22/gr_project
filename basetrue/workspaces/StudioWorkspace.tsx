import { useMemo, useState } from "react";
import ArtifactTagDisplay from "../components/ArtifactTagDisplay";
import IdeaEditor from "../components/IdeaEditor";
import ProjectCreator from "../components/ProjectCreator";
import QPUFrame from "../components/QPUFrame";
import RRDiagram from "../components/RRDiagram";
import SeedEditor from "../components/SeedEditor";
import WorkPanel from "../components/WorkPanel";
import {
  canUseGovernedApplyMode,
  getGovernanceProfilesForTier,
  isGovernanceProfileAllowed,
} from "../logic/pipelineLogic";
import { getPhaseColor, getTemporalGroup, getViewType } from "../logic/temporalRouting";
import { buildSeedRoute } from "../logic/rrRouter";
import { STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP } from "../logic/baseTrueConstants";
import type {
  GovernanceProfile,
  IdeaRecord,
  ProfileKind,
  ProjectRecord,
  RRLogicMode,
  RRQuadrant,
  RRSubnode,
  SeedRecord,
  StudioAccessTier,
} from "../types";

type StudioStage = "idea" | "seed" | "project" | "work";

interface StudioWorkspaceProps {
  initialTier?: StudioAccessTier;
  initialProfile?: ProfileKind;
  initialCompartmentIndex?: number;
}

const STUDIO_STAGES: Array<{ key: StudioStage; label: string }> = [
  { key: "idea", label: "Idea" },
  { key: "seed", label: "Seed" },
  { key: "project", label: "Project" },
  { key: "work", label: "Work" },
];

function clampStudioCompartmentIndex(value: number): number {
  if (!Number.isFinite(value)) {
    return 5;
  }
  return Math.min(8, Math.max(5, Math.floor(value)));
}

export default function StudioWorkspace({
  initialTier = "studio",
  initialProfile = "public",
  initialCompartmentIndex = 5,
}: StudioWorkspaceProps) {
  const [accessTier, setAccessTier] = useState<StudioAccessTier>(initialTier);
  const [profile, setProfile] = useState<ProfileKind>(initialProfile);
  const [compartmentIndex, setCompartmentIndex] = useState<number>(clampStudioCompartmentIndex(initialCompartmentIndex));
  const [activeStage, setActiveStage] = useState<StudioStage>("idea");
  const [idea, setIdea] = useState<IdeaRecord | null>(null);
  const [seed, setSeed] = useState<SeedRecord | null>(null);
  const [project, setProject] = useState<ProjectRecord | null>(null);

  const [rrQuadrant, setRrQuadrant] = useState<RRQuadrant>("language");
  const [rrSubnode, setRrSubnode] = useState<RRSubnode>("A");
  const [rrLogicMode, setRrLogicMode] = useState<RRLogicMode>("hierarchical");

  const temporalGroup = useMemo(() => getTemporalGroup(compartmentIndex), [compartmentIndex]);
  const view = useMemo(() => getViewType(temporalGroup), [temporalGroup]);
  const compartmentName = `studio-workspace-${compartmentIndex}`;
  const workspaceTier: StudioAccessTier = "studio";
  const governanceProfiles = useMemo(() => getGovernanceProfilesForTier("studio"), []);
  const canRunGovernedApply = useMemo(() => canUseGovernedApplyMode("studio"), []);
  const temporalOwner = useMemo(() => {
    if (STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP.qc_user.includes(temporalGroup)) {
      return "QC";
    }
    if (STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP.qa_va.includes(temporalGroup)) {
      return "QA";
    }
    return "unassigned";
  }, [temporalGroup]);
  const profileBadges = useMemo(() => {
    return governanceProfiles.map((profileName: GovernanceProfile) => ({
      profile: profileName,
      allowed: isGovernanceProfileAllowed("studio", profileName),
    }));
  }, [governanceProfiles]);

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

  const handleIdeaCreate = (nextIdea: IdeaRecord) => {
    setIdea(nextIdea);
    setSeed(null);
    setProject(null);
    setActiveStage("seed");
  };

  const handleSeedCreate = (nextSeed: SeedRecord) => {
    setSeed(nextSeed);
    setProject(null);
    setActiveStage("project");
  };

  const handleProjectCreate = (nextProject: ProjectRecord) => {
    setProject(nextProject);
    setActiveStage("work");
  };

  const handleProjectUpdate = (nextProject: ProjectRecord) => {
    setProject(nextProject);
  };

  return (
    <section className="studio-workspace" role="region" aria-labelledby="studio-workspace-heading">
      <header className="panel studio-header-panel" role="region" aria-labelledby="studio-workspace-heading">
        <p className="eyebrow">BaseTrue Studio Workspace</p>
        <h2 id="studio-workspace-heading">Controlled Creative Workstation</h2>
        <p className="status-line studio-status-line">
          Linear flow: Idea -&gt; Seed -&gt; Project -&gt; Work. Studio enforces scaled QPU with no tower floors.
        </p>

        <div className="studio-stage-rail" role="list" aria-label="Studio stage progression">
          {STUDIO_STAGES.map((stage, index) => (
            <span
              key={stage.key}
              className={`studio-stage-pill${activeStage === stage.key ? " is-active" : ""}`}
              role="listitem"
              aria-current={activeStage === stage.key ? "step" : undefined}
            >
              {index + 1}. {stage.label}
            </span>
          ))}
        </div>

        <div className="studio-summary-grid" role="list" aria-label="Studio workspace summary">
          <article className="studio-summary-card" role="listitem">
            <h4>Temporal Owner</h4>
            <p className={`studio-owner-pill owner-${temporalOwner.toLowerCase()}`}>{temporalOwner}</p>
            <p className="studio-summary-detail">Compartment group drives QC/QA overlay ownership.</p>
          </article>
          <article className="studio-summary-card" role="listitem">
            <h4>View Context</h4>
            <p className="studio-summary-keyline">Temporal: {temporalGroup}</p>
            <p className="studio-summary-keyline">View: {view}</p>
          </article>
          <article className="studio-summary-card" role="listitem">
            <h4>Route Preview</h4>
            <p className="studio-summary-route">{rrRoutePreview}</p>
            <p className="studio-summary-detail">Preview only; Studio remains deterministic and gated.</p>
          </article>
        </div>

        <div className="routing-controls studio-routing-controls">
          <label>
            Access Tier
            <select value={accessTier} onChange={() => setAccessTier("studio")}>
              <option value="studio">studio</option>
            </select>
          </label>
          <label>
            Profile
            <select value={profile} onChange={(event) => setProfile(event.target.value === "personal" ? "personal" : "public")}>
              <option value="public">public</option>
              <option value="personal">personal</option>
            </select>
          </label>
          <label>
            Compartment (5-8)
            <input
              type="number"
              min={5}
              max={8}
              value={compartmentIndex}
              onChange={(event) => setCompartmentIndex(clampStudioCompartmentIndex(Number(event.target.value || 5)))}
            />
          </label>
        </div>

        <p className="status-line studio-status-line" role="status" aria-live="polite">
          Stage: {activeStage} | Temporal: {temporalGroup} | View: {view} | RR route preview: {rrRoutePreview}
        </p>
        <p className="status-line studio-status-line">
          Governance profiles: {governanceProfiles.join(", ")} | Temporal overlay owner: {temporalOwner}
        </p>

        <div className="studio-badge-row">
          {profileBadges.map((item) => (
            <span key={item.profile} className={`commands-badge studio-badge ${item.allowed ? "is-allowed" : "is-blocked"}`}>
              {item.profile}:{item.allowed ? "allowed" : "blocked"}
            </span>
          ))}
          <span className="commands-badge studio-badge is-blocked">governed apply:{canRunGovernedApply ? "enabled" : "disabled"}</span>
          <span className="commands-badge studio-badge is-blocked">release workflows:disabled</span>
        </div>

        <div className="studio-command-row" aria-label="Studio disabled enterprise actions">
          <button type="button" className="studio-disabled-command" disabled>
            improve-all --apply (enterprise only)
          </button>
          <button type="button" className="studio-disabled-command" disabled>
            release --bump patch (enterprise only)
          </button>
          <button type="button" className="studio-disabled-command" disabled>
            release-notes (enterprise only)
          </button>
        </div>
      </header>

      <section className="panel studio-panel phase-section phase-create" data-color={getPhaseColor("create", temporalGroup)}>
        <h3>1. Idea Panel</h3>
        <p>Non-interactive RR preview for initial ideation context.</p>
        <IdeaEditor
          profile={profile}
          compartmentName={compartmentName}
          compartmentIndex={compartmentIndex}
          temporalGroup={temporalGroup}
          tier={workspaceTier}
          phaseColor={getPhaseColor("create", temporalGroup)}
          onCreate={handleIdeaCreate}
          existingIdea={idea}
        />
        <ArtifactTagDisplay label="Studio Idea Tags" tags={idea?.artifact_tags} />
        <RRDiagram
          isLargeScreen={true}
          tier={workspaceTier}
          temporalGroup={temporalGroup}
          selectedQuadrant={rrQuadrant}
          selectedSubnode={rrSubnode}
          selectedLogicMode={rrLogicMode}
          routingEnabled={false}
          interactive={false}
        />
        <button type="button" onClick={() => setActiveStage("seed")} disabled={!idea}>
          Seed Formation
        </button>
      </section>

      <section className="panel studio-panel phase-section phase-create" data-color={getPhaseColor("create", temporalGroup)}>
        <h3>2. Seed Panel</h3>
        <SeedEditor
          profile={profile}
          compartmentName={compartmentName}
          compartmentIndex={compartmentIndex}
          temporalGroup={temporalGroup}
          tier={workspaceTier}
          phaseColor={getPhaseColor("create", temporalGroup)}
          idea={idea}
          existingSeed={seed}
          onCreate={handleSeedCreate}
          rrQuadrant={rrQuadrant}
          rrSubnode={rrSubnode}
          rrLogicMode={rrLogicMode}
          onRrQuadrantChange={setRrQuadrant}
          onRrSubnodeChange={setRrSubnode}
          onRrLogicModeChange={setRrLogicMode}
        />
        <RRDiagram
          isLargeScreen={true}
          tier={workspaceTier}
          temporalGroup={temporalGroup}
          selectedQuadrant={rrQuadrant}
          selectedSubnode={rrSubnode}
          selectedLogicMode={rrLogicMode}
          onSelectQuadrant={setRrQuadrant}
          onSelectSubnode={setRrSubnode}
          onSelectLogicMode={setRrLogicMode}
          routingEnabled={true}
          interactive={true}
        />
        <ArtifactTagDisplay label="Studio Seed Tags" tags={seed?.artifact_tags} />
        <button type="button" onClick={() => setActiveStage("project")} disabled={!seed}>
          Activate Project
        </button>
      </section>

      <section className="panel studio-panel phase-section phase-post" data-color={getPhaseColor("post", temporalGroup)}>
        <h3>3. Project Panel</h3>
        <ProjectCreator
          profile={profile}
          compartmentName={compartmentName}
          compartmentIndex={compartmentIndex}
          temporalGroup={temporalGroup}
          tier={workspaceTier}
          phaseColor={getPhaseColor("post", temporalGroup)}
          seed={seed}
          existingProject={project}
          workspaceMode="studio"
          onCreate={handleProjectCreate}
        />
        <QPUFrame
          compartmentIndex={compartmentIndex}
          tier={workspaceTier}
          temporalGroup={temporalGroup}
          seed={seed}
          project={project}
          scaledOnly={true}
          workspaceMode="studio"
        />
        <ArtifactTagDisplay label="Studio Project Tags" tags={project?.artifact_tags} />
        <button type="button" onClick={() => setActiveStage("work")} disabled={!project}>
          Enter Work Phase
        </button>
      </section>

      <section className="panel studio-panel phase-section phase-work" data-color={getPhaseColor("work", temporalGroup)}>
        <h3>4. Work Panel</h3>
        <p>Simplified Garden view with flat orchestration and no tower floors.</p>
        <WorkPanel
          profile={profile}
          compartmentName={compartmentName}
          compartmentIndex={compartmentIndex}
          temporalGroup={temporalGroup}
          tier={workspaceTier}
          phaseColor={getPhaseColor("work", temporalGroup)}
          project={project}
          onUpdate={handleProjectUpdate}
          readOnly={false}
          simplifiedMode={true}
          workspaceMode="studio"
        />
        <ArtifactTagDisplay label="Studio Work Tags" tags={project?.work_artifacts?.[0]?.artifact_tags} />
      </section>
    </section>
  );
}
