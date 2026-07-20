import type { EBookPhase26TranslationResult } from "./ebookPhase26TranslationEngine";

export interface EBookPhase26TranslationDiagnostics {
  diagnosticsId: string;
  translationResult: EBookPhase26TranslationResult;
  mode: "translation";
}

export const buildPhase26TranslationDiagnostics = (
  translationResult: EBookPhase26TranslationResult,
): EBookPhase26TranslationDiagnostics => ({
  diagnosticsId: "phase26-translation-diagnostics-placeholder",
  translationResult,
  mode: "translation",
});