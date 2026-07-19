export function buildMultiLayerVerification({
  tier,
  semanticConsistency,
  tierBundleIntegrity,
  artifactVerification,
  distributionReport,
}) {
  const layerChecks = {
    semanticIdentity: Boolean(semanticConsistency?.semanticIdentity?.isValid),
    pipelineQpuConsistency: Boolean(semanticConsistency?.pipelineQpuConsistency?.isValid),
    distributionArtifactAlignment: Boolean(
      semanticConsistency?.distributionArtifactAlignment?.isValid,
    ),
    telemetrySchemaShape: Boolean(semanticConsistency?.telemetrySchemaShape?.isValid),
    tierBundleIntegrity: Boolean(tierBundleIntegrity?.isValid),
    artifactVerification: Boolean(artifactVerification?.verificationId),
    distributionReport: Boolean(distributionReport?.activeDistribution?.resolvedRuleId),
  };

  const failedLayers = Object.entries(layerChecks)
    .filter(([, isValid]) => !isValid)
    .map(([layer]) => layer);

  return {
    verificationId: `multi-layer-${tier || "unknown"}`,
    tier: tier || "",
    layerChecks,
    failedLayers,
    isValid: failedLayers.length === 0,
  };
}
