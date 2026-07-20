import type { EBookPhase25ExportEnvelope } from "../phase25/ebookPhase25Export";

export interface EBookPhase26TranslationPlan {
  planId: string;
  sourceExport: EBookPhase25ExportEnvelope;
  mode: "translation";
}

export const buildPhase26TranslationPlan = (
  sourceExport: EBookPhase25ExportEnvelope,
): EBookPhase26TranslationPlan => ({
  planId: "phase26-translation-plan-placeholder",
  sourceExport,
  mode: "translation",
});