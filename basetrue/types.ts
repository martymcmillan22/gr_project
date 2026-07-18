export type Tier = "novice" | "intermediate" | "advanced" | "studio" | "enterprise";
export type Phase = "create" | "post" | "work";
export type TemporalGroup = "past" | "present_past" | "present_future" | "future";
export type ViewType = "list" | "detail" | "how_to" | "present";
export type GeometryMode = "architectural" | "layered" | "flat";
export type GovernanceProfile = "weekly" | "monthly" | "quarterly" | "annual";

export type ProfileKind = "public" | "personal";

export type PipelineStage = "idea" | "seed" | "project" | "work";
export type CompartmentViewMode = "dashboard" | "pipeline";
export type WorkspaceMode = "default" | "studio" | "enterprise";
export type StudioAccessTier = Extract<Tier, "studio" | "enterprise">;
export type EnterpriseAccessTier = Extract<Tier, "enterprise">;
export type RRQuadrant = "language" | "arts" | "math" | "science";
export type RRSubnode = "A" | "B" | "C" | "D";
export type RRLogicMode = "hierarchical" | "network" | "object" | "relational";
export type QpuOrchestrationMode = "scaled" | "tower";

export interface StudioWorkspaceConfig {
  workspace: "studio";
  access_tier: StudioAccessTier;
  compartment_index: number;
}

export interface EnterpriseWorkspaceConfig {
  workspace: "enterprise";
  access_tier: EnterpriseAccessTier;
}

export interface RRSelection {
  quadrant: RRQuadrant;
  subnode: RRSubnode;
  logic_mode: RRLogicMode;
  temporal_group: TemporalGroup;
}

export interface QpuSliceAllocation {
  slice: RRQuadrant;
  weight: number;
  count: number;
}

export interface QpuPlan {
  qpu_plan_id: string;
  base_count: number;
  adjusted_count: number;
  eligible: boolean;
  max_compartment: number;
  orchestration_mode: QpuOrchestrationMode;
  geometry_mode: GeometryMode;
  tower_enabled: boolean;
  tower_floors: number;
  rr_influence?: RRSelection;
  temporal_group: TemporalGroup;
  auto_slices: QpuSliceAllocation[];
  slices: QpuSliceAllocation[];
  manual_slice_adjustments?: QpuSliceAllocation[];
  notes: string[];
}

export interface QpuFloorPlan {
  floor: number;
  total_count: number;
  slices: QpuSliceAllocation[];
  steps: string[];
}

export interface TierConfig {
  commands: Array<number | "all">;
  rr: boolean;
  qpu: boolean;
  storage_gb?: number;
  qpu_max_compartment?: number;
}

export interface ArtifactTags {
  profile: ProfileKind;
  compartment: string;
  compartment_name: string;
  compartment_index: number;
  phase: Phase;
  temporal_group: TemporalGroup;
  tier: Tier;
  rr_route?: string;
  qpu_plan_id?: string;
  floor?: number | null;
}

export interface WorkRecord {
  work_id: string;
  project_id: string;
  floor: number;
  task: string;
  temporal_group: TemporalGroup;
  phase: "work";
  tier: Tier;
  artifact_tags: ArtifactTags;
}

export interface IdeaRecord {
  idea_id: string;
  title: string;
  description: string;
  tags: string[];
  temporal_group: TemporalGroup;
  phase: "create";
  tier: Tier;
  created_at: string;
  geometry_mode: GeometryMode;
  artifact_tags: ArtifactTags;
}

export interface SeedRecord {
  seed_id: string;
  idea_id: string;
  structure: string;
  metadata: Record<string, string>;
  temporal_group: TemporalGroup;
  phase: "create";
  tier: Tier;
  seed_route?: string;
  rr_selection?: RRSelection;
  rr_route?: string;
  ready_for_qpu: boolean;
  geometry_mode: Extract<GeometryMode, "layered" | "architectural">;
  artifact_tags: ArtifactTags;
}

export interface ProjectRecord {
  project_id: string;
  seed_id: string;
  qpu_allocation: number;
  qpu_plan: QpuPlan;
  temporal_group: TemporalGroup;
  phase: Phase;
  tier: Tier;
  work_state: string;
  tower_level?: number;
  artifacts: string[];
  work_artifacts?: WorkRecord[];
  geometry_mode: Extract<GeometryMode, "architectural">;
  artifact_tags: ArtifactTags;
}
