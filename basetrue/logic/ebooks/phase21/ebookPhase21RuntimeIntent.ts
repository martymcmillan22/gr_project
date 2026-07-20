import type { EBookPhase20ExportEnvelope } from "../phase20/ebookPhase20Export";

export interface EBookPhase21RuntimeIntent {
  intentId: string;
  sourceExport: EBookPhase20ExportEnvelope;
  mode: "intent";
}

export const buildPhase21RuntimeIntent = (
  sourceExport: EBookPhase20ExportEnvelope,
): EBookPhase21RuntimeIntent => ({
  intentId: "phase21-runtime-intent-placeholder",
  sourceExport,
  mode: "intent",
});