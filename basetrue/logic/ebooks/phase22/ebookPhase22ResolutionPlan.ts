import type { EBookPhase21ExportEnvelope } from "../phase21/ebookPhase21Export";

export interface EBookPhase22ResolutionPlan {
  planId: string;
  sourceExport: EBookPhase21ExportEnvelope;
  mode: "resolution";
}

export const buildPhase22ResolutionPlan = (
  sourceExport: EBookPhase21ExportEnvelope,
): EBookPhase22ResolutionPlan => ({
  planId: "phase22-resolution-plan-placeholder",
  sourceExport,
  mode: "resolution",
});