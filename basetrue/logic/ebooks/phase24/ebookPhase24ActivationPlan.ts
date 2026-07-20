import type { EBookPhase23ExportEnvelope } from "../phase23/ebookPhase23Export";

export interface EBookPhase24ActivationPlan {
  planId: string;
  sourceExport: EBookPhase23ExportEnvelope;
  mode: "activation";
}

export const buildPhase24ActivationPlan = (
  sourceExport: EBookPhase23ExportEnvelope,
): EBookPhase24ActivationPlan => ({
  planId: "phase24-activation-plan-placeholder",
  sourceExport,
  mode: "activation",
});