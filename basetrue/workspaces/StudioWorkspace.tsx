import { useEffect, useMemo, useState } from "react";
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
import { buildPhase18PlaceholderExportEnvelope } from "../logic/ebooks/phase18/ebookPhase18Placeholder";
import { buildPhase19ExportEnvelope } from "../logic/ebooks/phase19/ebookPhase19Export";
import { buildPhase19LogicSpine } from "../logic/ebooks/phase19/ebookPhase19LogicSpine";
import { buildPhase19Orchestrator } from "../logic/ebooks/phase19/ebookPhase19Orchestrator";
import { buildPhase19TypeCheck } from "../logic/ebooks/phase19/ebookPhase19TypeCheck";
import type { EBookPhase19Placement } from "../logic/ebooks/phase19/ebookPhase19Placement";
import type { EBookPhase19RuntimeEnvelope } from "../logic/ebooks/phase19/ebookPhase19Envelope";
import { emitDeterministicTelemetry, incrementDeterministicMetric } from "../../frontend_homepage/src/ui/deterministicTelemetry";
import { buildPhase20Diagnostics } from "../logic/ebooks/phase20/ebookPhase20Diagnostics";
import { buildPhase20ExportEnvelope as buildPhase20Export } from "../logic/ebooks/phase20/ebookPhase20Export";
import { buildPhase20RuntimePlan } from "../logic/ebooks/phase20/ebookPhase20RuntimePlan";
import { runPhase20DryRun } from "../logic/ebooks/phase20/ebookPhase20DryRunEngine";
import { buildPhase21ExportEnvelope } from "../logic/ebooks/phase21/ebookPhase21Export";
import { buildPhase21PreRouter } from "../logic/ebooks/phase21/ebookPhase21PreRouter";
import { buildPhase21RuntimeIntent } from "../logic/ebooks/phase21/ebookPhase21RuntimeIntent";
import { buildPhase21RuntimeLanes } from "../logic/ebooks/phase21/ebookPhase21RuntimeLanes";
import { buildPhase22ResolutionPlan } from "../logic/ebooks/phase22/ebookPhase22ResolutionPlan";
import { runPhase22Resolution } from "../logic/ebooks/phase22/ebookPhase22ResolutionEngine";
import { buildPhase22ResolutionDiagnostics } from "../logic/ebooks/phase22/ebookPhase22ResolutionDiagnostics";
import { buildPhase22ExportEnvelope } from "../logic/ebooks/phase22/ebookPhase22Export";
import { buildPhase23MaterialPlan } from "../logic/ebooks/phase23/ebookPhase23MaterialPlan";
import { runPhase23Material } from "../logic/ebooks/phase23/ebookPhase23MaterialEngine";
import { buildPhase23MaterialDiagnostics } from "../logic/ebooks/phase23/ebookPhase23MaterialDiagnostics";
import { buildPhase23ExportEnvelope } from "../logic/ebooks/phase23/ebookPhase23Export";
import { buildPhase24ActivationPlan } from "../logic/ebooks/phase24/ebookPhase24ActivationPlan";
import { runPhase24Activation } from "../logic/ebooks/phase24/ebookPhase24ActivationEngine";
import { buildPhase24ActivationDiagnostics } from "../logic/ebooks/phase24/ebookPhase24ActivationDiagnostics";
import { buildPhase24ExportEnvelope } from "../logic/ebooks/phase24/ebookPhase24Export";
import { buildPhase25ProjectionPlan } from "../logic/ebooks/phase25/ebookPhase25ProjectionPlan";
import { runPhase25Projection } from "../logic/ebooks/phase25/ebookPhase25ProjectionEngine";
import { buildPhase25ProjectionDiagnostics } from "../logic/ebooks/phase25/ebookPhase25ProjectionDiagnostics";
import { buildPhase25ExportEnvelope } from "../logic/ebooks/phase25/ebookPhase25Export";
import { buildPhase26TranslationPlan } from "../logic/ebooks/phase26/ebookPhase26TranslationPlan";
import { runPhase26Translation } from "../logic/ebooks/phase26/ebookPhase26TranslationEngine";
import { buildPhase26TranslationDiagnostics } from "../logic/ebooks/phase26/ebookPhase26TranslationDiagnostics";
import { buildPhase26ExportEnvelope } from "../logic/ebooks/phase26/ebookPhase26Export";
import { buildPhase27RenderingPlan } from "../logic/ebooks/phase27/ebookPhase27RenderingPlan";
import { runPhase27Rendering } from "../logic/ebooks/phase27/ebookPhase27RenderingEngine";
import { buildPhase27RenderingDiagnostics } from "../logic/ebooks/phase27/ebookPhase27RenderingDiagnostics";
import { buildPhase27ExportEnvelope } from "../logic/ebooks/phase27/ebookPhase27Export";
import { buildPhase28SerializationPlan } from "../logic/ebooks/phase28/ebookPhase28SerializationPlan";
import { runPhase28Serialization } from "../logic/ebooks/phase28/ebookPhase28SerializationEngine";
import { buildPhase28SerializationDiagnostics } from "../logic/ebooks/phase28/ebookPhase28SerializationDiagnostics";
import { buildPhase28ExportEnvelope } from "../logic/ebooks/phase28/ebookPhase28Export";
import { buildPhase29TransmissionPlan } from "../logic/ebooks/phase29/ebookPhase29TransmissionPlan";
import { runPhase29Transmission } from "../logic/ebooks/phase29/ebookPhase29TransmissionEngine";
import { buildPhase29TransmissionDiagnostics } from "../logic/ebooks/phase29/ebookPhase29TransmissionDiagnostics";
import { buildPhase29ExportEnvelope } from "../logic/ebooks/phase29/ebookPhase29Export";
import { buildPhase30FinalizationPlan } from "../logic/ebooks/phase30/ebookPhase30FinalizationPlan";
import { runPhase30Finalization } from "../logic/ebooks/phase30/ebookPhase30FinalizationEngine";
import { buildPhase30FinalizationDiagnostics } from "../logic/ebooks/phase30/ebookPhase30FinalizationDiagnostics";
import { buildPhase30ExportEnvelope } from "../logic/ebooks/phase30/ebookPhase30Export";
import type {
  GovernanceProfile,
  IdeaRecord,
  ProfileKind,
  ProjectRecord,
  RRLogicMode,
  RRQuadrant,
  RRSubnode,
  SeedRecord,
  TemporalGroup,
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
  const emitStudioTelemetry = (eventName: string, payload: Record<string, unknown> = {}) => {
    emitDeterministicTelemetry({
      eventName,
      tier: "studio",
      surface: "workspace",
      payload,
    });
  };

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
    if (temporalGroup === "past" || temporalGroup === "present_past") {
      return "QC";
    }
    if (temporalGroup === "present_future" || temporalGroup === "future") {
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
    emitStudioTelemetry("studio.idea.created", {
      compartmentIndex,
      temporalGroup,
    });
    incrementDeterministicMetric("studio.idea.created", {
      tier: "studio",
    });
  };

  const handleSeedCreate = (nextSeed: SeedRecord) => {
    setSeed(nextSeed);
    setProject(null);
    setActiveStage("project");
    emitStudioTelemetry("studio.seed.created", {
      compartmentIndex,
      temporalGroup,
    });
    incrementDeterministicMetric("studio.seed.created", {
      tier: "studio",
    });
  };

  const handleProjectCreate = (nextProject: ProjectRecord) => {
    setProject(nextProject);
    setActiveStage("work");
    emitStudioTelemetry("studio.project.created", {
      compartmentIndex,
      temporalGroup,
      projectId: nextProject.project_id,
    });
    incrementDeterministicMetric("studio.project.created", {
      tier: "studio",
    });
  };

  const handleProjectUpdate = (nextProject: ProjectRecord) => {
    setProject(nextProject);
    emitStudioTelemetry("studio.project.updated", {
      projectId: nextProject.project_id,
    });
  };

  useEffect(() => {
    emitStudioTelemetry("studio.workspace.loaded", {
      compartmentIndex,
      profile,
      stage: activeStage,
    });
    incrementDeterministicMetric("studio.workspace.loaded", {
      tier: "studio",
    });
    // This mount event is deterministic and intentionally one-time.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    emitStudioTelemetry("studio.stage.changed", {
      stage: activeStage,
      compartmentIndex,
      temporalGroup,
    });
  }, [activeStage, compartmentIndex, temporalGroup]);

  useEffect(() => {
    emitStudioTelemetry("studio.compartment.changed", {
      compartmentIndex,
      temporalGroup,
      view,
    });
  }, [compartmentIndex, temporalGroup, view]);

  useEffect(() => {
    emitStudioTelemetry("studio.route.preview.changed", {
      rrRoutePreview,
      rrQuadrant,
      rrSubnode,
      rrLogicMode,
    });
  }, [rrLogicMode, rrQuadrant, rrRoutePreview, rrSubnode]);

  const phase18EBookSurfaces = ["list", "detail", "how_to", "present"] as const;
  const phase18StudioExportEnvelope = buildPhase18PlaceholderExportEnvelope("studio");
  const phase19RuntimeEnvelope: EBookPhase19RuntimeEnvelope = {
    generatedAt: "phase19-placeholder",
    envelopeId: "phase19-runtime-envelope-placeholder",
    phase18: phase18StudioExportEnvelope,
    mode: "static",
  };
  const phase19Placement: EBookPhase19Placement = {
    generatedAt: "phase19-placeholder",
    placementId: "phase19-placement-placeholder",
    runtimeEnvelopeId: phase19RuntimeEnvelope.envelopeId,
    region: "studio",
    mode: "static",
  };
  const phase19LogicSpine = buildPhase19LogicSpine(phase19RuntimeEnvelope);
  const phase19Orchestrator = buildPhase19Orchestrator(phase19LogicSpine);
  const phase19TypeCheck = buildPhase19TypeCheck(phase19Orchestrator);
  const phase19ExportEnvelope = buildPhase19ExportEnvelope(phase19TypeCheck);
  const phase20RuntimePlan = buildPhase20RuntimePlan(phase19ExportEnvelope);
  const phase20DryRunResult = runPhase20DryRun(phase20RuntimePlan);
  const phase20Diagnostics = buildPhase20Diagnostics(phase20DryRunResult);
  const phase20ExportEnvelope = buildPhase20Export(phase20Diagnostics);
  const phase21RuntimeIntent = buildPhase21RuntimeIntent(phase20ExportEnvelope);
  const phase21RuntimeLanes = buildPhase21RuntimeLanes(phase21RuntimeIntent);
  const phase21PreRouter = buildPhase21PreRouter(phase21RuntimeLanes);
  const phase21ExportEnvelope = buildPhase21ExportEnvelope(phase21PreRouter);
  const phase22ResolutionPlan = buildPhase22ResolutionPlan(phase21ExportEnvelope);
  const phase22ResolutionResult = runPhase22Resolution(phase22ResolutionPlan);
  const phase22Diagnostics = buildPhase22ResolutionDiagnostics(phase22ResolutionResult);
  const phase22ExportEnvelope = buildPhase22ExportEnvelope(phase22Diagnostics);
  const phase23MaterialPlan = buildPhase23MaterialPlan(phase22ExportEnvelope);
  const phase23MaterialResult = runPhase23Material(phase23MaterialPlan);
  const phase23Diagnostics = buildPhase23MaterialDiagnostics(phase23MaterialResult);
  const phase23ExportEnvelope = buildPhase23ExportEnvelope(phase23Diagnostics);
  const phase24ActivationPlan = buildPhase24ActivationPlan(phase23ExportEnvelope);
  const phase24ActivationResult = runPhase24Activation(phase24ActivationPlan);
  const phase24Diagnostics = buildPhase24ActivationDiagnostics(phase24ActivationResult);
  const phase24ExportEnvelope = buildPhase24ExportEnvelope(phase24Diagnostics);
  const phase25ProjectionPlan = buildPhase25ProjectionPlan(phase24ExportEnvelope);
  const phase25ProjectionResult = runPhase25Projection(phase25ProjectionPlan);
  const phase25Diagnostics = buildPhase25ProjectionDiagnostics(phase25ProjectionResult);
  const phase25ExportEnvelope = buildPhase25ExportEnvelope(phase25Diagnostics);
  const phase26TranslationPlan = buildPhase26TranslationPlan(phase25ExportEnvelope);
  const phase26TranslationResult = runPhase26Translation(phase26TranslationPlan);
  const phase26Diagnostics = buildPhase26TranslationDiagnostics(phase26TranslationResult);
  const phase26ExportEnvelope = buildPhase26ExportEnvelope(phase26Diagnostics);
  const phase27RenderingPlan = buildPhase27RenderingPlan(phase26ExportEnvelope);
  const phase27RenderingResult = runPhase27Rendering(phase27RenderingPlan);
  const phase27Diagnostics = buildPhase27RenderingDiagnostics(phase27RenderingResult);
  const phase27ExportEnvelope = buildPhase27ExportEnvelope(phase27Diagnostics);
  const phase28SerializationPlan = buildPhase28SerializationPlan(phase27ExportEnvelope);
  const phase28SerializationResult = runPhase28Serialization(phase28SerializationPlan);
  const phase28Diagnostics = buildPhase28SerializationDiagnostics(phase28SerializationResult);
  const phase28ExportEnvelope = buildPhase28ExportEnvelope(phase28Diagnostics);
  const phase29TransmissionPlan = buildPhase29TransmissionPlan(phase28ExportEnvelope);
  const phase29TransmissionResult = runPhase29Transmission(phase29TransmissionPlan);
  const phase29Diagnostics = buildPhase29TransmissionDiagnostics(phase29TransmissionResult);
  const phase29ExportEnvelope = buildPhase29ExportEnvelope(phase29Diagnostics);
  const phase30FinalizationPlan = buildPhase30FinalizationPlan(phase29ExportEnvelope);
  const phase30FinalizationResult = runPhase30Finalization(phase30FinalizationPlan);
  const phase30Diagnostics = buildPhase30FinalizationDiagnostics(phase30FinalizationResult);
  const phase30ExportEnvelope = buildPhase30ExportEnvelope(phase30Diagnostics);

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
            <select
              value={profile}
              onChange={(event) => {
                const nextProfile = event.target.value === "personal" ? "personal" : "public";
                setProfile(nextProfile);
                emitStudioTelemetry("studio.profile.changed", {
                  profile: nextProfile,
                });
              }}
            >
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
              onChange={(event) => {
                const nextCompartmentIndex = clampStudioCompartmentIndex(Number(event.target.value || 5));
                setCompartmentIndex(nextCompartmentIndex);
                emitStudioTelemetry("studio.compartment.input.changed", {
                  compartmentIndex: nextCompartmentIndex,
                });
              }}
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

      <section className="panel studio-panel phase18-ebook-placeholder" aria-label="Studio E-Book Phase 18 placeholder">
        <h3>Phase 18 E-Book Hooks</h3>
        <p>Placeholder integration only. No routing or behavioral wiring.</p>
        <ul>
          {phase18EBookSurfaces.map((surface) => (
            <li key={surface}>Studio surface: {surface}</li>
          ))}
        </ul>
      </section>

      <section
        className="panel studio-panel phase18-export-placeholder"
        aria-label="Studio Phase 18 export placeholder"
      >
        <h3>Phase 18 Export Hook</h3>
        <p>Placeholder integration only. No routing, no behavior, no AV playback.</p>
        <p>Export ID: {phase18StudioExportEnvelope.exportId}</p>
      </section>

      <section
        className="panel studio-panel phase18-inspector"
        aria-label="Studio Phase 18 inspector"
      >
        <h3>Phase 18 Inspector</h3>
        <p>Mode: {phase18StudioExportEnvelope.typeCheck.orchestrator.root.mode}</p>
        <p>Has Audio: {phase18StudioExportEnvelope.typeCheck.orchestrator.root.hasAudio ? "yes" : "no"}</p>
        <p>Has AV: {phase18StudioExportEnvelope.typeCheck.orchestrator.root.hasAV ? "yes" : "no"}</p>
        <p>Export ID: {phase18StudioExportEnvelope.exportId}</p>
      </section>

      <section
        className="panel studio-panel phase18-debug-console"
        aria-label="Studio Phase 18 debug console"
      >
        <h3>Phase 18 Debug Console</h3>
        <p>Read-only diagnostic payload for deterministic Phase 18 export envelope.</p>
        <details>
          <summary>Show Export Envelope JSON</summary>
          <pre>{JSON.stringify(phase18StudioExportEnvelope, null, 2)}</pre>
        </details>
      </section>

      <section
        className="panel studio-panel phase18-validator"
        aria-label="Studio Phase 18 envelope validator"
      >
        <h3>Phase 18 Envelope Validator</h3>
        <p>
          Envelope OK: {phase18StudioExportEnvelope &&
          phase18StudioExportEnvelope.typeCheck &&
          phase18StudioExportEnvelope.typeCheck.orchestrator &&
          phase18StudioExportEnvelope.typeCheck.orchestrator.root
            ? "yes"
            : "no"}
        </p>
        <p>
          Aggregate OK: {phase18StudioExportEnvelope.typeCheck.orchestrator.root.module.envelope.aggregate ? "yes" : "no"}
        </p>
        <p>
          Present Root OK: {phase18StudioExportEnvelope.typeCheck.orchestrator.root.module.envelope.aggregate.presentRoot ? "yes" : "no"}
        </p>
        <p>AV Root OK: {phase18StudioExportEnvelope.typeCheck.orchestrator.root.module.envelope.aggregate.avRoot ? "yes" : "no"}</p>
      </section>

      <section
        className="panel studio-panel phase18-runtime-preview"
        aria-label="Studio Phase 18 runtime preview"
      >
        <h3>Phase 18 Runtime Preview</h3>
        <p>Runtime Mode: {phase18StudioExportEnvelope.typeCheck.orchestrator.root.mode}</p>
        <p>Audio Capability: {phase18StudioExportEnvelope.typeCheck.orchestrator.root.hasAudio ? "enabled" : "disabled"}</p>
        <p>AV Capability: {phase18StudioExportEnvelope.typeCheck.orchestrator.root.hasAV ? "enabled" : "disabled"}</p>
        <p>This is a non-behavioral preview. No playback, no routing, no engine execution.</p>
      </section>

      <section className="panel phase19-runtime-panel" aria-label="Phase 19 runtime placeholder">
        <h3>Phase 19 Runtime Envelope</h3>
        <p>Envelope ID: {phase19RuntimeEnvelope.envelopeId}</p>
        <p>Placement ID: {phase19Placement.placementId}</p>
        <p>Mode: {phase19RuntimeEnvelope.mode}</p>
        <p>Region: {phase19Placement.region}</p>
      </section>

      <section className="panel phase19-export-panel" aria-label="Phase 19 export envelope">
        <h3>Phase 19 Export Envelope</h3>
        <p>Export ID: {phase19ExportEnvelope.exportId}</p>
        <p>TypeCheck ID: {phase19TypeCheck.typeCheckId}</p>
        <p>Orchestrator ID: {phase19Orchestrator.orchestratorId}</p>
        <p>Logic Spine ID: {phase19LogicSpine.spineId}</p>
        <p>Mode: {phase19ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase20-export-panel" aria-label="Phase 20 export envelope">
        <h3>Phase 20 Export Envelope</h3>
        <p>Export ID: {phase20ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase20Diagnostics.diagnosticsId}</p>
        <p>Dry-Run Result ID: {phase20DryRunResult.resultId}</p>
        <p>Runtime Plan ID: {phase20RuntimePlan.planId}</p>
        <p>Mode: {phase20ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase21-export-panel" aria-label="Phase 21 export envelope">
        <h3>Phase 21 Export Envelope</h3>
        <p>Export ID: {phase21ExportEnvelope.exportId}</p>
        <p>Pre-Router ID: {phase21PreRouter.preRouterId}</p>
        <p>Selected Lane: {phase21PreRouter.selectedLane}</p>
        <p>Runtime Lanes ID: {phase21RuntimeLanes.lanesId}</p>
        <p>Runtime Intent ID: {phase21RuntimeIntent.intentId}</p>
        <p>Mode: {phase21ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase22-export-panel" aria-label="Phase 22 export envelope">
        <h3>Phase 22 Export Envelope</h3>
        <p>Export ID: {phase22ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase22Diagnostics.diagnosticsId}</p>
        <p>Resolution Result ID: {phase22ResolutionResult.resultId}</p>
        <p>Resolved Lane: {phase22ResolutionResult.resolvedLane}</p>
        <p>Resolution Plan ID: {phase22ResolutionPlan.planId}</p>
        <p>Mode: {phase22ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase23-export-panel" aria-label="Phase 23 export envelope">
        <h3>Phase 23 Export Envelope</h3>
        <p>Export ID: {phase23ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase23Diagnostics.diagnosticsId}</p>
        <p>Material Result ID: {phase23MaterialResult.resultId}</p>
        <p>Materialized Lane: {phase23MaterialResult.materializedLane}</p>
        <p>Material Plan ID: {phase23MaterialPlan.planId}</p>
        <p>Mode: {phase23ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase24-export-panel" aria-label="Phase 24 export envelope">
        <h3>Phase 24 Export Envelope</h3>
        <p>Export ID: {phase24ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase24Diagnostics.diagnosticsId}</p>
        <p>Activation Result ID: {phase24ActivationResult.resultId}</p>
        <p>Activated Lane: {phase24ActivationResult.activatedLane}</p>
        <p>Activation Plan ID: {phase24ActivationPlan.planId}</p>
        <p>Mode: {phase24ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase25-export-panel" aria-label="Phase 25 export envelope">
        <h3>Phase 25 Export Envelope</h3>
        <p>Export ID: {phase25ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase25Diagnostics.diagnosticsId}</p>
        <p>Projection Result ID: {phase25ProjectionResult.resultId}</p>
        <p>Projected Lane: {phase25ProjectionResult.projectedLane}</p>
        <p>Projection Plan ID: {phase25ProjectionPlan.planId}</p>
        <p>Mode: {phase25ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase26-export-panel" aria-label="Phase 26 export envelope">
        <h3>Phase 26 Export Envelope</h3>
        <p>Export ID: {phase26ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase26Diagnostics.diagnosticsId}</p>
        <p>Translation Result ID: {phase26TranslationResult.resultId}</p>
        <p>Translated Lane: {phase26TranslationResult.translatedLane}</p>
        <p>Translation Plan ID: {phase26TranslationPlan.planId}</p>
        <p>Mode: {phase26ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase27-export-panel" aria-label="Phase 27 export envelope">
        <h3>Phase 27 Export Envelope</h3>
        <p>Export ID: {phase27ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase27Diagnostics.diagnosticsId}</p>
        <p>Rendering Result ID: {phase27RenderingResult.resultId}</p>
        <p>Rendered Lane: {phase27RenderingResult.renderedLane}</p>
        <p>Rendering Plan ID: {phase27RenderingPlan.planId}</p>
        <p>Mode: {phase27ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase28-export-panel" aria-label="Phase 28 export envelope">
        <h3>Phase 28 Export Envelope</h3>
        <p>Export ID: {phase28ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase28Diagnostics.diagnosticsId}</p>
        <p>Serialization Result ID: {phase28SerializationResult.resultId}</p>
        <p>Serialized Lane: {phase28SerializationResult.serializedLane}</p>
        <p>Serialization Plan ID: {phase28SerializationPlan.planId}</p>
        <p>Mode: {phase28ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase29-export-panel" aria-label="Phase 29 export envelope">
        <h3>Phase 29 Export Envelope</h3>
        <p>Export ID: {phase29ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase29Diagnostics.diagnosticsId}</p>
        <p>Transmission Result ID: {phase29TransmissionResult.resultId}</p>
        <p>Transmitted Lane: {phase29TransmissionResult.transmittedLane}</p>
        <p>Transmission Plan ID: {phase29TransmissionPlan.planId}</p>
        <p>Mode: {phase29ExportEnvelope.mode}</p>
      </section>

      <section className="panel phase30-export-panel" aria-label="Phase 30 export envelope">
        <h3>Phase 30 Export Envelope</h3>
        <p>Export ID: {phase30ExportEnvelope.exportId}</p>
        <p>Diagnostics ID: {phase30Diagnostics.diagnosticsId}</p>
        <p>Finalization Result ID: {phase30FinalizationResult.resultId}</p>
        <p>Finalized Lane: {phase30FinalizationResult.finalizedLane}</p>
        <p>Finalization Plan ID: {phase30FinalizationPlan.planId}</p>
        <p>Mode: {phase30ExportEnvelope.mode}</p>
      </section>
    </section>
  );
}
