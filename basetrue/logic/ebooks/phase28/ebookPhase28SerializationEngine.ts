import type { EBookPhase28SerializationPlan } from "./ebookPhase28SerializationPlan";

export interface EBookPhase28SerializationResult {
  resultId: string;
  plan: EBookPhase28SerializationPlan;
  serializedLane: string;
  status: "ok" | "warning";
}

export const runPhase28Serialization = (
  plan: EBookPhase28SerializationPlan,
): EBookPhase28SerializationResult => ({
  resultId: "phase28-serialization-result-placeholder",
  plan,
  serializedLane: plan.sourceExport.diagnostics.renderingResult.renderedLane,
  status: "ok",
});