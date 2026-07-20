import type { EBookPhase20DryRunResult } from "./ebookPhase20DryRunEngine";

export interface EBookPhase20Diagnostics {
  diagnosticsId: string;
  dryRunResult: EBookPhase20DryRunResult;
  mode: "dry-run";
}

export const buildPhase20Diagnostics = (
  dryRunResult: EBookPhase20DryRunResult,
): EBookPhase20Diagnostics => ({
  diagnosticsId: "phase20-diagnostics-placeholder",
  dryRunResult,
  mode: "dry-run",
});