export function buildDeterministicArtifactVerification({
  artifactManifest,
  packagingMetadata,
  releaseMetadata,
  integritySignatures,
}) {
  return {
    verificationId: artifactManifest?.manifestId || "",
    artifactManifestId: artifactManifest?.manifestId || "",
    bundleId: packagingMetadata?.bundleId || "",
    releaseChannel: releaseMetadata?.channel || "",
    artifactSignatureId: integritySignatures?.artifactManifest?.signatureId || "",
    artifactSignature: integritySignatures?.artifactManifest?.signature || "",
    bundleSignatureId: integritySignatures?.bundleManifest?.signatureId || "",
    bundleSignature: integritySignatures?.bundleManifest?.signature || "",
    releaseSignatureId: integritySignatures?.releaseMetadata?.signatureId || "",
    releaseSignature: integritySignatures?.releaseMetadata?.signature || "",
    telemetrySignatureId: integritySignatures?.telemetrySchema?.signatureId || "",
    telemetrySignature: integritySignatures?.telemetrySchema?.signature || "",
  };
}
