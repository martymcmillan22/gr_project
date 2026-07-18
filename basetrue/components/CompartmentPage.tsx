import { useEffect, useMemo, useState } from "react";
import { getPhaseColor, getTemporalGroup, getViewType } from "../logic/temporalRouting";
import {
  canCreateIdea,
  canCreateProject,
  canFormSeed,
  canRouteRRInPipeline,
  canUseQPUTower,
  canViewRRInPipeline,
} from "../logic/pipelineLogic";
import { getTierConfig, hasQPU } from "../logic/tierLogic";
import ArtifactTagDisplay from "./ArtifactTagDisplay";
import PhaseSectionCreate from "./PhaseSectionCreate";
import PhaseSectionPost from "./PhaseSectionPost";
import PhaseSectionWork from "./PhaseSectionWork";
import { emitDeterministicTelemetry, incrementDeterministicMetric } from "../../frontend_homepage/src/ui/deterministicTelemetry";
import type {
  CompartmentViewMode,
  IdeaRecord,
  PipelineStage,
  ProfileKind,
  ProjectRecord,
  SeedRecord,
  Tier,
} from "../types";

interface CompartmentPageProps {
  profile: ProfileKind;
  name: string;
  index: number;
  tier: Tier;
  viewMode?: CompartmentViewMode;
}

export default function CompartmentPage(props: CompartmentPageProps) {
  const emitCompartmentTelemetry = (eventName: string, payload: Record<string, unknown> = {}) => {
    emitDeterministicTelemetry({
      eventName,
      tier: props.tier,
      surface: "compartment",
      payload,
    });
  };

  const [viewMode, setViewMode] = useState<CompartmentViewMode>(props.viewMode || "dashboard");
  const isDashboard = viewMode === "dashboard";
  const group = getTemporalGroup(props.index);
  const view = getViewType(group);
  const tierCfg = getTierConfig(props.tier);
  const [activeStage, setActiveStage] = useState<PipelineStage>("idea");
  const [idea, setIdea] = useState<IdeaRecord | null>(null);
  const [seed, setSeed] = useState<SeedRecord | null>(null);
  const [project, setProject] = useState<ProjectRecord | null>(null);

  const gateState = useMemo(() => {
    return {
      canIdea: canCreateIdea(props.tier),
      canSeed: canFormSeed(props.tier) && Boolean(idea),
      canProject: canCreateProject(props.tier) && Boolean(seed),
      canWork: Boolean(project),
    };
  }, [idea, project, props.tier, seed]);

  const handleIdeaCreate = (nextIdea: IdeaRecord) => {
    setIdea(nextIdea);
    setSeed(null);
    setProject(null);
    setActiveStage("seed");
    emitCompartmentTelemetry("compartment.idea.created", {
      index: props.index,
      profile: props.profile,
    });
    incrementDeterministicMetric("compartment.idea.created", {
      tier: props.tier,
    });
  };

  const handleSeedCreate = (nextSeed: SeedRecord) => {
    setSeed(nextSeed);
    setProject(null);
    setActiveStage("project");
    emitCompartmentTelemetry("compartment.seed.created", {
      index: props.index,
      profile: props.profile,
    });
    incrementDeterministicMetric("compartment.seed.created", {
      tier: props.tier,
    });
  };

  const handleProjectCreate = (nextProject: ProjectRecord) => {
    setProject(nextProject);
    setActiveStage("work");
    emitCompartmentTelemetry("compartment.project.created", {
      projectId: nextProject.project_id,
      index: props.index,
    });
    incrementDeterministicMetric("compartment.project.created", {
      tier: props.tier,
    });
  };

  const handleProjectUpdate = (nextProject: ProjectRecord) => {
    setProject(nextProject);
    emitCompartmentTelemetry("compartment.project.updated", {
      projectId: nextProject.project_id,
    });
  };

  useEffect(() => {
    emitCompartmentTelemetry("compartment.loaded", {
      profile: props.profile,
      index: props.index,
      tier: props.tier,
    });
    incrementDeterministicMetric("compartment.loaded", {
      tier: props.tier,
    });
    // Deterministic mount telemetry is intentionally emitted once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    emitCompartmentTelemetry("compartment.view.mode.changed", {
      viewMode,
      dashboard: isDashboard,
    });
  }, [isDashboard, viewMode]);

  useEffect(() => {
    emitCompartmentTelemetry("compartment.stage.changed", {
      stage: activeStage,
      group,
      view,
    });
  }, [activeStage, group, view]);

  useEffect(() => {
    emitCompartmentTelemetry("compartment.gate.snapshot", {
      canIdea: gateState.canIdea,
      canSeed: gateState.canSeed,
      canProject: gateState.canProject,
      canWork: gateState.canWork,
    });
  }, [gateState.canIdea, gateState.canProject, gateState.canSeed, gateState.canWork]);

  return (
    <div className="compartment-page" data-tier={props.tier}>
      <header>
        <h1>
          {props.profile === "public" ? "Public" : "Personal"} - {props.name}
        </h1>
        <span className="tier-badge">{props.tier}</span>
        <span className="temporal-badge">{group}</span>
        <span className="commands-badge">Commands: {tierCfg.commands.join(", ")}</span>
      </header>

      <section className="pipeline-navigation">
        <p>{isDashboard ? "Compartment Dashboard" : "Seed to Project Pipeline"}</p>
        <p>Compartment policy: read-only artifact lens. Create runs in Corporation, Post in Museum, Work in Garden.</p>
        <p>
          Studio workspace: <a href="/basetrue/studio">open dedicated Studio workstation</a>
        </p>
        <div className="action-grid" role="group" aria-label="Compartment mode">
          <button
            type="button"
            onClick={() => {
              setViewMode("dashboard");
              emitCompartmentTelemetry("compartment.view.mode.select", {
                targetMode: "dashboard",
              });
            }}
            aria-pressed={isDashboard}
            aria-current={isDashboard ? "step" : undefined}
            disabled={isDashboard}
          >
            Dashboard Mode
          </button>
          <button
            type="button"
            onClick={() => {
              setViewMode("pipeline");
              emitCompartmentTelemetry("compartment.view.mode.select", {
                targetMode: "pipeline",
              });
            }}
            aria-pressed={!isDashboard}
            aria-current={!isDashboard ? "step" : undefined}
            disabled={!isDashboard}
          >
            Pipeline Mode
          </button>
        </div>
        {!isDashboard ? (
          <div className="action-grid">
            <button
              type="button"
              disabled={!gateState.canIdea}
              aria-current={activeStage === "idea" ? "step" : undefined}
              onClick={() => {
                setActiveStage("idea");
                emitCompartmentTelemetry("compartment.stage.select", {
                  stage: "idea",
                });
              }}
            >
              Create Idea
            </button>
            <button
              type="button"
              disabled={!gateState.canSeed}
              aria-current={activeStage === "seed" ? "step" : undefined}
              onClick={() => {
                setActiveStage("seed");
                emitCompartmentTelemetry("compartment.stage.select", {
                  stage: "seed",
                });
              }}
            >
              Form Seed
            </button>
            <button
              type="button"
              disabled={!gateState.canProject}
              aria-current={activeStage === "project" ? "step" : undefined}
              onClick={() => {
                setActiveStage("project");
                emitCompartmentTelemetry("compartment.stage.select", {
                  stage: "project",
                });
              }}
            >
              Activate Project
            </button>
            <button
              type="button"
              disabled={!gateState.canWork}
              aria-current={activeStage === "work" ? "step" : undefined}
              onClick={() => {
                setActiveStage("work");
                emitCompartmentTelemetry("compartment.stage.select", {
                  stage: "work",
                });
              }}
            >
              Enter Work Phase
            </button>
          </div>
        ) : null}
        <p role="status" aria-live="polite" aria-atomic="true">
          Stage: {isDashboard ? "dashboard" : activeStage} | RR pipeline: {canRouteRRInPipeline(props.tier) ? "enabled" : "disabled"} | QPU: {hasQPU(props.tier) ? "enabled" : "disabled"} | Tower: {canUseQPUTower(props.tier) ? "enabled" : "disabled"}
        </p>
        <ArtifactTagDisplay label="Lens Idea" tags={idea?.artifact_tags} />
        <ArtifactTagDisplay label="Lens Seed" tags={seed?.artifact_tags} />
        <ArtifactTagDisplay label="Lens Project" tags={project?.artifact_tags} />
        <ArtifactTagDisplay label="Lens Work Artifact" tags={project?.work_artifacts?.[0]?.artifact_tags} />
      </section>

      {isDashboard || activeStage === "idea" || activeStage === "seed" ? (
        <PhaseSectionCreate
          profile={props.profile}
          compartmentName={props.name}
          compartmentIndex={props.index}
          tier={props.tier}
          temporalGroup={group}
          view={view}
          color={getPhaseColor("create", group)}
          showRR={canViewRRInPipeline(props.tier)}
          viewMode={viewMode}
          idea={idea}
          seed={seed}
          onIdeaCreate={handleIdeaCreate}
          onSeedCreate={handleSeedCreate}
        />
      ) : null}

      {isDashboard || activeStage === "project" ? (
        <PhaseSectionPost
          profile={props.profile}
          compartmentName={props.name}
          compartmentIndex={props.index}
          tier={props.tier}
          temporalGroup={group}
          view={view}
          color={getPhaseColor("post", group)}
          showQPU={hasQPU(props.tier)}
          viewMode={viewMode}
          seed={seed}
          project={project}
          onProjectCreate={handleProjectCreate}
        />
      ) : null}

      {isDashboard || activeStage === "work" ? (
        <PhaseSectionWork
          profile={props.profile}
          compartmentName={props.name}
          compartmentIndex={props.index}
          tier={props.tier}
          temporalGroup={group}
          view={view}
          color={getPhaseColor("work", group)}
          showQPUTower={canUseQPUTower(props.tier)}
          viewMode={viewMode}
          project={project}
          onProjectUpdate={handleProjectUpdate}
        />
      ) : null}
    </div>
  );
}
