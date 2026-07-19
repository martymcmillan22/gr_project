export const DETERMINISTIC_INTEGRITY_SIGNATURES = Object.freeze({
  artifactManifest: Object.freeze({
    signatureId: "int-artifact-manifest-20260719-001",
    signature: "sig-sha256-9e7a7c4f3a9b7a6c12f1f8b0d2c1a3b4",
  }),
  bundleManifest: Object.freeze({
    signatureId: "int-bundle-manifest-20260719-001",
    signature: "sig-sha256-1d8e6f4f8f5a2b8c7d3e4f6a9b0c1d2e",
  }),
  tierDistributionProfiles: Object.freeze({
    signatureId: "int-tier-distribution-20260719-001",
    signature: "sig-sha256-4f2c1d8e6a9b0c1d2e3f4a5b6c7d8e9f",
  }),
  releaseMetadata: Object.freeze({
    signatureId: "int-release-metadata-20260719-001",
    signature: "sig-sha256-7c4f3a9b7a6c12f1f8b0d2c1a3b49e7a",
  }),
  telemetrySchema: Object.freeze({
    signatureId: "int-telemetry-schema-20260719-001",
    signature: "sig-sha256-2b8c7d3e4f6a9b0c1d2e3f4a5b6c7d8e",
  }),
});

export function getDeterministicIntegritySignatures() {
  return {
    artifactManifest: { ...DETERMINISTIC_INTEGRITY_SIGNATURES.artifactManifest },
    bundleManifest: { ...DETERMINISTIC_INTEGRITY_SIGNATURES.bundleManifest },
    tierDistributionProfiles: { ...DETERMINISTIC_INTEGRITY_SIGNATURES.tierDistributionProfiles },
    releaseMetadata: { ...DETERMINISTIC_INTEGRITY_SIGNATURES.releaseMetadata },
    telemetrySchema: { ...DETERMINISTIC_INTEGRITY_SIGNATURES.telemetrySchema },
  };
}