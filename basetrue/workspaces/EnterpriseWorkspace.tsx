import { useEffect, useMemo, useState } from "react";
import btAnchor from "../anchors/bt_anchor.json";
import ArtifactTagDisplay from "../components/ArtifactTagDisplay";
import QPUTower from "../components/QPUTower";
import TowerExecutionTimeline from "../components/TowerExecutionTimeline";
import { emitDeterministicTelemetry, incrementDeterministicMetric } from "../../frontend_homepage/src/ui/deterministicTelemetry";
import {
  canUseGovernedApplyMode,
  getGovernanceProfilesForTier,
  isGovernanceProfileAllowed,
} from "../logic/pipelineLogic";
import { buildArtifactTags } from "../logic/artifactTagging";
import { buildQpuFloorPlans, buildQpuPlan } from "../logic/qpuEngine";
import { buildRrSelection, buildSeedRoute } from "../logic/rrRouter";
import { getTemporalGroup, getViewType } from "../logic/temporalRouting";
import { buildPhase18PlaceholderExportEnvelope } from "../logic/ebooks/phase18/ebookPhase18Placeholder";
import { buildPhase19ExportEnvelope } from "../logic/ebooks/phase19/ebookPhase19Export";
import { buildPhase19LogicSpine } from "../logic/ebooks/phase19/ebookPhase19LogicSpine";
import { buildPhase19Orchestrator } from "../logic/ebooks/phase19/ebookPhase19Orchestrator";
import { buildPhase19TypeCheck } from "../logic/ebooks/phase19/ebookPhase19TypeCheck";
import type { EBookPhase19Placement } from "../logic/ebooks/phase19/ebookPhase19Placement";
import type { EBookPhase19RuntimeEnvelope } from "../logic/ebooks/phase19/ebookPhase19Envelope";
import {
  STUDIO_ENTERPRISE_GARDEN_MAINTENANCE,
  STUDIO_ENTERPRISE_GUIDED_CHAIN,
  STUDIO_ENTERPRISE_TOWER,
} from "../logic/baseTrueConstants";
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
  ArtifactTags,
  EnterpriseAccessTier,
  GovernanceProfile,
  ProjectRecord,
  QpuFloorPlan,
  TemporalGroup,
} from "../types";

type ExecutionState = "planned" | "in_progress" | "completed";

interface EnterpriseWorkspaceProps {
  accessTier?: EnterpriseAccessTier;
  profile?: "public" | "personal";
}

const TEMPORAL_FLOOR_PURPOSE: Record<TemporalGroup, string> = {
  past: "archival/reflection",
  present_past: "refinement",
  present_future: "planning",
  future: "execution",
};

const ENTERPRISE_CHAIN_HINTS: Record<(typeof STUDIO_ENTERPRISE_GUIDED_CHAIN)[number], string> = {
  Monuments: "Prepare monument-safe artifacts before transactional handoff.",
  Checkout: "Validate governed release packets and execution readiness.",
  Surveys: "Collect semantic signal and confidence feedback.",
  Polls: "Aggregate comparative outcomes for routing decisions.",
};

function buildEnterpriseProjects(profile: "public" | "personal"): ProjectRecord[] {
  const planIndices = [9, 10, 11, 12];
  const quadrants = ["language", "arts", "math", "science"] as const;

  return planIndices.map((compartmentIndex, offset) => {
    const temporalGroup = getTemporalGroup(compartmentIndex);
    const rrSelection = buildRrSelection({
      quadrant: quadrants[offset % 4],
      subnode: (["A", "B", "C", "D"] as const)[offset % 4],
      logicMode: (["hierarchical", "network", "object", "relational"] as const)[offset % 4],
      temporalGroup,
    });
    const qpuPlan = buildQpuPlan({
      tier: "enterprise",
      compartmentIndex,
      temporalGroup,
      rrSelection,
      workspaceMode: "enterprise",
    });

    const compartmentName = btAnchor.compartments[profile][compartmentIndex - 1] || `Enterprise-${compartmentIndex}`;

    return {
      project_id: `enterprise-project-${compartmentIndex}`,
      seed_id: `enterprise-seed-${compartmentIndex}`,
      qpu_allocation: qpuPlan.adjusted_count,
      qpu_plan: qpuPlan,
      temporal_group: temporalGroup,
      phase: "work",
      tier: "enterprise",
      work_state: "planned",
      tower_level: Math.max(1, compartmentIndex - 4),
      artifacts: [
        `enterprise.tower.${compartmentIndex}`,
        `temporal.${temporalGroup}`,
        `rr.${buildSeedRoute({
          quadrant: rrSelection.quadrant,
          subnode: rrSelection.subnode,
          logicMode: rrSelection.logic_mode,
          temporalGroup: rrSelection.temporal_group,
        })}`,
      ],
      geometry_mode: "architectural",
      artifact_tags: buildArtifactTags({
        profile,
        compartmentName,
        compartmentIndex,
        phase: "post",
        temporalGroup,
        tier: "enterprise",
        rrSelection,
        qpuPlanId: qpuPlan.qpu_plan_id,
        workspaceMode: "enterprise",
      }),
    };
  });
}

function cycleExecutionState(state: ExecutionState): ExecutionState {
  if (state === "planned") {
    return "in_progress";
  }
  if (state === "in_progress") {
    return "completed";
  }
  return "planned";
}

export default function EnterpriseWorkspace({ accessTier = "enterprise", profile = "public" }: EnterpriseWorkspaceProps) {
  if (accessTier !== "enterprise") {
    return (
      <section className="panel">
        <h2>Enterprise Workspace Access Required</h2>
        <p className="status-line">Only tier enterprise can access this workspace.</p>
      </section>
    );
  }

  const [projects] = useState<ProjectRecord[]>(() => buildEnterpriseProjects(profile));
  const [activeProjectId, setActiveProjectId] = useState<string>(projects[0]?.project_id || "");
  const [activeFloor, setActiveFloor] = useState<number>(1);
  const [hoveredFloor, setHoveredFloor] = useState<number | null>(null);
  const [executionStateMap, setExecutionStateMap] = useState<Record<string, ExecutionState>>({});

  const emitEnterpriseTelemetry = (eventName: string, payload: Record<string, unknown> = {}) => {
    emitDeterministicTelemetry({
      eventName,
      tier: "enterprise",
      surface: "workspace",
      payload,
    });
  };

  const activeProject = useMemo(
    () => projects.find((project) => project.project_id === activeProjectId) || projects[0] || null,
    [activeProjectId, projects],
  );

  const floorPlans = useMemo<QpuFloorPlan[]>(
    () => (activeProject ? buildQpuFloorPlans(activeProject.qpu_plan) : []),
    [activeProject],
  );

  const effectiveFloor = hoveredFloor || activeFloor;
  const governanceProfiles = useMemo(() => getGovernanceProfilesForTier("enterprise"), []);
  const canRunGovernedApply = useMemo(() => canUseGovernedApplyMode("enterprise"), []);
  const temporalOwner = useMemo(() => {
    const group = activeProject?.temporal_group;
    if (!group) {
      return "unassigned";
    }
    if (group === "past" || group === "present_past") {
      return "QC";
    }
    if (group === "present_future" || group === "future") {
      return "QA";
    }
    return "unassigned";
  }, [activeProject?.temporal_group]);
  const activeZone = useMemo(() => {
    const floorsPerZone = STUDIO_ENTERPRISE_TOWER.floors_per_zone;
    return Math.max(1, Math.min(STUDIO_ENTERPRISE_TOWER.zones, Math.ceil(effectiveFloor / floorsPerZone)));
  }, [effectiveFloor]);
  const guidedChainIndex = useMemo(
    () => Math.max(0, Math.min(STUDIO_ENTERPRISE_GUIDED_CHAIN.length - 1, activeZone - 1)),
    [activeZone],
  );
  const activeGardenRoute = useMemo(
    () => STUDIO_ENTERPRISE_GARDEN_MAINTENANCE[(activeZone - 1) % STUDIO_ENTERPRISE_GARDEN_MAINTENANCE.length],
    [activeZone],
  );
  const profileBadges = useMemo(() => {
    return governanceProfiles.map((profileName: GovernanceProfile) => ({
      profile: profileName,
      allowed: isGovernanceProfileAllowed("enterprise", profileName),
    }));
  }, [governanceProfiles]);
  const activeFloorPlan = useMemo(
    () => floorPlans.find((floor) => floor.floor === effectiveFloor) || floorPlans[0] || null,
    [effectiveFloor, floorPlans],
  );

  const floorTag = useMemo<ArtifactTags | null>(() => {
    if (!activeProject || !activeFloorPlan) {
      return null;
    }

    return buildArtifactTags({
      profile: activeProject.artifact_tags.profile,
      compartmentName: activeProject.artifact_tags.compartment_name,
      compartmentIndex: activeProject.artifact_tags.compartment_index,
      phase: "work",
      temporalGroup: activeProject.temporal_group,
      tier: activeProject.tier,
      rrSelection: activeProject.qpu_plan.rr_influence,
      qpuPlanId: activeProject.qpu_plan.qpu_plan_id,
      floor: activeFloorPlan.floor,
      workspaceMode: "enterprise",
    });
  }, [activeFloorPlan, activeProject]);

  const rrRoute = useMemo(() => {
    if (!activeProject?.qpu_plan.rr_influence) {
      return "none";
    }
    const rr = activeProject.qpu_plan.rr_influence;
    return `${rr.quadrant}.${rr.subnode}.${rr.logic_mode}.${rr.temporal_group}`;
  }, [activeProject?.qpu_plan.rr_influence]);

  const towerSummary = useMemo(() => {
    if (!activeProject) {
      return "none";
    }
    return activeProject.qpu_plan.slices.map((slice) => `${slice.slice}:${slice.count}`).join(" | ");
  }, [activeProject]);

  const hoveredFloorSummary = useMemo(() => {
    if (!hoveredFloor) {
      return null;
    }
    const plan = floorPlans.find((floor) => floor.floor === hoveredFloor);
    if (!plan) {
      return null;
    }
    return `Floor ${hoveredFloor}: ${plan.total_count} units | ${plan.slices
      .map((slice) => `${slice.slice}:${slice.count}`)
      .join(" | ")}`;
  }, [floorPlans, hoveredFloor]);

  useEffect(() => {
    emitEnterpriseTelemetry("enterprise.workspace.loaded", {
      profile,
      projectId: activeProject?.project_id || "none",
    });
    incrementDeterministicMetric("enterprise.workspace.loaded", {
      tier: "enterprise",
    });
    // Deterministic mount telemetry is intentionally emitted once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    emitEnterpriseTelemetry("enterprise.project.changed", {
      projectId: activeProject?.project_id || "none",
      temporalGroup: activeProject?.temporal_group || "none",
    });
  }, [activeProject?.project_id, activeProject?.temporal_group]);

  useEffect(() => {
    emitEnterpriseTelemetry("enterprise.floor.changed", {
      activeFloor,
      effectiveFloor,
      hoveredFloor: hoveredFloor || 0,
    });
  }, [activeFloor, effectiveFloor, hoveredFloor]);

  useEffect(() => {
    emitEnterpriseTelemetry("enterprise.zone.changed", {
      activeZone,
      guidedChainIndex,
      gardenRoute: activeGardenRoute,
    });
  }, [activeGardenRoute, activeZone, guidedChainIndex]);

  const phase18EBookHooks = ["present", "qpu narrative"] as const;
  const phase18EnterpriseExportEnvelope = buildPhase18PlaceholderExportEnvelope("enterprise");
  const phase19RuntimeEnvelope: EBookPhase19RuntimeEnvelope = {
    generatedAt: "phase19-placeholder",
    envelopeId: "phase19-runtime-envelope-placeholder",
    phase18: phase18EnterpriseExportEnvelope,
    mode: "static",
  };
  const phase19Placement: EBookPhase19Placement = {
    generatedAt: "phase19-placeholder",
    placementId: "phase19-placement-placeholder",
    runtimeEnvelopeId: phase19RuntimeEnvelope.envelopeId,
    region: "enterprise",
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
    <section className="enterprise-workspace">
      <header className="panel enterprise-header-panel">
        <p className="eyebrow">BaseTrue Enterprise Workspace</p>
        <h2>Tower Control Room</h2>
        <div className="enterprise-header-badge-row">
          <span className="tier-badge">tier enterprise</span>
          <span className="temporal-badge">workspace enterprise</span>
          <span className="commands-badge">project {activeProject?.project_id || "none"}</span>
          <span className="commands-badge">tower height {activeProject?.qpu_plan.tower_floors || 0}</span>
          <span className="commands-badge">active floor {effectiveFloor || "-"}</span>
        </div>
        <p className="status-line enterprise-status-line">
          Full enterprise orchestration across all tower floors. Temporal view: {activeProject?.temporal_group || "-"} ({
          activeProject ? TEMPORAL_FLOOR_PURPOSE[activeProject.temporal_group] : "-"
          })
        </p>
        <p className="status-line enterprise-status-line">
          Governance profiles: {governanceProfiles.join(", ")} | Temporal overlay owner: {temporalOwner} | Active zone: {activeZone}
        </p>
        <p className="status-line enterprise-status-line">
          Garden maintenance route: {activeGardenRoute} | Guided chain: {STUDIO_ENTERPRISE_GUIDED_CHAIN.join(" -> ")}
        </p>

        <div className="enterprise-summary-grid" role="list">
          <article className="enterprise-summary-card" role="listitem">
            <h4>Active Floor Context</h4>
            <p className="enterprise-summary-keyline">Floor {effectiveFloor || "-"}</p>
            <p className="enterprise-summary-detail">Zone {activeZone} · Route {rrRoute}</p>
          </article>
          <article className="enterprise-summary-card" role="listitem">
            <h4>Zone & Garden Path</h4>
            <p className="enterprise-summary-keyline">Zone {activeZone}</p>
            <p className="enterprise-summary-detail">Garden route: {activeGardenRoute}</p>
          </article>
          <article className="enterprise-summary-card" role="listitem">
            <h4>Temporal Owner</h4>
            <p className={`enterprise-owner-pill owner-${temporalOwner.toLowerCase()}`}>{temporalOwner}</p>
            <p className="enterprise-summary-detail">Owner derived from temporal group governance.</p>
          </article>
        </div>

        <div className="enterprise-zone-rail" aria-label="Enterprise tower zones" role="list">
          {Array.from({ length: STUDIO_ENTERPRISE_TOWER.zones }, (_, index) => {
            const zone = index + 1;
            const floorStart = (zone - 1) * STUDIO_ENTERPRISE_TOWER.floors_per_zone + 1;
            const floorEnd = zone * STUDIO_ENTERPRISE_TOWER.floors_per_zone;
            return (
              <span
                key={zone}
                className={`enterprise-zone-pill${zone === activeZone ? " is-active" : ""}`}
                role="listitem"
                aria-current={zone === activeZone ? "step" : undefined}
              >
                Zone {zone} · Floors {floorStart}-{floorEnd}
              </span>
            );
          })}
        </div>

        <section className="enterprise-chain-panel" aria-label="Monuments to Polls guided chain">
          <h4>Monuments -&gt; Checkout -&gt; Surveys -&gt; Polls</h4>
          <ol className="enterprise-chain-list">
            {STUDIO_ENTERPRISE_GUIDED_CHAIN.map((stage, index) => (
              <li key={stage} className={index === guidedChainIndex ? "is-active" : ""}>
                <strong>{stage}</strong>
                <span>{ENTERPRISE_CHAIN_HINTS[stage]}</span>
              </li>
            ))}
          </ol>
        </section>

        <div className="enterprise-badge-row">
          {profileBadges.map((item) => (
            <span key={item.profile} className={`commands-badge enterprise-badge ${item.allowed ? "is-allowed" : "is-blocked"}`}>
              {item.profile}:{item.allowed ? "allowed" : "blocked"}
            </span>
          ))}
          <span className={`commands-badge enterprise-badge ${canRunGovernedApply ? "is-allowed" : "is-blocked"}`}>
            governed apply:{canRunGovernedApply ? "enabled" : "disabled"}
          </span>
          <span className={`commands-badge enterprise-badge ${canRunGovernedApply ? "is-allowed" : "is-blocked"}`}>
            release workflows:{canRunGovernedApply ? "enabled" : "disabled"}
          </span>
        </div>

        <div className="enterprise-command-row">
          <button type="button" disabled={!canRunGovernedApply}>
            improve-all --apply
          </button>
          <button type="button" disabled={!canRunGovernedApply}>
            release --bump patch
          </button>
          <button type="button" disabled={!canRunGovernedApply}>
            release-notes
          </button>
        </div>
        <p className="status-line enterprise-status-line">RR route: {rrRoute} | QPU plan: {activeProject?.qpu_plan.qpu_plan_id || "none"}</p>
        <p className="status-line enterprise-status-line">Tower-wide slice summary: {towerSummary}</p>
        <ArtifactTagDisplay
          label="Enterprise Header Tags"
          tags={activeProject?.artifact_tags}
          workspaceMode="enterprise"
          semanticMix={activeProject?.qpu_plan.slices.map((slice) => `${slice.slice}:${slice.count}`)}
        />
      </header>

      <section className="panel enterprise-panel">
        <h3>1. Project Selection Panel</h3>
        <p className="status-line">Enterprise-eligible projects with deterministic tower plans.</p>
        <div className="action-grid">
          {projects.map((project) => (
            <button
              key={project.project_id}
              type="button"
              aria-pressed={project.project_id === activeProject?.project_id}
              onClick={() => {
                setActiveProjectId(project.project_id);
                setActiveFloor(1);
                setHoveredFloor(null);
                emitEnterpriseTelemetry("enterprise.project.selected", {
                  projectId: project.project_id,
                });
              }}
            >
              {project.project_id}
            </button>
          ))}
        </div>
        <ArtifactTagDisplay
          label="Selected Project Tags"
          tags={activeProject?.artifact_tags}
          workspaceMode="enterprise"
          semanticMix={activeProject?.qpu_plan.slices.map((slice) => `${slice.slice}:${slice.count}`)}
        />
      </section>

      <section className="panel enterprise-panel">
        <h3>2. Tower Overview Panel</h3>
        <p className="status-line">
          Full tower interaction with floor selection and hover summaries. View mode: {activeProject ? getViewType(activeProject.temporal_group) : "-"}
        </p>
        <div className="enterprise-tower-layout">
          <QPUTower
            compartmentIndex={activeProject?.artifact_tags.compartment_index || 9}
            project={activeProject}
            selectedFloor={effectiveFloor}
            onFloorSelect={(floor) => {
              setActiveFloor(floor);
              emitEnterpriseTelemetry("enterprise.tower.floor.selected", {
                floor,
              });
            }}
            onFloorHover={(floor) => {
              setHoveredFloor(floor);
              emitEnterpriseTelemetry("enterprise.tower.floor.hovered", {
                floor: floor || 0,
              });
            }}
            workspaceMode="enterprise"
            interactive={true}
          />
          <aside className="enterprise-tower-aside">
            <h4>Zone Snapshot</h4>
            <p className="status-line" role="status" aria-live="polite" aria-atomic="true">
              Zone {activeZone} governs floors around {effectiveFloor}.
            </p>
            <p className="status-line" role="status" aria-live="polite" aria-atomic="true">
              Garden route: {activeGardenRoute}
            </p>
            {hoveredFloorSummary ? (
              <p className="status-line" role="status" aria-live="polite" aria-atomic="true">
                Hover: {hoveredFloorSummary}
              </p>
            ) : (
              <p className="status-line" role="status" aria-live="polite" aria-atomic="true">
                Hover a floor for preview.
              </p>
            )}
          </aside>
        </div>
      </section>

      <section className="panel enterprise-panel">
        <h3>3. Floor Detail Panel</h3>
        {activeFloorPlan ? (
          <>
            <p className="status-line">
              Floor {activeFloorPlan.floor} | Units: {activeFloorPlan.total_count} | Temporal purpose: {TEMPORAL_FLOOR_PURPOSE[activeProject?.temporal_group || "past"]}
            </p>
            <p className="status-line">
              RR semantic breakdown: {activeProject?.qpu_plan.rr_influence?.quadrant || "-"}.
              {activeProject?.qpu_plan.rr_influence?.subnode || "-"}.
              {activeProject?.qpu_plan.rr_influence?.logic_mode || "-"}
            </p>
            <div className="enterprise-floor-slice-grid" role="list">
              {activeFloorPlan.slices.map((slice) => {
                const widthPct = activeFloorPlan.total_count > 0 ? Math.round((slice.count / activeFloorPlan.total_count) * 100) : 0;
                return (
                  <div key={`${activeFloorPlan.floor}-${slice.slice}`} className="enterprise-floor-slice-row" role="listitem">
                    <div className="enterprise-floor-slice-head">
                      <span>{slice.slice}</span>
                      <span>{slice.count}</span>
                    </div>
                    <div className="enterprise-floor-slice-track">
                      <div
                        className="enterprise-floor-slice-fill"
                        style={{
                          width: `${widthPct}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="status-line">
              Slice distribution: {activeFloorPlan.slices.map((slice) => `${slice.slice}:${slice.count}`).join(" | ")}
            </p>
            <ArtifactTagDisplay
              label="Floor Detail Tags"
              tags={floorTag}
              workspaceMode="enterprise"
              semanticMix={activeFloorPlan.slices.map((slice) => `${slice.slice}:${slice.count}`)}
            />
            <ul>
              {activeFloorPlan.steps.map((step) => (
                <li key={`${activeFloorPlan.floor}-${step}`}>
                  <strong>[{executionStateMap[`${activeProject?.project_id}-f${activeFloorPlan.floor}-s${activeFloorPlan.steps.indexOf(step) + 1}`] || "planned"}]</strong> {step}
                </li>
              ))}
            </ul>
            <div className="enterprise-floor-links">
              <a href="#enterprise-timeline">Jump to timeline</a>
              <a href="#enterprise-tower">Jump to tower</a>
            </div>
            <div className="enterprise-preview-grid">
              <strong>Floor-level artifact previews</strong>
              {activeFloorPlan.steps.slice(0, 3).map((step, index) => (
                <ArtifactTagDisplay
                  key={`${activeFloorPlan.floor}-preview-${index}`}
                  label={`Preview ${index + 1}`}
                  tags={
                    activeProject
                      ? buildArtifactTags({
                          profile: activeProject.artifact_tags.profile,
                          compartmentName: activeProject.artifact_tags.compartment_name,
                          compartmentIndex: activeProject.artifact_tags.compartment_index,
                          phase: "work",
                          temporalGroup: activeProject.temporal_group,
                          tier: activeProject.tier,
                          rrSelection: activeProject.qpu_plan.rr_influence,
                          qpuPlanId: activeProject.qpu_plan.qpu_plan_id,
                          floor: activeFloorPlan.floor,
                          workspaceMode: "enterprise",
                        })
                      : null
                  }
                  workspaceMode="enterprise"
                  semanticMix={[step]}
                />
              ))}
            </div>
          </>
        ) : (
          <p className="status-line">No floor details available.</p>
        )}
      </section>

      <section className="panel enterprise-panel" id="enterprise-timeline">
        <h3>4. Work Execution Panel</h3>
        <p className="status-line">Multi-floor execution list with floor, temporal, and RR quadrant filters.</p>
        <TowerExecutionTimeline
          activeProject={activeProject}
          qpuPlan={activeProject?.qpu_plan}
          workArtifacts={activeProject?.work_artifacts}
          activeFloor={effectiveFloor}
          executionStateMap={executionStateMap}
          onAdvanceState={(rowId, state) => {
            setExecutionStateMap((current) => ({
              ...current,
              [rowId]: cycleExecutionState(state),
            }));
            emitEnterpriseTelemetry("enterprise.timeline.state.advanced", {
              rowId,
              previousState: state,
              nextState: cycleExecutionState(state),
            });
            incrementDeterministicMetric("enterprise.timeline.state.advanced", {
              tier: "enterprise",
            });
          }}
        />
      </section>

      <section className="panel enterprise-panel phase18-ebook-placeholder" aria-label="Enterprise E-Book Phase 18 placeholder">
        <h3>Phase 18 E-Book Hooks</h3>
        <p>Placeholder integration only. No routing or behavioral wiring.</p>
        <ul>
          {phase18EBookHooks.map((hook) => (
            <li key={hook}>Enterprise hook: {hook}</li>
          ))}
        </ul>
      </section>

      <section
        className="panel enterprise-panel phase18-export-placeholder"
        aria-label="Enterprise Phase 18 export placeholder"
      >
        <h3>Phase 18 Export Hook</h3>
        <p>Placeholder integration only. No routing, no behavior, no AV playback.</p>
        <p>Export ID: {phase18EnterpriseExportEnvelope.exportId}</p>
      </section>

      <section
        className="panel enterprise-panel phase18-inspector"
        aria-label="Enterprise Phase 18 inspector"
      >
        <h3>Phase 18 Inspector</h3>
        <p>Mode: {phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root.mode}</p>
        <p>Has Audio: {phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root.hasAudio ? "yes" : "no"}</p>
        <p>Has AV: {phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root.hasAV ? "yes" : "no"}</p>
        <p>Export ID: {phase18EnterpriseExportEnvelope.exportId}</p>
      </section>

      <section
        className="panel enterprise-panel phase18-debug-console"
        aria-label="Enterprise Phase 18 debug console"
      >
        <h3>Phase 18 Debug Console</h3>
        <p>Read-only diagnostic payload for deterministic Phase 18 export envelope.</p>
        <details>
          <summary>Show Export Envelope JSON</summary>
          <pre>{JSON.stringify(phase18EnterpriseExportEnvelope, null, 2)}</pre>
        </details>
      </section>

      <section
        className="panel enterprise-panel phase18-validator"
        aria-label="Enterprise Phase 18 envelope validator"
      >
        <h3>Phase 18 Envelope Validator</h3>
        <p>
          Envelope OK: {phase18EnterpriseExportEnvelope &&
          phase18EnterpriseExportEnvelope.typeCheck &&
          phase18EnterpriseExportEnvelope.typeCheck.orchestrator &&
          phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root
            ? "yes"
            : "no"}
        </p>
        <p>
          Aggregate OK: {phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root.module.envelope.aggregate ? "yes" : "no"}
        </p>
        <p>
          Present Root OK: {phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root.module.envelope.aggregate.presentRoot ? "yes" : "no"}
        </p>
        <p>AV Root OK: {phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root.module.envelope.aggregate.avRoot ? "yes" : "no"}</p>
      </section>

      <section
        className="panel enterprise-panel phase18-runtime-preview"
        aria-label="Enterprise Phase 18 runtime preview"
      >
        <h3>Phase 18 Runtime Preview</h3>
        <p>Runtime Mode: {phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root.mode}</p>
        <p>Audio Capability: {phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root.hasAudio ? "enabled" : "disabled"}</p>
        <p>AV Capability: {phase18EnterpriseExportEnvelope.typeCheck.orchestrator.root.hasAV ? "enabled" : "disabled"}</p>
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
