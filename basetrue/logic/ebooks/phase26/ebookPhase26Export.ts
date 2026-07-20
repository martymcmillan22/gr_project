import type { EBookPhase26TranslationDiagnostics } from "./ebookPhase26TranslationDiagnostics";

export interface EBookPhase26ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase26TranslationDiagnostics;
  mode: "translation";
}

export const buildPhase26ExportEnvelope = (
  diagnostics: EBookPhase26TranslationDiagnostics,
): EBookPhase26ExportEnvelope => ({
  exportId: "phase26-export-envelope-placeholder",
  diagnostics,
  mode: "translation",
});