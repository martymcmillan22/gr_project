import type { EBookPhase27RenderingPlan } from "./ebookPhase27RenderingPlan";

export interface EBookPhase27RenderingResult {
  resultId: string;
  plan: EBookPhase27RenderingPlan;
  renderedLane: string;
  status: "ok" | "warning";
}

export const runPhase27Rendering = (
  plan: EBookPhase27RenderingPlan,
): EBookPhase27RenderingResult => ({
  resultId: "phase27-rendering-result-placeholder",
  plan,
  renderedLane: plan.sourceExport.diagnostics.translationResult.translatedLane,
  status: "ok",
});