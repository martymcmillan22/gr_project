import type { EBookPhase20RuntimePlan } from "./ebookPhase20RuntimePlan";

export interface EBookPhase20DryRunResult {
  resultId: string;
  plan: EBookPhase20RuntimePlan;
  status: "ok" | "warning";
}

export const runPhase20DryRun = (
  plan: EBookPhase20RuntimePlan,
): EBookPhase20DryRunResult => ({
  resultId: "phase20-dryrun-result-placeholder",
  plan,
  status: "ok",
});