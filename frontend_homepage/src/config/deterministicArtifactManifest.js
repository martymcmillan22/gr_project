export const DETERMINISTIC_ARTIFACT_MANIFEST = Object.freeze({
  manifestId: "bt-artifacts-2026-07-18",
  appBundle: Object.freeze({
    id: "basetrue-homepage-app",
    entry: "static/homepage_app/main.js",
    html: "static/homepage_app/index.html",
    styles: "static/homepage_app/index.css",
  }),
  assets: Object.freeze({
    directory: "static/homepage_app",
    templatePattern: "static/homepage_app/template*.js",
  }),
  baselines: Object.freeze({
    routeDeterminism: "frontend_homepage/src/basetrue/appRouteDeterminism.test.tsx",
    visualDeterminism: "frontend_homepage/e2e/ux-visual-determinism.spec.ts",
  }),
  telemetryConfig: Object.freeze({
    namespace: "bt.semantic.telemetry",
    storeKey: "__btDeterministicTelemetry",
  }),
  releaseMetadata: Object.freeze({
    semanticVersion: "0.1.0",
    buildId: "gr-homepage-0.1.0+det.20260718.001",
    releaseChannel: "deterministic-stable",
  }),
});

export function getDeterministicArtifactManifest() {
  return {
    manifestId: DETERMINISTIC_ARTIFACT_MANIFEST.manifestId,
    appBundle: { ...DETERMINISTIC_ARTIFACT_MANIFEST.appBundle },
    assets: { ...DETERMINISTIC_ARTIFACT_MANIFEST.assets },
    baselines: { ...DETERMINISTIC_ARTIFACT_MANIFEST.baselines },
    telemetryConfig: { ...DETERMINISTIC_ARTIFACT_MANIFEST.telemetryConfig },
    releaseMetadata: { ...DETERMINISTIC_ARTIFACT_MANIFEST.releaseMetadata },
  };
}