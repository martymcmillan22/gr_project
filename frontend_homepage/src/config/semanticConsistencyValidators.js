function hasText(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isSha256Signature(signature = "") {
  return String(signature).startsWith("sig-sha256-");
}

export function validateSemanticIdentity({ tier, releaseMetadata, packagingMetadata }) {
  const semanticVersion = releaseMetadata?.semanticVersion || "";
  const packageVersion = packagingMetadata?.packageVersion || "";
  const bundleId = packagingMetadata?.bundleId || "";

  const checks = {
    tierDefined: hasText(tier),
    semanticVersionDefined: hasText(semanticVersion),
    packageVersionDefined: hasText(packageVersion),
    versionAligned: semanticVersion === packageVersion,
    bundleDefined: hasText(bundleId),
  };

  return {
    semanticVersion,
    packageVersion,
    bundleId,
    checks,
    isValid: Object.values(checks).every(Boolean),
  };
}

export function validatePipelineQpuConsistency({ distributionProfile, distributionRule, tierBundleIntegrity }) {
  const profileMode = distributionProfile?.packagingMode || "";
  const profileChannel = distributionProfile?.channel || "";
  const ruleChannel = distributionRule?.channel || "";

  const checks = {
    profileModeDefined: hasText(profileMode),
    profileChannelDefined: hasText(profileChannel),
    ruleChannelDefined: hasText(ruleChannel),
    channelAligned: profileChannel === ruleChannel,
    tierBundleIntegrityValid: Boolean(tierBundleIntegrity?.isValid),
  };

  return {
    packagingMode: profileMode,
    profileChannel,
    ruleChannel,
    checks,
    isValid: Object.values(checks).every(Boolean),
  };
}

export function validateDistributionArtifactAlignment({
  releaseMetadata,
  packagingMetadata,
  artifactManifest,
  distributionProfile,
  distributionRule,
}) {
  const releaseChannel = releaseMetadata?.channel || "";
  const profileChannel = distributionProfile?.channel || "";
  const ruleChannel = distributionRule?.channel || "";
  const profileBundleId = distributionProfile?.bundleId || "";
  const ruleBundleId = distributionRule?.bundleId || "";
  const artifactBundleEntry = artifactManifest?.appBundle?.entry || "";

  const checks = {
    releaseChannelDefined: hasText(releaseChannel),
    profileChannelDefined: hasText(profileChannel),
    ruleChannelDefined: hasText(ruleChannel),
    channelAligned: profileChannel === ruleChannel,
    profileBundleDefined: hasText(profileBundleId),
    ruleBundleDefined: hasText(ruleBundleId),
    bundleAligned: profileBundleId === ruleBundleId,
    packagingBundleDefined: hasText(packagingMetadata?.bundleId || ""),
    artifactEntryDefined: hasText(artifactBundleEntry),
  };

  return {
    releaseChannel,
    profileChannel,
    ruleChannel,
    profileBundleId,
    ruleBundleId,
    artifactBundleEntry,
    checks,
    isValid: Object.values(checks).every(Boolean),
  };
}

export function validateTelemetrySchemaShape({ integritySignatures }) {
  const telemetrySignatureId = integritySignatures?.telemetrySchema?.signatureId || "";
  const telemetrySignature = integritySignatures?.telemetrySchema?.signature || "";

  const checks = {
    telemetrySignatureIdDefined: hasText(telemetrySignatureId),
    telemetrySignatureDefined: hasText(telemetrySignature),
    telemetrySignatureHashShape: isSha256Signature(telemetrySignature),
  };

  return {
    telemetrySignatureId,
    telemetrySignature,
    checks,
    isValid: Object.values(checks).every(Boolean),
  };
}

export function buildSemanticConsistencyValidators({
  tier,
  releaseMetadata,
  packagingMetadata,
  artifactManifest,
  distributionProfile,
  distributionRule,
  integritySignatures,
  tierBundleIntegrity,
}) {
  const semanticIdentity = validateSemanticIdentity({
    tier,
    releaseMetadata,
    packagingMetadata,
  });
  const pipelineQpuConsistency = validatePipelineQpuConsistency({
    distributionProfile,
    distributionRule,
    tierBundleIntegrity,
  });
  const distributionArtifactAlignment = validateDistributionArtifactAlignment({
    releaseMetadata,
    packagingMetadata,
    artifactManifest,
    distributionProfile,
    distributionRule,
  });
  const telemetrySchemaShape = validateTelemetrySchemaShape({ integritySignatures });

  const checks = {
    semanticIdentity: semanticIdentity.isValid,
    pipelineQpuConsistency: pipelineQpuConsistency.isValid,
    distributionArtifactAlignment: distributionArtifactAlignment.isValid,
    telemetrySchemaShape: telemetrySchemaShape.isValid,
  };

  return {
    validationId: `sem-consistency-${tier || "unknown"}`,
    tier: tier || "",
    semanticIdentity,
    pipelineQpuConsistency,
    distributionArtifactAlignment,
    telemetrySchemaShape,
    checks,
    isValid: Object.values(checks).every(Boolean),
  };
}
