import { TierSelector } from "../../workflow/tier/tier_selector"
import {
  TemplateBasePath,
  TEMPLATE_BASE_PATHS,
  TemplateLoader,
} from "./template_loader"
import { ProfileKey } from "../../workflow/tier/tier_types"
import { getUIBundle } from "../tier/tier_ui_map"
import { routeUI } from "../tier/tier_ui_router"

function isTemplateBasePath(basePath: string): basePath is TemplateBasePath {
  return (TEMPLATE_BASE_PATHS as readonly string[]).includes(basePath)
}

function resolveInterfaceId(basePath: TemplateBasePath, profile: ProfileKey): string {
  if (basePath.startsWith("interface_")) {
    return basePath.replace("interface_", "")
  }

  if (basePath === "storytelling_dashboard") {
    return "storytelling"
  }

  if (profile === "public_free") {
    return "public_profile"
  }

  if (profile === "personal_free") {
    return "personal_profile"
  }

  return "corporation"
}

export function useTierTemplate(profile: ProfileKey, basePath: string) {
  const selector = new TierSelector(profile)
  const tier = selector.getCurrentTier()

  if (!isTemplateBasePath(basePath)) {
    return TemplateLoader.load("dashboard", tier)
  }

  const uiRoute = routeUI({
    tier,
    interfaceId: resolveInterfaceId(basePath, profile),
    templateGroup: basePath,
  })

  if (uiRoute.error || !uiRoute.mode) {
    return TemplateLoader.load(basePath, tier)
  }

  const bundle = getUIBundle(uiRoute.mode, tier)
  const allowedGroups = bundle.rules?.allowed_template_groups ?? []
  const resolvedBasePath = uiRoute.mode === "ui_diagnostics" ? "semantic_debugger" : basePath

  if (!allowedGroups.includes(resolvedBasePath as TemplateBasePath)) {
    return TemplateLoader.load(resolvedBasePath as TemplateBasePath, tier, {
      bypassTierCheck: uiRoute.mode === "ui_diagnostics",
    })
  }

  return TemplateLoader.load(resolvedBasePath as TemplateBasePath, tier, {
    bypassTierCheck: uiRoute.mode === "ui_diagnostics",
  })
}
