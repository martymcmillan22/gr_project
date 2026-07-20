import type { EBookPhase24ActivationResult } from "./ebookPhase24ActivationEngine";

export interface EBookPhase24ActivationDiagnostics {
  diagnosticsId: string;
  activationResult: EBookPhase24ActivationResult;
  mode: "activation";
}

export const buildPhase24ActivationDiagnostics = (
  activationResult: EBookPhase24ActivationResult,
): EBookPhase24ActivationDiagnostics => ({
  diagnosticsId: "phase24-activation-diagnostics-placeholder",
  activationResult,
  mode: "activation",
});