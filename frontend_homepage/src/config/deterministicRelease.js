const RELEASE_TIER_TAGS = Object.freeze([
  "novice",
  "intermediate",
  "studio",
  "enterprise",
]);

export const DETERMINISTIC_RELEASE_METADATA = Object.freeze({
  semanticVersion: "0.1.0",
  buildId: "gr-homepage-0.1.0+det.20260718.001",
  channel: "deterministic-stable",
  tierTags: RELEASE_TIER_TAGS,
});

export function getDeterministicReleaseMetadata() {
  return {
    semanticVersion: DETERMINISTIC_RELEASE_METADATA.semanticVersion,
    buildId: DETERMINISTIC_RELEASE_METADATA.buildId,
    channel: DETERMINISTIC_RELEASE_METADATA.channel,
    tierTags: [...DETERMINISTIC_RELEASE_METADATA.tierTags],
  };
}