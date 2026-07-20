import type { EBookPhase27RenderingResult } from "./ebookPhase27RenderingEngine";

export interface EBookPhase27RenderingDiagnostics {
  diagnosticsId: string;
  renderingResult: EBookPhase27RenderingResult;
  mode: "rendering";
}

export const buildPhase27RenderingDiagnostics = (
  renderingResult: EBookPhase27RenderingResult,
): EBookPhase27RenderingDiagnostics => ({
  diagnosticsId: "phase27-rendering-diagnostics-placeholder",
  renderingResult,
  mode: "rendering",
});