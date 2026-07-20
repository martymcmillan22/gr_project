import type { EBookPhase24ActivationPlan } from "./ebookPhase24ActivationPlan";

export interface EBookPhase24ActivationResult {
  resultId: string;
  plan: EBookPhase24ActivationPlan;
  activatedLane: string;
  status: "ok" | "warning";
}

export const runPhase24Activation = (
  plan: EBookPhase24ActivationPlan,
): EBookPhase24ActivationResult => ({
  resultId: "phase24-activation-result-placeholder",
  plan,
  activatedLane: plan.sourceExport.diagnostics.materialResult.materializedLane,
  status: "ok",
});