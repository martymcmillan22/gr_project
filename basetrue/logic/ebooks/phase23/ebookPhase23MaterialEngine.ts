import type { EBookPhase23MaterialPlan } from "./ebookPhase23MaterialPlan";

export interface EBookPhase23MaterialResult {
  resultId: string;
  plan: EBookPhase23MaterialPlan;
  materializedLane: string;
  status: "ok" | "warning";
}

export const runPhase23Material = (
  plan: EBookPhase23MaterialPlan,
): EBookPhase23MaterialResult => ({
  resultId: "phase23-material-result-placeholder",
  plan,
  materializedLane: plan.sourceExport.diagnostics.resolutionResult.resolvedLane,
  status: "ok",
});