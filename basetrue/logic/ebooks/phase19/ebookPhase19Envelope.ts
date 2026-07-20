import type { EBookPhase18ExportEnvelope } from "../phase18/ebookPhase18Export";

export interface EBookPhase19RuntimeEnvelope {
  generatedAt: string;
  envelopeId: string;
  phase18: EBookPhase18ExportEnvelope;
  mode: "static";
}