import type { EBookPhase19ExportEnvelope } from "../phase19/ebookPhase19Export";

export interface EBookPhase20RuntimePlan {
  planId: string;
  sourceExport: EBookPhase19ExportEnvelope;
  mode: "dry-run";
}

export const buildPhase20RuntimePlan = (
  sourceExport: EBookPhase19ExportEnvelope,
): EBookPhase20RuntimePlan => ({
  planId: "phase20-runtime-plan-placeholder",
  sourceExport,
  mode: "dry-run",
});