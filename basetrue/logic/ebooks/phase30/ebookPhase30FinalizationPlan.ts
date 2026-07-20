import type { EBookPhase29ExportEnvelope } from "../phase29/ebookPhase29Export";

export interface EBookPhase30FinalizationPlan {
  planId: string;
  sourceExport: EBookPhase29ExportEnvelope;
  mode: "finalization";
}

export const buildPhase30FinalizationPlan = (
  sourceExport: EBookPhase29ExportEnvelope,
): EBookPhase30FinalizationPlan => ({
  planId: "phase30-finalization-plan-placeholder",
  sourceExport,
  mode: "finalization",
});