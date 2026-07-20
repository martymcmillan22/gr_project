import type { EBookPhase29TransmissionResult } from "./ebookPhase29TransmissionEngine";

export interface EBookPhase29TransmissionDiagnostics {
  diagnosticsId: string;
  transmissionResult: EBookPhase29TransmissionResult;
  mode: "transmission";
}

export const buildPhase29TransmissionDiagnostics = (
  transmissionResult: EBookPhase29TransmissionResult,
): EBookPhase29TransmissionDiagnostics => ({
  diagnosticsId: "phase29-transmission-diagnostics-placeholder",
  transmissionResult,
  mode: "transmission",
});