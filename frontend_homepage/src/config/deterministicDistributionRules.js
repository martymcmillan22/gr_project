export const DETERMINISTIC_DISTRIBUTION_RULES = Object.freeze([
  Object.freeze({
    ruleId: "dist-rule-novice",
    tier: "novice",
    channel: "novice-safe",
    bundleId: "bundle.basetrue.novice.20260718",
  }),
  Object.freeze({
    ruleId: "dist-rule-intermediate",
    tier: "intermediate",
    channel: "intermediate-safe",
    bundleId: "bundle.basetrue.intermediate.20260718",
  }),
  Object.freeze({
    ruleId: "dist-rule-studio",
    tier: "studio",
    channel: "studio-candidate",
    bundleId: "bundle.basetrue.studio.20260718",
  }),
  Object.freeze({
    ruleId: "dist-rule-enterprise",
    tier: "enterprise",
    channel: "enterprise-governed",
    bundleId: "bundle.basetrue.enterprise.20260718",
  }),
]);

export function resolveDistributionRule(tier, channel) {
  return (
    DETERMINISTIC_DISTRIBUTION_RULES.find(
      (rule) => rule.tier === tier && rule.channel === channel,
    ) || null
  );
}