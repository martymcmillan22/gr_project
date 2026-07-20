import type { EBookPhase19LogicSpine } from "./ebookPhase19LogicSpine";

export interface EBookPhase19Orchestrator {
  orchestratorId: string;
  logicSpine: EBookPhase19LogicSpine;
  mode: "static";
}

export const buildPhase19Orchestrator = (
  logicSpine: EBookPhase19LogicSpine,
): EBookPhase19Orchestrator => ({
  orchestratorId: "phase19-orchestrator-placeholder",
  logicSpine,
  mode: "static",
});