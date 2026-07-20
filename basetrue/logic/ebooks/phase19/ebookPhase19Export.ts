import type { EBookPhase19TypeCheck } from "./ebookPhase19TypeCheck";

export interface EBookPhase19ExportEnvelope {
  exportId: string;
  typeCheck: EBookPhase19TypeCheck;
  mode: "static";
}

export const buildPhase19ExportEnvelope = (
  typeCheck: EBookPhase19TypeCheck,
): EBookPhase19ExportEnvelope => ({
  exportId: "phase19-export-envelope-placeholder",
  typeCheck,
  mode: "static",
});