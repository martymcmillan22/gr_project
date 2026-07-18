export function buildDeterministicDistributionReport({
  releaseMetadata,
  packagingMetadata,
  artifactManifest,
  tierDistributionProfiles,
  activeTier,
  activeDistributionRule,
}) {
  const activeProfile = tierDistributionProfiles?.byTier?.[activeTier] || null;

  return {
    activeTier,
    release: {
      semanticVersion: releaseMetadata?.semanticVersion || "",
      buildId: releaseMetadata?.buildId || "",
      releaseChannel: releaseMetadata?.channel || "",
    },
    packaging: {
      packageId: packagingMetadata?.packageId || "",
      packageVersion: packagingMetadata?.packageVersion || "",
      bundleId: packagingMetadata?.bundleId || "",
      buildSignature: packagingMetadata?.buildSignature || "",
    },
    artifacts: {
      manifestId: artifactManifest?.manifestId || "",
      appBundleId: artifactManifest?.appBundle?.id || "",
      appBundleEntry: artifactManifest?.appBundle?.entry || "",
    },
    activeDistribution: {
      profileId: activeProfile?.profileId || "",
      profileBundleId: activeProfile?.bundleId || "",
      channel: activeProfile?.channel || "",
      packagingMode: activeProfile?.packagingMode || "",
      resolvedRuleId: activeDistributionRule?.ruleId || "",
      resolvedBundleId: activeDistributionRule?.bundleId || "",
    },
  };
}