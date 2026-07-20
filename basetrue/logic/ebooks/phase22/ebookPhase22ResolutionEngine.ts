import type { EBookPhase22ResolutionPlan } from "./ebookPhase22ResolutionPlan";

export interface EBookPhase22ResolutionResult {
  resultId: string;
  plan: EBookPhase22ResolutionPlan;
  resolvedLane: string;
  status: "ok" | "warning";
}

export const runPhase22Resolution = (
  plan: EBookPhase22ResolutionPlan,
): EBookPhase22ResolutionResult => ({
  resultId: "phase22-resolution-result-placeholder",
  plan,
  resolvedLane: plan.sourceExport.preRouter.selectedLane,
  status: "ok",
});