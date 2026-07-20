import type { EBookPhase28ExportEnvelope } from "../phase28/ebookPhase28Export";

export interface EBookPhase29TransmissionPlan {
  planId: string;
  sourceExport: EBookPhase28ExportEnvelope;
  mode: "transmission";
}

export const buildPhase29TransmissionPlan = (
  sourceExport: EBookPhase28ExportEnvelope,
): EBookPhase29TransmissionPlan => ({
  planId: "phase29-transmission-plan-placeholder",
  sourceExport,
  mode: "transmission",
});