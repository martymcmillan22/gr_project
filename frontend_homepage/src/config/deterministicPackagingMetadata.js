export const DETERMINISTIC_PACKAGING_METADATA = Object.freeze({
  packageId: "basetrue.semantic.distribution",
  packageVersion: "0.1.0",
  bundleId: "bundle.basetrue.semantic.20260718.001",
  releaseChannel: "deterministic-stable",
  buildSignature: "sig-sha256-0a6f26d90b70f1438e89f53f129db2b5",
  tierTags: Object.freeze(["novice", "intermediate", "studio", "enterprise"]),
});

export function getDeterministicPackagingMetadata() {
  return {
    packageId: DETERMINISTIC_PACKAGING_METADATA.packageId,
    packageVersion: DETERMINISTIC_PACKAGING_METADATA.packageVersion,
    bundleId: DETERMINISTIC_PACKAGING_METADATA.bundleId,
    releaseChannel: DETERMINISTIC_PACKAGING_METADATA.releaseChannel,
    buildSignature: DETERMINISTIC_PACKAGING_METADATA.buildSignature,
    tierTags: [...DETERMINISTIC_PACKAGING_METADATA.tierTags],
  };
}