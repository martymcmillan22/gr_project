import type { EBookPhase26TranslationPlan } from "./ebookPhase26TranslationPlan";

export interface EBookPhase26TranslationResult {
  resultId: string;
  plan: EBookPhase26TranslationPlan;
  translatedLane: string;
  status: "ok" | "warning";
}

export const runPhase26Translation = (
  plan: EBookPhase26TranslationPlan,
): EBookPhase26TranslationResult => ({
  resultId: "phase26-translation-result-placeholder",
  plan,
  translatedLane: plan.sourceExport.diagnostics.projectionResult.projectedLane,
  status: "ok",
});