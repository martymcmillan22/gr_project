import type { EBookPhase22ExportEnvelope } from "../phase22/ebookPhase22Export";

export interface EBookPhase23MaterialPlan {
  planId: string;
  sourceExport: EBookPhase22ExportEnvelope;
  mode: "material";
}

export const buildPhase23MaterialPlan = (
  sourceExport: EBookPhase22ExportEnvelope,
): EBookPhase23MaterialPlan => ({
  planId: "phase23-material-plan-placeholder",
  sourceExport,
  mode: "material",
});