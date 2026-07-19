export function evaluateTierBundleIntegrity({
  tier,
  distributionProfile,
  distributionRule,
  packagingMetadata,
  integritySignatures,
}) {
  const expectedTier = String(tier || "");
  const profileBundle = distributionProfile?.bundleId || "";
  const ruleBundle = distributionRule?.bundleId || "";
  const profileChannel = distributionProfile?.channel || "";
  const ruleChannel = distributionRule?.channel || "";

  const checks = {
    tierDefined: Boolean(expectedTier),
    profileDefined: Boolean(distributionProfile?.profileId),
    ruleDefined: Boolean(distributionRule?.ruleId),
    channelAligned: Boolean(profileChannel) && profileChannel === ruleChannel,
    bundleAligned: Boolean(profileBundle) && profileBundle === ruleBundle,
    signatureAligned: Boolean(
      packagingMetadata?.buildSignature && integritySignatures?.bundleManifest?.signature,
    ),
  };

  return {
    tier: expectedTier,
    profileId: distributionProfile?.profileId || "",
    ruleId: distributionRule?.ruleId || "",
    profileChannel,
    ruleChannel,
    profileBundle,
    ruleBundle,
    packageBundleId: packagingMetadata?.bundleId || "",
    signaturePair: {
      packageSignature: packagingMetadata?.buildSignature || "",
      bundleSignature: integritySignatures?.bundleManifest?.signature || "",
    },
    checks,
    isValid: Object.values(checks).every(Boolean),
  };
}
