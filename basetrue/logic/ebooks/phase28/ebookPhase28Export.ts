import type { EBookPhase28SerializationDiagnostics } from "./ebookPhase28SerializationDiagnostics";

export interface EBookPhase28ExportEnvelope {
  exportId: string;
  diagnostics: EBookPhase28SerializationDiagnostics;
  mode: "serialization";
}

export const buildPhase28ExportEnvelope = (
  diagnostics: EBookPhase28SerializationDiagnostics,
): EBookPhase28ExportEnvelope => ({
  exportId: "phase28-export-envelope-placeholder",
  diagnostics,
  mode: "serialization",
});