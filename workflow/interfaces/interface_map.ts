import { TierKey } from "../tier/tier_types"

import { getInterfaceCorporationRules } from "./interface_corporation"
import { getInterfaceMuseumRules } from "./interface_museum"
import { getInterfaceGardenRules } from "./interface_garden"
import { getInterfacePublicProfileRules } from "./interface_public_profile"
import { getInterfacePersonalProfileRules } from "./interface_personal_profile"
import { getInterfaceStorytellingRules } from "./interface_storytelling"

type InterfaceRules = ReturnType<typeof getInterfaceCorporationRules>

export const InterfaceMap: Partial<Record<string, (tier: TierKey) => InterfaceRules>> = {
  corporation: getInterfaceCorporationRules,
  museum: getInterfaceMuseumRules,
  garden: getInterfaceGardenRules,
  public_profile: getInterfacePublicProfileRules,
  personal_profile: getInterfacePersonalProfileRules,
  storytelling: getInterfaceStorytellingRules,
}

export function getInterfaceRules(interfaceId: string, tier: TierKey) {
  const fn = InterfaceMap[interfaceId]

  if (!fn) {
    return {
      error: true,
      reason: `Invalid interface ID: ${interfaceId}`,
      interfaceId,
      tier,
    }
  }

  return fn(tier)
}
