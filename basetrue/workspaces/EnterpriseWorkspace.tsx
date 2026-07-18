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
import {
  STUDIO_ENTERPRISE_GARDEN_MAINTENANCE,
  STUDIO_ENTERPRISE_GUIDED_CHAIN,
  STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP,
  STUDIO_ENTERPRISE_TOWER,
} from "../logic/baseTrueConstants";
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

  return planIndices.map((compartmentIndex, offset) => {
    const temporalGroup = getTemporalGroup(compartmentIndex);
    const rrSelection = buildRrSelection({
      quadrant: (["language", "arts", "math", "science"] as RRQuadrant[])[offset % 4],
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
    if (STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP.qc_user.includes(group)) {
      return "QC";
    }
    if (STUDIO_ENTERPRISE_TEMPORAL_OWNERSHIP.qa_va.includes(group)) {
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
    </section>
  );
}
