const TIER_DEPLOYMENT_RULES = Object.freeze({
  novice: Object.freeze({
    enabled: true,
    defaultChannel: "novice-safe",
    allowedChannels: Object.freeze(["novice-safe", "staging"]),
  }),
  intermediate: Object.freeze({
    enabled: true,
    defaultChannel: "intermediate-safe",
    allowedChannels: Object.freeze(["intermediate-safe", "staging"]),
  }),
  studio: Object.freeze({
    enabled: true,
    defaultChannel: "studio-candidate",
    allowedChannels: Object.freeze(["studio-candidate", "staging", "production"]),
  }),
  enterprise: Object.freeze({
    enabled: true,
    defaultChannel: "enterprise-governed",
    allowedChannels: Object.freeze(["enterprise-governed", "staging", "production"]),
  }),
});

export function getTierDeploymentRules() {
  return {
    byTier: {
      novice: {
        ...TIER_DEPLOYMENT_RULES.novice,
        allowedChannels: [...TIER_DEPLOYMENT_RULES.novice.allowedChannels],
      },
      intermediate: {
        ...TIER_DEPLOYMENT_RULES.intermediate,
        allowedChannels: [...TIER_DEPLOYMENT_RULES.intermediate.allowedChannels],
      },
      studio: {
        ...TIER_DEPLOYMENT_RULES.studio,
        allowedChannels: [...TIER_DEPLOYMENT_RULES.studio.allowedChannels],
      },
      enterprise: {
        ...TIER_DEPLOYMENT_RULES.enterprise,
        allowedChannels: [...TIER_DEPLOYMENT_RULES.enterprise.allowedChannels],
      },
    },
  };
}