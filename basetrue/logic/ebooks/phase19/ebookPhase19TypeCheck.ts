import type { EBookPhase19Orchestrator } from "./ebookPhase19Orchestrator";

export interface EBookPhase19TypeCheck {
  typeCheckId: string;
  orchestrator: EBookPhase19Orchestrator;
  mode: "static";
}

export const buildPhase19TypeCheck = (
  orchestrator: EBookPhase19Orchestrator,
): EBookPhase19TypeCheck => ({
  typeCheckId: "phase19-typecheck-placeholder",
  orchestrator,
  mode: "static",
});