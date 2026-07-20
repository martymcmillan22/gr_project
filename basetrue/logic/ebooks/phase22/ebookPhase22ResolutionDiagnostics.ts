import type { EBookPhase22ResolutionResult } from "./ebookPhase22ResolutionEngine";

export interface EBookPhase22ResolutionDiagnostics {
  diagnosticsId: string;
  resolutionResult: EBookPhase22ResolutionResult;
  mode: "resolution";
}

export const buildPhase22ResolutionDiagnostics = (
  resolutionResult: EBookPhase22ResolutionResult,
): EBookPhase22ResolutionDiagnostics => ({
  diagnosticsId: "phase22-resolution-diagnostics-placeholder",
  resolutionResult,
  mode: "resolution",
});