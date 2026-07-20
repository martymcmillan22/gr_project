import type { EBookPhase21RuntimeIntent } from "./ebookPhase21RuntimeIntent";

export interface EBookPhase21RuntimeLanes {
  lanesId: string;
  intent: EBookPhase21RuntimeIntent;
  lanes: string[];
  mode: "intent";
}

export const buildPhase21RuntimeLanes = (
  intent: EBookPhase21RuntimeIntent,
): EBookPhase21RuntimeLanes => ({
  lanesId: "phase21-runtime-lanes-placeholder",
  intent,
  lanes: ["lane-static", "lane-dryrun"],
  mode: "intent",
});