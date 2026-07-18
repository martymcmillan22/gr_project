import anchor from "../anchors/bt_anchor.json";

export function getQPUCount(compartmentIndex: number): number {
  return anchor.qpu_growth[String(compartmentIndex) as keyof typeof anchor.qpu_growth] ?? 0;
}
