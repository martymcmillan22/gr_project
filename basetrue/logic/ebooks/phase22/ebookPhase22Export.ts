import type { EBookPhase22ResolutionDiagnostics } from "./ebookPhase22ResolutionDiagnostics";

export interface EBookPhase22ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase22ResolutionDiagnostics;
  mode: "resolution";
}

export const buildPhase22ExportEnvelope = (
  diagnostics: EBookPhase22ResolutionDiagnostics,
): EBookPhase22ExportEnvelope => ({
  exportId: "phase22-export-envelope-placeholder",
  diagnostics,
  mode: "resolution",
});