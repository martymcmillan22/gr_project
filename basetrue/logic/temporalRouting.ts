import type { Phase, TemporalGroup, ViewType } from "../types";
import { PHASE_COLOR_BY_GROUP, TEMPORAL_GROUP_BY_INDEX, VIEW_BY_TEMPORAL_GROUP } from "./baseTrueConstants";
import { assertValidCompartmentIndex } from "./schemaGuards";

export function getTemporalGroup(compartmentIndex: number): TemporalGroup {
  assertValidCompartmentIndex(compartmentIndex);
  return TEMPORAL_GROUP_BY_INDEX[compartmentIndex];
}

export function getViewType(group: TemporalGroup): ViewType {
  return VIEW_BY_TEMPORAL_GROUP[group];
}

export function getPhaseColor(phase: Phase, group: TemporalGroup): string {
  return PHASE_COLOR_BY_GROUP[phase][group];
}
