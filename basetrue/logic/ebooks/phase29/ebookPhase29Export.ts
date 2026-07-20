import type { EBookPhase29TransmissionDiagnostics } from "./ebookPhase29TransmissionDiagnostics";

export interface EBookPhase29ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase29TransmissionDiagnostics;
  mode: "transmission";
}

export const buildPhase29ExportEnvelope = (
  diagnostics: EBookPhase29TransmissionDiagnostics,
): EBookPhase29ExportEnvelope => ({
  exportId: "phase29-export-envelope-placeholder",
  diagnostics,
  mode: "transmission",
});