import type { EBookPhase24ExportEnvelope } from "../phase24/ebookPhase24Export";

export interface EBookPhase25ProjectionPlan {
  planId: string;
  sourceExport: EBookPhase24ExportEnvelope;
  mode: "projection";
}

export const buildPhase25ProjectionPlan = (
  sourceExport: EBookPhase24ExportEnvelope,
): EBookPhase25ProjectionPlan => ({
  planId: "phase25-projection-plan-placeholder",
  sourceExport,
  mode: "projection",
});