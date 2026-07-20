import type { EBookPhase27RenderingDiagnostics } from "./ebookPhase27RenderingDiagnostics";

export interface EBookPhase27ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase27RenderingDiagnostics;
  mode: "rendering";
}

export const buildPhase27ExportEnvelope = (
  diagnostics: EBookPhase27RenderingDiagnostics,
): EBookPhase27ExportEnvelope => ({
  exportId: "phase27-export-envelope-placeholder",
  diagnostics,
  mode: "rendering",
});