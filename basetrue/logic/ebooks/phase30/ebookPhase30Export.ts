import type { EBookPhase30FinalizationDiagnostics } from "./ebookPhase30FinalizationDiagnostics";

export interface EBookPhase30ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase30FinalizationDiagnostics;
  mode: "finalization";
}

export const buildPhase30ExportEnvelope = (
  diagnostics: EBookPhase30FinalizationDiagnostics,
): EBookPhase30ExportEnvelope => ({
  exportId: "phase30-export-envelope-placeholder",
  diagnostics,
  mode: "finalization",
});