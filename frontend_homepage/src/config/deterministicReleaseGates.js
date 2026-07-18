export const DETERMINISTIC_RELEASE_GATES = Object.freeze([
  Object.freeze({
    id: "unit-tests",
    command: "npm test",
    required: true,
  }),
  Object.freeze({
    id: "e2e-tests",
    command: "npm run test:e2e",
    required: true,
  }),
  Object.freeze({
    id: "production-build",
    command: "npm run build",
    required: true,
  }),
  Object.freeze({
    id: "snapshot-drift",
    command: "git status --short",
    required: true,
  }),
  Object.freeze({
    id: "telemetry-health",
    command: "telemetry-shape-check",
    required: true,
  }),
]);