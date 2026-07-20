import type { EBookPhase26ExportEnvelope } from "../phase26/ebookPhase26Export";

export interface EBookPhase27RenderingPlan {
  planId: string;
  sourceExport: EBookPhase26ExportEnvelope;
  mode: "rendering";
}

export const buildPhase27RenderingPlan = (
  sourceExport: EBookPhase26ExportEnvelope,
): EBookPhase27RenderingPlan => ({
  planId: "phase27-rendering-plan-placeholder",
  sourceExport,
  mode: "rendering",
});