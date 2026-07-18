import { TierKey } from "../tier/tier_types"

import { getCompartment01Rules } from "./compartments/compartment_01"
import { getCompartment02Rules } from "./compartments/compartment_02"
import { getCompartment03Rules } from "./compartments/compartment_03"
import { getCompartment04Rules } from "./compartments/compartment_04"
import { getCompartment05Rules } from "./compartments/compartment_05"
import { getCompartment06Rules } from "./compartments/compartment_06"
import { getCompartment07Rules } from "./compartments/compartment_07"
import { getCompartment08Rules } from "./compartments/compartment_08"
import { getCompartment09Rules } from "./compartments/compartment_09"
import { getCompartment10Rules } from "./compartments/compartment_10"
import { getCompartment11Rules } from "./compartments/compartment_11"
import { getCompartment12Rules } from "./compartments/compartment_12"
import { getCompartment13Rules } from "./compartments/compartment_13"
import { getCompartment14Rules } from "./compartments/compartment_14"
import { getCompartment15Rules } from "./compartments/compartment_15"
import { getCompartment16Rules } from "./compartments/compartment_16"
import { getCompartment17Rules } from "./compartments/compartment_17"
import { getCompartment18Rules } from "./compartments/compartment_18"
import { getCompartment19Rules } from "./compartments/compartment_19"
import { getCompartment20Rules } from "./compartments/compartment_20"
import { getCompartment21Rules } from "./compartments/compartment_21"
import { getCompartment22Rules } from "./compartments/compartment_22"
import { getCompartment23Rules } from "./compartments/compartment_23"
import { getCompartment24Rules } from "./compartments/compartment_24"

type CompartmentRules = ReturnType<typeof getCompartment01Rules>

export const CompartmentMap: Partial<Record<number, (tier: TierKey) => CompartmentRules>> = {
  1: getCompartment01Rules,
  2: getCompartment02Rules,
  3: getCompartment03Rules,
  4: getCompartment04Rules,
  5: getCompartment05Rules,
  6: getCompartment06Rules,
  7: getCompartment07Rules,
  8: getCompartment08Rules,
  9: getCompartment09Rules,
  10: getCompartment10Rules,
  11: getCompartment11Rules,
  12: getCompartment12Rules,
  13: getCompartment13Rules,
  14: getCompartment14Rules,
  15: getCompartment15Rules,
  16: getCompartment16Rules,
  17: getCompartment17Rules,
  18: getCompartment18Rules,
  19: getCompartment19Rules,
  20: getCompartment20Rules,
  21: getCompartment21Rules,
  22: getCompartment22Rules,
  23: getCompartment23Rules,
  24: getCompartment24Rules,
}

export function getCompartmentRules(compartmentId: number, tier: TierKey) {
  const fn = CompartmentMap[compartmentId]

  if (!fn) {
    return {
      error: true,
      reason: `Invalid compartment ID: ${compartmentId}. Must be between 1 and 24.`,
      id: compartmentId,
      tier,
    }
  }

  return fn(tier)
}
