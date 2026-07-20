import type { EBookPhase21RuntimeLanes } from "./ebookPhase21RuntimeLanes";

export interface EBookPhase21PreRouter {
  preRouterId: string;
  lanes: EBookPhase21RuntimeLanes;
  selectedLane: string;
  mode: "intent";
}

export const buildPhase21PreRouter = (
  lanes: EBookPhase21RuntimeLanes,
): EBookPhase21PreRouter => ({
  preRouterId: "phase21-prerouter-placeholder",
  lanes,
  selectedLane: lanes.lanes[0],
  mode: "intent",
});