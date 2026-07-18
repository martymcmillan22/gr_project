import { useMemo, useState } from "react";
import btAnchor from "../anchors/bt_anchor.json";
import ArtifactTagDisplay from "../components/ArtifactTagDisplay";
import QPUTower from "../components/QPUTower";
import TowerExecutionTimeline from "../components/TowerExecutionTimeline";
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

  return (
    <section className="enterprise-workspace">
      <header className="panel">
        <p className="eyebrow">BaseTrue Enterprise Workspace</p>
        <h2>Tower Control Room</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "8px" }}>
          <span className="tier-badge">tier enterprise</span>
          <span className="temporal-badge">workspace enterprise</span>
          <span className="commands-badge">project {activeProject?.project_id || "none"}</span>
          <span className="commands-badge">tower height {activeProject?.qpu_plan.tower_floors || 0}</span>
          <span className="commands-badge">active floor {effectiveFloor || "-"}</span>
        </div>
        <p className="status-line">
          Full enterprise orchestration across all tower floors. Temporal view: {activeProject?.temporal_group || "-"} ({
          activeProject ? TEMPORAL_FLOOR_PURPOSE[activeProject.temporal_group] : "-"
          })
        </p>
        <p className="status-line">
          Governance profiles: {governanceProfiles.join(", ")} | Temporal overlay owner: {temporalOwner} | Active zone: {activeZone}
        </p>
        <p className="status-line">
          Garden maintenance route: {activeGardenRoute} | Guided chain: {STUDIO_ENTERPRISE_GUIDED_CHAIN.join(" -> ")}
        </p>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "8px" }}>
          {profileBadges.map((item) => (
            <span key={item.profile} className="commands-badge">
              {item.profile}:{item.allowed ? "allowed" : "blocked"}
            </span>
          ))}
          <span className="commands-badge">governed apply:{canRunGovernedApply ? "enabled" : "disabled"}</span>
          <span className="commands-badge">release workflows:{canRunGovernedApply ? "enabled" : "disabled"}</span>
        </div>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "8px" }}>
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
        <p className="status-line">RR route: {rrRoute} | QPU plan: {activeProject?.qpu_plan.qpu_plan_id || "none"}</p>
        <p className="status-line">Tower-wide slice summary: {towerSummary}</p>
        <ArtifactTagDisplay
          label="Enterprise Header Tags"
          tags={activeProject?.artifact_tags}
          workspaceMode="enterprise"
          semanticMix={activeProject?.qpu_plan.slices.map((slice) => `${slice.slice}:${slice.count}`)}
        />
      </header>

      <section className="panel">
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

      <section className="panel">
        <h3>2. Tower Overview Panel</h3>
        <p className="status-line">
          Full tower interaction with floor selection and hover summaries. View mode: {activeProject ? getViewType(activeProject.temporal_group) : "-"}
        </p>
        <QPUTower
          compartmentIndex={activeProject?.artifact_tags.compartment_index || 9}
          project={activeProject}
          selectedFloor={effectiveFloor}
          onFloorSelect={setActiveFloor}
          onFloorHover={setHoveredFloor}
          workspaceMode="enterprise"
          interactive={true}
        />
        {hoveredFloorSummary ? <p className="status-line">Hover: {hoveredFloorSummary}</p> : null}
      </section>

      <section className="panel">
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
            <div style={{ display: "grid", gap: "6px", margin: "8px 0" }}>
              {activeFloorPlan.slices.map((slice) => {
                const widthPct = activeFloorPlan.total_count > 0 ? Math.round((slice.count / activeFloorPlan.total_count) * 100) : 0;
                return (
                  <div key={`${activeFloorPlan.floor}-${slice.slice}`}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>{slice.slice}</span>
                      <span>{slice.count}</span>
                    </div>
                    <div style={{ height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "999px" }}>
                      <div
                        style={{
                          width: `${widthPct}%`,
                          height: "6px",
                          borderRadius: "999px",
                          background: "rgba(93, 157, 255, 0.8)",
                          transition: "width 250ms ease",
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
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              <a href="#enterprise-timeline">Jump to timeline</a>
              <a href="#enterprise-tower">Jump to tower</a>
            </div>
            <div style={{ display: "grid", gap: "6px", marginTop: "8px" }}>
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

      <section className="panel">
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
          }}
        />
      </section>
    </section>
  );
}
