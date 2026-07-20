import type { EBookPhase27ExportEnvelope } from "../phase27/ebookPhase27Export";

export interface EBookPhase28SerializationPlan {
  planId: string;
  sourceExport: EBookPhase27ExportEnvelope;
  mode: "serialization";
}

export const buildPhase28SerializationPlan = (
  sourceExport: EBookPhase27ExportEnvelope,
): EBookPhase28SerializationPlan => ({
  planId: "phase28-serialization-plan-placeholder",
  sourceExport,
  mode: "serialization",
});