import type { EBookPhase25ProjectionResult } from "./ebookPhase25ProjectionEngine";

export interface EBookPhase25ProjectionDiagnostics {
  diagnosticsId: string;
  projectionResult: EBookPhase25ProjectionResult;
  mode: "projection";
}

export const buildPhase25ProjectionDiagnostics = (
  projectionResult: EBookPhase25ProjectionResult,
): EBookPhase25ProjectionDiagnostics => ({
  diagnosticsId: "phase25-projection-diagnostics-placeholder",
  projectionResult,
  mode: "projection",
});