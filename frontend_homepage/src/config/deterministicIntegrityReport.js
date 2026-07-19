export function buildDeterministicIntegrityReport({
  tier,
  releaseMetadata,
  packagingMetadata,
  artifactManifest,
  integritySignatures,
  artifactVerification,
  tierBundleIntegrity,
  semanticConsistency,
  multiLayerVerification,
}) {
  const checks = {
    artifactVerification: Boolean(artifactVerification?.verificationId),
    tierBundleIntegrity: Boolean(tierBundleIntegrity?.isValid),
    semanticConsistency: Boolean(semanticConsistency?.isValid),
    multiLayerVerification: Boolean(multiLayerVerification?.isValid),
    telemetrySignature: Boolean(integritySignatures?.telemetrySchema?.signatureId),
  };

  return {
    reportId: `det-integrity-${tier || "unknown"}`,
    tier: tier || "",
    release: {
      semanticVersion: releaseMetadata?.semanticVersion || "",
      buildId: releaseMetadata?.buildId || "",
      channel: releaseMetadata?.channel || "",
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
    },
    signatures: {
      artifactSignatureId: integritySignatures?.artifactManifest?.signatureId || "",
      bundleSignatureId: integritySignatures?.bundleManifest?.signatureId || "",
      releaseSignatureId: integritySignatures?.releaseMetadata?.signatureId || "",
      telemetrySignatureId: integritySignatures?.telemetrySchema?.signatureId || "",
    },
    verification: {
      artifactVerificationId: artifactVerification?.verificationId || "",
      tierBundleIntegrityValid: Boolean(tierBundleIntegrity?.isValid),
      semanticConsistencyValid: Boolean(semanticConsistency?.isValid),
      multiLayerVerificationId: multiLayerVerification?.verificationId || "",
      multiLayerVerificationValid: Boolean(multiLayerVerification?.isValid),
    },
    checks,
    isValid: Object.values(checks).every(Boolean),
  };
}
