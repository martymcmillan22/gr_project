import type { EBookPhase20Diagnostics } from "./ebookPhase20Diagnostics";

export interface EBookPhase20ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase20Diagnostics;
  mode: "dry-run";
}

export const buildPhase20ExportEnvelope = (
  diagnostics: EBookPhase20Diagnostics,
): EBookPhase20ExportEnvelope => ({
  exportId: "phase20-export-envelope-placeholder",
  diagnostics,
  mode: "dry-run",
});