import type { EBookPhase29TransmissionPlan } from "./ebookPhase29TransmissionPlan";

export interface EBookPhase29TransmissionResult {
  resultId: string;
  plan: EBookPhase29TransmissionPlan;
  transmittedLane: string;
  status: "ok" | "warning";
}

export const runPhase29Transmission = (
  plan: EBookPhase29TransmissionPlan,
): EBookPhase29TransmissionResult => ({
  resultId: "phase29-transmission-result-placeholder",
  plan,
  transmittedLane: plan.sourceExport.diagnostics.serializationResult.serializedLane,
  status: "ok",
});