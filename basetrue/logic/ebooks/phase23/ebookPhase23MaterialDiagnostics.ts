import type { EBookPhase23MaterialResult } from "./ebookPhase23MaterialEngine";

export interface EBookPhase23MaterialDiagnostics {
  diagnosticsId: string;
  materialResult: EBookPhase23MaterialResult;
  mode: "material";
}

export const buildPhase23MaterialDiagnostics = (
  materialResult: EBookPhase23MaterialResult,
): EBookPhase23MaterialDiagnostics => ({
  diagnosticsId: "phase23-material-diagnostics-placeholder",
  materialResult,
  mode: "material",
});