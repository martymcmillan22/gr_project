import type { EBookPhase19RuntimeEnvelope } from "./ebookPhase19Envelope";

export interface EBookPhase19LogicSpine {
  spineId: string;
  runtimeEnvelope: EBookPhase19RuntimeEnvelope;
  mode: "static";
}

export const buildPhase19LogicSpine = (
  runtimeEnvelope: EBookPhase19RuntimeEnvelope,
): EBookPhase19LogicSpine => ({
  spineId: "phase19-logic-spine-placeholder",
  runtimeEnvelope,
  mode: "static",
});