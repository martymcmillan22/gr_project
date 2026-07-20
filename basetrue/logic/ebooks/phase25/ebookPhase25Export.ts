import type { EBookPhase25ProjectionDiagnostics } from "./ebookPhase25ProjectionDiagnostics";

export interface EBookPhase25ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase25ProjectionDiagnostics;
  mode: "projection";
}

export const buildPhase25ExportEnvelope = (
  diagnostics: EBookPhase25ProjectionDiagnostics,
): EBookPhase25ExportEnvelope => ({
  exportId: "phase25-export-envelope-placeholder",
  diagnostics,
  mode: "projection",
});