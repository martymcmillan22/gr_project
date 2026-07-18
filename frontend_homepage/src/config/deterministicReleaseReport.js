export function buildDeterministicReleaseReport({
  releaseMetadata,
  tierDeploymentRules,
  releaseGates,
  rollbackPolicy,
}) {
  const tiers = Object.keys(tierDeploymentRules?.byTier || {});
  const gateIds = Array.isArray(releaseGates) ? releaseGates.map((gate) => gate.id) : [];

  return {
    semanticVersion: releaseMetadata?.semanticVersion || "",
    buildId: releaseMetadata?.buildId || "",
    releaseChannel: releaseMetadata?.channel || "",
    tierTags: Array.isArray(releaseMetadata?.tierTags) ? [...releaseMetadata.tierTags] : [],
    tierDeploymentSummary: tiers.map((tier) => ({
      tier,
      enabled: Boolean(tierDeploymentRules?.byTier?.[tier]?.enabled),
      defaultChannel: tierDeploymentRules?.byTier?.[tier]?.defaultChannel || "",
    })),
    requiredGateIds: gateIds,
    rollback: {
      allowed: Boolean(rollbackPolicy?.rollbackAllowed),
      fallbackChannel: rollbackPolicy?.fallbackChannel || "",
      currentBuildId: rollbackPolicy?.currentBuildId || "",
      previousBuildId: rollbackPolicy?.previousBuildId || "",
    },
  };
}