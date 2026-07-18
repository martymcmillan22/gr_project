export const DETERMINISTIC_ROLLBACK_POLICY = Object.freeze({
  fallbackChannel: "deterministic-safe",
  fallbackSemanticVersion: "0.1.0",
  currentBuildId: "gr-homepage-0.1.0+det.20260718.001",
  previousBuildId: "gr-homepage-0.1.0+det.20260711.001",
  previousSemanticVersion: "0.1.0",
  rollbackAllowed: true,
});

export function getDeterministicRollbackPolicy() {
  return {
    fallbackChannel: DETERMINISTIC_ROLLBACK_POLICY.fallbackChannel,
    fallbackSemanticVersion: DETERMINISTIC_ROLLBACK_POLICY.fallbackSemanticVersion,
    currentBuildId: DETERMINISTIC_ROLLBACK_POLICY.currentBuildId,
    previousBuildId: DETERMINISTIC_ROLLBACK_POLICY.previousBuildId,
    previousSemanticVersion: DETERMINISTIC_ROLLBACK_POLICY.previousSemanticVersion,
    rollbackAllowed: DETERMINISTIC_ROLLBACK_POLICY.rollbackAllowed,
  };
}