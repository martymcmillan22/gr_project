import type { EBookPhase30FinalizationResult } from "./ebookPhase30FinalizationEngine";

export interface EBookPhase30FinalizationDiagnostics {
  diagnosticsId: string;
  finalizationResult: EBookPhase30FinalizationResult;
  mode: "finalization";
}

export const buildPhase30FinalizationDiagnostics = (
  finalizationResult: EBookPhase30FinalizationResult,
): EBookPhase30FinalizationDiagnostics => ({
  diagnosticsId: "phase30-finalization-diagnostics-placeholder",
  finalizationResult,
  mode: "finalization",
});