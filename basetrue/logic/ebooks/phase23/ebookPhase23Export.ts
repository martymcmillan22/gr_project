import type { EBookPhase23MaterialDiagnostics } from "./ebookPhase23MaterialDiagnostics";

export interface EBookPhase23ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase23MaterialDiagnostics;
  mode: "material";
}

export const buildPhase23ExportEnvelope = (
  diagnostics: EBookPhase23MaterialDiagnostics,
): EBookPhase23ExportEnvelope => ({
  exportId: "phase23-export-envelope-placeholder",
  diagnostics,
  mode: "material",
});