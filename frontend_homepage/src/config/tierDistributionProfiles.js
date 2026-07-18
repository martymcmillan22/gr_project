const TIER_DISTRIBUTION_PROFILES = Object.freeze({
  novice: Object.freeze({
    profileId: "dist-novice-core",
    bundleId: "bundle.basetrue.novice.20260718",
    packagingMode: "guided",
    channel: "novice-safe",
  }),
  intermediate: Object.freeze({
    profileId: "dist-intermediate-core",
    bundleId: "bundle.basetrue.intermediate.20260718",
    packagingMode: "progressive",
    channel: "intermediate-safe",
  }),
  studio: Object.freeze({
    profileId: "dist-studio-extended",
    bundleId: "bundle.basetrue.studio.20260718",
    packagingMode: "creator",
    channel: "studio-candidate",
  }),
  enterprise: Object.freeze({
    profileId: "dist-enterprise-governed",
    bundleId: "bundle.basetrue.enterprise.20260718",
    packagingMode: "governed",
    channel: "enterprise-governed",
  }),
});

export function getTierDistributionProfiles() {
  return {
    byTier: {
      novice: { ...TIER_DISTRIBUTION_PROFILES.novice },
      intermediate: { ...TIER_DISTRIBUTION_PROFILES.intermediate },
      studio: { ...TIER_DISTRIBUTION_PROFILES.studio },
      enterprise: { ...TIER_DISTRIBUTION_PROFILES.enterprise },
    },
  };
}