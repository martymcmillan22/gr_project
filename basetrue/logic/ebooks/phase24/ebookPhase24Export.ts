import type { EBookPhase24ActivationDiagnostics } from "./ebookPhase24ActivationDiagnostics";

export interface EBookPhase24ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase24ActivationDiagnostics;
  mode: "activation";
}

export const buildPhase24ExportEnvelope = (
  diagnostics: EBookPhase24ActivationDiagnostics,
): EBookPhase24ExportEnvelope => ({
  exportId: "phase24-export-envelope-placeholder",
  diagnostics,
  mode: "activation",
});