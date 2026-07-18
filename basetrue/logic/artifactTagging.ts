import type { ArtifactTags, Phase, ProfileKind, RRSelection, TemporalGroup, Tier, WorkspaceMode } from "../types";
import { buildSeedRoute } from "./rrRouter";

export function buildArtifactTags(params: {
  profile: ProfileKind;
  compartmentName: string;
  compartmentIndex: number;
  phase: Phase;
  temporalGroup: TemporalGroup;
  tier: Tier;
  rrRoute?: string;
  rrSelection?: RRSelection;
  qpuPlanId?: string;
  floor?: number | null;
  workspaceMode?: WorkspaceMode;
}): ArtifactTags {
  const computedRrRoute =
    params.rrRoute ||
    (params.rrSelection
      ? buildSeedRoute({
          quadrant: params.rrSelection.quadrant,
          subnode: params.rrSelection.subnode,
          logicMode: params.rrSelection.logic_mode,
          temporalGroup: params.rrSelection.temporal_group,
        })
      : undefined);

  return {
    profile: params.profile,
    compartment: params.compartmentName,
    compartment_name: params.compartmentName,
    compartment_index: params.compartmentIndex,
    phase: params.phase,
    temporal_group: params.temporalGroup,
    tier: params.tier,
    rr_route: computedRrRoute,
    qpu_plan_id: params.qpuPlanId,
    floor: params.workspaceMode === "studio" ? null : params.floor,
  };
}

export function formatArtifactTags(tags: ArtifactTags): string {
  const parts = [
    `profile=${tags.profile}`,
    `compartment=${tags.compartment}`,
    `index=${tags.compartment_index}`,
    `phase=${tags.phase}`,
    `tier=${tags.tier}`,
    `temporal=${tags.temporal_group}`,
  ];

  if (tags.rr_route) {
    parts.push(`rr_route=${tags.rr_route}`);
  }
  if (tags.qpu_plan_id) {
    parts.push(`qpu_plan_id=${tags.qpu_plan_id}`);
  }
  if (typeof tags.floor === "number") {
    parts.push(`floor=${tags.floor}`);
  }

  return parts.join(" | ");
}
