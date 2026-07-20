import type { EBookPhase28SerializationResult } from "./ebookPhase28SerializationEngine";

export interface EBookPhase28SerializationDiagnostics {
  diagnosticsId: string;
  serializationResult: EBookPhase28SerializationResult;
  mode: "serialization";
}

export const buildPhase28SerializationDiagnostics = (
  serializationResult: EBookPhase28SerializationResult,
): EBookPhase28SerializationDiagnostics => ({
  diagnosticsId: "phase28-serialization-diagnostics-placeholder",
  serializationResult,
  mode: "serialization",
});