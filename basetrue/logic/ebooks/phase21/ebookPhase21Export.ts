import type { EBookPhase21PreRouter } from "./ebookPhase21PreRouter";

export interface EBookPhase21ExportEnvelope {
  exportId: string;
  preRouter: EBookPhase21PreRouter;
  mode: "intent";
}

export const buildPhase21ExportEnvelope = (
  preRouter: EBookPhase21PreRouter,
): EBookPhase21ExportEnvelope => ({
  exportId: "phase21-export-envelope-placeholder",
  preRouter,
  mode: "intent",
});