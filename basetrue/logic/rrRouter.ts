import type {
  RRLogicMode,
  RRQuadrant,
  RRSelection,
  RRSubnode,
  TemporalGroup,
  Tier,
} from "../types";

export const RR_QUADRANTS: RRQuadrant[] = ["language", "arts", "math", "science"];
export const RR_SUBNODES: RRSubnode[] = ["A", "B", "C", "D"];
export const RR_LOGIC_MODES: RRLogicMode[] = ["hierarchical", "network", "object", "relational"];

export const RR_SUBNODE_MEANINGS: Record<RRSubnode, string> = {
  A: "Abstract",
  B: "Build",
  C: "Connect",
  D: "Detail",
};

export function getRrDiagramMode(tier: Tier): "architectural" | "layered" | "flat" {
  if (tier === "intermediate") {
    return "flat";
  }
  if (tier === "advanced") {
    return "layered";
  }
  return "architectural";
}

export function buildSeedRoute(selection: {
  quadrant: RRQuadrant;
  subnode: RRSubnode;
  logicMode: RRLogicMode;
  temporalGroup: TemporalGroup;
}): string {
  return `${selection.quadrant}.${selection.subnode}.${selection.logicMode}.${selection.temporalGroup}`;
}

export function buildRrSelection(selection: {
  quadrant: RRQuadrant;
  subnode: RRSubnode;
  logicMode: RRLogicMode;
  temporalGroup: TemporalGroup;
}): RRSelection {
  return {
    quadrant: selection.quadrant,
    subnode: selection.subnode,
    logic_mode: selection.logicMode,
    temporal_group: selection.temporalGroup,
  };
}
