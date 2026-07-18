import { getQPUCount } from "./qpuGrowth";
import { getTierQpuMaxCompartment } from "./pipelineLogic";
import { RR_QUADRANTS } from "./baseTrueConstants";
import { assertValidCompartmentIndex, isWorkspaceMode } from "./schemaGuards";
import type {
  QpuFloorPlan,
  QpuPlan,
  QpuSliceAllocation,
  RRLogicMode,
  RRQuadrant,
  RRSelection,
  TemporalGroup,
  Tier,
  WorkspaceMode,
} from "../types";

const QUADRANTS: RRQuadrant[] = [...RR_QUADRANTS];

const LOGIC_MODE_MULTIPLIER: Record<RRLogicMode, number> = {
  hierarchical: 1,
  network: 1.08,
  object: 1.16,
  relational: 1.24,
};

const TEMPORAL_MULTIPLIER: Record<TemporalGroup, number> = {
  past: 0.9,
  present_past: 1,
  present_future: 1.12,
  future: 1.2,
};

const SUBNODE_BIAS: Record<"A" | "B" | "C" | "D", Record<RRQuadrant, number>> = {
  A: { language: 1, arts: 1, math: 1, science: 1 },
  B: { language: 0.9, arts: 0.9, math: 1.2, science: 1.1 },
  C: { language: 1.2, arts: 1.1, math: 0.9, science: 0.9 },
  D: { language: 0.9, arts: 0.95, math: 1.15, science: 1.2 },
};

function resolveBaseQpuCount(compartmentIndex: number): number {
  if (compartmentIndex === 4) {
    return 4;
  }
  return getQPUCount(compartmentIndex);
}

function resolveGeometryMode(tier: Tier, rrSelection?: RRSelection): "flat" | "layered" | "architectural" {
  if (tier === "enterprise") {
    return "architectural";
  }

  if (!rrSelection) {
    return "layered";
  }

  if (rrSelection.logic_mode === "hierarchical") {
    return "flat";
  }

  if (rrSelection.logic_mode === "network") {
    return "layered";
  }

  return "architectural";
}

function normalizeWeights(weights: Record<RRQuadrant, number>): Record<RRQuadrant, number> {
  const total = Object.values(weights).reduce((sum, value) => sum + value, 0);
  if (total <= 0) {
    return { language: 0.25, arts: 0.25, math: 0.25, science: 0.25 };
  }

  return {
    language: weights.language / total,
    arts: weights.arts / total,
    math: weights.math / total,
    science: weights.science / total,
  };
}

function distributeCounts(total: number, weights: Record<RRQuadrant, number>): QpuSliceAllocation[] {
  if (total <= 0) {
    return QUADRANTS.map((slice) => ({ slice, weight: weights[slice], count: 0 }));
  }

  const raw = QUADRANTS.map((slice) => ({
    slice,
    weight: weights[slice],
    rawCount: total * weights[slice],
  }));

  const baseCounts = raw.map((item) => ({ ...item, count: Math.floor(item.rawCount) }));
  let remaining = total - baseCounts.reduce((sum, item) => sum + item.count, 0);

  if (remaining > 0) {
    const byRemainder = [...baseCounts].sort((a, b) => {
      const remainderA = a.rawCount - a.count;
      const remainderB = b.rawCount - b.count;
      return remainderB - remainderA;
    });

    for (let i = 0; i < byRemainder.length && remaining > 0; i += 1) {
      byRemainder[i].count += 1;
      remaining -= 1;
    }

    return QUADRANTS.map((slice) => {
      const item = byRemainder.find((entry) => entry.slice === slice)!;
      return { slice, weight: item.weight, count: item.count };
    });
  }

  return baseCounts.map((item) => ({ slice: item.slice, weight: item.weight, count: item.count }));
}

function distributeEvenly(total: number, buckets: number): number[] {
  if (buckets <= 0) {
    return [];
  }

  const base = Math.floor(total / buckets);
  let remainder = total - base * buckets;
  const distribution = new Array<number>(buckets).fill(base);

  for (let index = 0; index < buckets && remainder > 0; index += 1) {
    distribution[index] += 1;
    remainder -= 1;
  }

  return distribution;
}

export function applyManualSliceAdjustments(plan: QpuPlan, manualCounts: Partial<Record<RRQuadrant, number>>): QpuPlan {
  const requested = QUADRANTS.map((slice) => {
    const value = manualCounts[slice] ?? 0;
    return {
      slice,
      count: Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0,
    };
  });

  const requestedTotal = requested.reduce((sum, item) => sum + item.count, 0);
  if (requestedTotal > plan.adjusted_count) {
    return {
      ...plan,
      notes: [...plan.notes, `Manual slice override rejected: requested ${requestedTotal}, max ${plan.adjusted_count}.`],
    };
  }

  const baselineBySlice = Object.fromEntries(plan.auto_slices.map((slice) => [slice.slice, slice.count])) as Record<
    RRQuadrant,
    number
  >;

  const withFill: Record<RRQuadrant, number> = { language: 0, arts: 0, math: 0, science: 0 };
  QUADRANTS.forEach((slice) => {
    withFill[slice] = requested.find((entry) => entry.slice === slice)?.count ?? 0;
  });

  let remaining = plan.adjusted_count - requestedTotal;
  const fillPriority = [...plan.auto_slices].sort((a, b) => b.count - a.count);
  for (let index = 0; index < fillPriority.length && remaining > 0; index += 1) {
    const key = fillPriority[index].slice;
    withFill[key] += 1;
    remaining -= 1;
    if (index === fillPriority.length - 1 && remaining > 0) {
      index = -1;
    }
  }

  const manualSliceAdjustments: QpuSliceAllocation[] = QUADRANTS.map((slice) => ({
    slice,
    count: withFill[slice],
    weight: plan.adjusted_count > 0 ? withFill[slice] / plan.adjusted_count : 0,
  }));

  const changed = QUADRANTS.some((slice) => withFill[slice] !== baselineBySlice[slice]);
  const notes = changed
    ? [...plan.notes, "Manual slice override applied within adjusted_count constraint."]
    : plan.notes;

  return {
    ...plan,
    slices: manualSliceAdjustments,
    manual_slice_adjustments: manualSliceAdjustments,
    notes,
  };
}

export function buildQpuPlan(params: {
  tier: Tier;
  compartmentIndex: number;
  temporalGroup: TemporalGroup;
  rrSelection?: RRSelection;
  workspaceMode?: WorkspaceMode;
}): QpuPlan {
  const { tier, compartmentIndex, temporalGroup, rrSelection } = params;
  assertValidCompartmentIndex(compartmentIndex);
  const workspaceMode: WorkspaceMode = isWorkspaceMode(params.workspaceMode) ? params.workspaceMode : "default";
  const effectiveTier: Tier =
    workspaceMode === "enterprise"
      ? "enterprise"
      : workspaceMode === "studio" && tier === "enterprise"
        ? "studio"
        : tier;
  const maxCompartment = getTierQpuMaxCompartment(effectiveTier);
  const eligible = maxCompartment > 0 && compartmentIndex <= maxCompartment;
  const baseCount = resolveBaseQpuCount(compartmentIndex);

  const logicMultiplier = rrSelection ? LOGIC_MODE_MULTIPLIER[rrSelection.logic_mode] : 1;
  const temporalMultiplier = TEMPORAL_MULTIPLIER[temporalGroup];
  const adjustedCount = eligible ? Math.max(0, Math.round(baseCount * logicMultiplier * temporalMultiplier)) : 0;

  const baseWeights: Record<RRQuadrant, number> = {
    language: 1,
    arts: 1,
    math: 1,
    science: 1,
  };

  if (rrSelection) {
    baseWeights[rrSelection.quadrant] += 0.55;
    const subnodeWeights = SUBNODE_BIAS[rrSelection.subnode];
    QUADRANTS.forEach((quadrant) => {
      baseWeights[quadrant] *= subnodeWeights[quadrant];
    });
  }

  const normalized = normalizeWeights(baseWeights);
  const slices = distributeCounts(adjustedCount, normalized);

  const towerEnabled = workspaceMode !== "studio" && effectiveTier === "enterprise";
  const towerFloors = towerEnabled ? Math.max(1, Math.ceil(Math.log2(Math.max(1, adjustedCount)))) : 0;

  const notes: string[] = [];
  const rrRouteId = rrSelection
    ? `${rrSelection.quadrant}.${rrSelection.subnode}.${rrSelection.logic_mode}.${rrSelection.temporal_group}`
    : "none";
  const qpuPlanId = `qpu.${workspaceMode}.${tier}.${compartmentIndex}.${temporalGroup}.${rrRouteId}`;
  if (!eligible) {
    notes.push(`Compartment ${compartmentIndex} exceeds tier QPU max compartment ${maxCompartment}.`);
  }
  if (rrSelection) {
    notes.push(`RR influence: ${rrSelection.quadrant}.${rrSelection.subnode}.${rrSelection.logic_mode}.${rrSelection.temporal_group}`);
  }
  if (workspaceMode === "studio") {
    notes.push("Studio workspace mode: scaled QPU only, tower orchestration disabled.");
  }
  if (workspaceMode === "enterprise") {
    notes.push("Enterprise workspace mode: full tower orchestration enabled.");
  }

  return {
    qpu_plan_id: qpuPlanId,
    base_count: baseCount,
    adjusted_count: adjustedCount,
    eligible,
    max_compartment: maxCompartment,
    orchestration_mode: towerEnabled ? "tower" : "scaled",
    geometry_mode: resolveGeometryMode(effectiveTier, rrSelection),
    tower_enabled: towerEnabled,
    tower_floors: towerFloors,
    rr_influence: rrSelection,
    temporal_group: temporalGroup,
    auto_slices: slices,
    slices,
    notes,
  };
}

export function buildQpuFloorPlans(plan: QpuPlan): QpuFloorPlan[] {
  if (!plan.tower_enabled || plan.tower_floors <= 0) {
    return [];
  }

  return Array.from({ length: plan.tower_floors }, (_, floorIndex) => {
    const floor = floorIndex + 1;
    const floorSlices = plan.slices.map((slice) => {
      const perFloor = distributeEvenly(slice.count, plan.tower_floors);
      const count = perFloor[floorIndex] ?? 0;
      return {
        ...slice,
        count,
      };
    });

    const totalCount = floorSlices.reduce((sum, slice) => sum + slice.count, 0);
    const steps = [
      `Floor ${floor}: execute ${plan.orchestration_mode} dispatch for ${totalCount} units.`,
      `Floor ${floor}: temporal overlay ${plan.temporal_group}.`,
    ];

    if (plan.rr_influence) {
      steps.push(`Floor ${floor}: route to ${plan.rr_influence.quadrant}.${plan.rr_influence.subnode}.`);
    }

    floorSlices.forEach((slice) => {
      steps.push(`Floor ${floor}: ${slice.slice} slice receives ${slice.count} units.`);
    });

    return {
      floor,
      total_count: totalCount,
      slices: floorSlices,
      steps,
    };
  });
}

export function buildWorkOrchestrationSteps(plan: QpuPlan): string[] {
  const steps = [
    `Initialize ${plan.orchestration_mode} orchestration for ${plan.adjusted_count} QPU units.`,
    `Apply temporal overlay: ${plan.temporal_group}.`,
  ];

  if (plan.rr_influence) {
    steps.push(
      `Route focus: ${plan.rr_influence.quadrant}.${plan.rr_influence.subnode}.${plan.rr_influence.logic_mode}.`,
    );
  }

  if (plan.tower_enabled) {
    steps.push(`Tower orchestration across ${plan.tower_floors} floors.`);
  }

  plan.slices.forEach((slice) => {
    steps.push(`Allocate ${slice.count} units to ${slice.slice} slice.`);
  });

  return steps;
}
