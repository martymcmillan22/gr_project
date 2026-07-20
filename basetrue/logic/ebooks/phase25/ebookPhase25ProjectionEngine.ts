import type { EBookPhase25ProjectionPlan } from "./ebookPhase25ProjectionPlan";

export interface EBookPhase25ProjectionResult {
  resultId: string;
  plan: EBookPhase25ProjectionPlan;
  projectedLane: string;
  status: "ok" | "warning";
}

export const runPhase25Projection = (
  plan: EBookPhase25ProjectionPlan,
): EBookPhase25ProjectionResult => ({
  resultId: "phase25-projection-result-placeholder",
  plan,
  projectedLane: plan.sourceExport.diagnostics.activationResult.activatedLane,
  status: "ok",
});