import React from "react";
import {
  emitDeterministicTelemetry,
  incrementDeterministicMetric,
  reportDeterministicError,
  startDeterministicTimer,
  stopDeterministicTimer,
} from "./deterministicTelemetry";

function joinClassNames(...values) {
  return values.filter(Boolean).join(" ");
}

export function DeterministicSurfaceFallback({
  tier,
  surface,
  title,
  message,
  mode = "error",
  details,
  releaseMetadata,
  deploymentPolicy,
  rollbackPolicy,
  packagingMetadata,
  artifactManifest,
  distributionProfile,
  distributionRule,
  distributionReport,
  integritySignatures,
  artifactVerification,
  tierBundleIntegrity,
}) {
  React.useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "deterministic.fallback.rendered",
      tier,
      surface,
      payload: {
        mode,
      },
    });
    incrementDeterministicMetric("deterministic.fallback.activations", {
      tier,
      surface,
      mode,
    });
  }, [mode, surface, tier]);

  return (
    <section
      className={joinClassNames(
        "det-surface-fallback",
        `det-surface-fallback--${mode}`,
        `det-surface-fallback--${tier}`,
      )}
      data-tier={tier}
      data-surface={surface}
      data-release-version={releaseMetadata?.semanticVersion || ""}
      data-release-build={releaseMetadata?.buildId || ""}
      data-release-channel={releaseMetadata?.channel || ""}
      data-release-deploy-enabled={deploymentPolicy?.enabled ? "true" : "false"}
      data-release-deploy-channel={deploymentPolicy?.defaultChannel || ""}
      data-release-rollback-allowed={rollbackPolicy?.rollbackAllowed ? "true" : "false"}
      data-release-previous-build={rollbackPolicy?.previousBuildId || ""}
      data-package-bundle-id={packagingMetadata?.bundleId || ""}
      data-package-signature={packagingMetadata?.buildSignature || ""}
      data-artifact-manifest-id={artifactManifest?.manifestId || ""}
      data-distribution-profile={distributionProfile?.profileId || ""}
      data-distribution-mode={distributionProfile?.packagingMode || ""}
      data-distribution-rule={distributionRule?.ruleId || ""}
      data-distribution-bundle={distributionRule?.bundleId || ""}
      data-distribution-report-tier={distributionReport?.activeTier || ""}
      data-distribution-report-channel={distributionReport?.activeDistribution?.channel || ""}
      data-integrity-artifact-signature={integritySignatures?.artifactManifest?.signature || ""}
      data-integrity-bundle-signature={integritySignatures?.bundleManifest?.signature || ""}
      data-integrity-release-signature={integritySignatures?.releaseMetadata?.signature || ""}
      data-integrity-telemetry-signature={integritySignatures?.telemetrySchema?.signature || ""}
      data-artifact-verification-id={artifactVerification?.verificationId || ""}
      data-tier-bundle-integrity-valid={tierBundleIntegrity?.isValid ? "true" : "false"}
      data-tier-bundle-integrity-profile={tierBundleIntegrity?.profileId || ""}
      role={mode === "loading" ? "status" : "alert"}
      aria-live={mode === "loading" ? "polite" : "assertive"}
      aria-atomic="true"
    >
      <p className="det-surface-fallback-eyebrow">Deterministic {surface}</p>
      <h3>{title}</h3>
      <p className="status-line">{message}</p>
      <div className="det-surface-fallback-skeleton" aria-hidden="true">
        <span className="det-surface-skeleton-row" />
        <span className="det-surface-skeleton-row" />
        <span className="det-surface-skeleton-row" />
      </div>
      {details ? <p className="status-line">{details}</p> : null}
    </section>
  );
}

export class DeterministicErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(_error, _errorInfo) {
    // Deterministic fallback is rendered by state transition only.
    reportDeterministicError({
      tier: this.props.tier,
      surface: this.props.surface,
      code: "boundary_catch",
    });
  }

  render() {
    const {
      children,
      tier,
      surface,
      fallbackTitle,
      fallbackMessage,
      fallbackDetails,
      shellClassName,
      releaseMetadata,
      deploymentPolicy,
      rollbackPolicy,
      packagingMetadata,
      artifactManifest,
      distributionProfile,
      distributionRule,
      distributionReport,
      integritySignatures,
      artifactVerification,
      tierBundleIntegrity,
    } = this.props;

    if (this.state.hasError) {
      return (
        <DeterministicSurfaceFallback
          tier={tier}
          surface={surface}
          title={fallbackTitle}
          message={fallbackMessage}
          details={fallbackDetails}
          mode="error"
          releaseMetadata={releaseMetadata}
          deploymentPolicy={deploymentPolicy}
          rollbackPolicy={rollbackPolicy}
          packagingMetadata={packagingMetadata}
          artifactManifest={artifactManifest}
          distributionProfile={distributionProfile}
          distributionRule={distributionRule}
          distributionReport={distributionReport}
          integritySignatures={integritySignatures}
          artifactVerification={artifactVerification}
          tierBundleIntegrity={tierBundleIntegrity}
        />
      );
    }

    return (
      <div
        className={joinClassNames(
          "det-boundary-shell",
          `det-boundary-shell--${tier}`,
          shellClassName,
        )}
        data-tier={tier}
        data-surface={surface}
        data-release-version={releaseMetadata?.semanticVersion || ""}
        data-release-build={releaseMetadata?.buildId || ""}
        data-release-channel={releaseMetadata?.channel || ""}
        data-release-deploy-enabled={deploymentPolicy?.enabled ? "true" : "false"}
        data-release-deploy-channel={deploymentPolicy?.defaultChannel || ""}
        data-release-rollback-allowed={rollbackPolicy?.rollbackAllowed ? "true" : "false"}
        data-release-previous-build={rollbackPolicy?.previousBuildId || ""}
        data-package-bundle-id={packagingMetadata?.bundleId || ""}
        data-package-signature={packagingMetadata?.buildSignature || ""}
        data-artifact-manifest-id={artifactManifest?.manifestId || ""}
        data-distribution-profile={distributionProfile?.profileId || ""}
        data-distribution-mode={distributionProfile?.packagingMode || ""}
        data-distribution-rule={distributionRule?.ruleId || ""}
        data-distribution-bundle={distributionRule?.bundleId || ""}
        data-distribution-report-tier={distributionReport?.activeTier || ""}
        data-distribution-report-channel={distributionReport?.activeDistribution?.channel || ""}
        data-integrity-artifact-signature={integritySignatures?.artifactManifest?.signature || ""}
        data-integrity-bundle-signature={integritySignatures?.bundleManifest?.signature || ""}
        data-integrity-release-signature={integritySignatures?.releaseMetadata?.signature || ""}
        data-integrity-telemetry-signature={integritySignatures?.telemetrySchema?.signature || ""}
        data-artifact-verification-id={artifactVerification?.verificationId || ""}
        data-tier-bundle-integrity-valid={tierBundleIntegrity?.isValid ? "true" : "false"}
        data-tier-bundle-integrity-profile={tierBundleIntegrity?.profileId || ""}
      >
        {children}
      </div>
    );
  }
}

export function DeterministicLoadingSurface({
  tier,
  surface,
  title,
  message,
  releaseMetadata,
  deploymentPolicy,
  rollbackPolicy,
  packagingMetadata,
  artifactManifest,
  distributionProfile,
  distributionRule,
  distributionReport,
  integritySignatures,
  artifactVerification,
  tierBundleIntegrity,
}) {
  return (
    <DeterministicSurfaceFallback
      tier={tier}
      surface={surface}
      title={title}
      message={message}
      mode="loading"
      releaseMetadata={releaseMetadata}
      deploymentPolicy={deploymentPolicy}
      rollbackPolicy={rollbackPolicy}
      packagingMetadata={packagingMetadata}
      artifactManifest={artifactManifest}
      distributionProfile={distributionProfile}
      distributionRule={distributionRule}
      distributionReport={distributionReport}
      integritySignatures={integritySignatures}
      artifactVerification={artifactVerification}
      tierBundleIntegrity={tierBundleIntegrity}
    />
  );
}

export function DeterministicGuardedSurface({
  tier,
  surface,
  shellClassName,
  loading,
  loadingTitle,
  loadingMessage,
  children,
  releaseMetadata,
  deploymentPolicy,
  rollbackPolicy,
  packagingMetadata,
  artifactManifest,
  distributionProfile,
  distributionRule,
  distributionReport,
  integritySignatures,
  artifactVerification,
  tierBundleIntegrity,
}) {
  const loadingTimerRef = React.useRef("");

  React.useEffect(() => {
    if (loading) {
      loadingTimerRef.current = startDeterministicTimer("deterministic.loading.duration", {
        tier,
        surface,
      });
      emitDeterministicTelemetry({
        eventName: "deterministic.loading.started",
        tier,
        surface,
      });
      return;
    }

    if (loadingTimerRef.current) {
      const durationMs = stopDeterministicTimer(loadingTimerRef.current);
      emitDeterministicTelemetry({
        eventName: "deterministic.loading.completed",
        tier,
        surface,
        payload: {
          durationMs,
        },
      });
      loadingTimerRef.current = "";
    }
  }, [loading, surface, tier]);

  if (loading) {
    return (
      <DeterministicLoadingSurface
        tier={tier}
        surface={surface}
        title={loadingTitle || "Deterministic loading surface"}
        message={loadingMessage || "Deterministic loading state is active while preserving surface stability."}
        releaseMetadata={releaseMetadata}
        deploymentPolicy={deploymentPolicy}
        rollbackPolicy={rollbackPolicy}
        packagingMetadata={packagingMetadata}
        artifactManifest={artifactManifest}
        distributionProfile={distributionProfile}
        distributionRule={distributionRule}
        distributionReport={distributionReport}
        integritySignatures={integritySignatures}
        artifactVerification={artifactVerification}
        tierBundleIntegrity={tierBundleIntegrity}
      />
    );
  }

  return (
    <div
      className={joinClassNames(
        "det-guard-shell",
        `det-guard-shell--${tier}`,
        shellClassName,
      )}
      data-tier={tier}
      data-surface={surface}
        data-release-version={releaseMetadata?.semanticVersion || ""}
        data-release-build={releaseMetadata?.buildId || ""}
        data-release-channel={releaseMetadata?.channel || ""}
        data-release-deploy-enabled={deploymentPolicy?.enabled ? "true" : "false"}
        data-release-deploy-channel={deploymentPolicy?.defaultChannel || ""}
        data-release-rollback-allowed={rollbackPolicy?.rollbackAllowed ? "true" : "false"}
        data-release-previous-build={rollbackPolicy?.previousBuildId || ""}
        data-package-bundle-id={packagingMetadata?.bundleId || ""}
        data-package-signature={packagingMetadata?.buildSignature || ""}
        data-artifact-manifest-id={artifactManifest?.manifestId || ""}
        data-distribution-profile={distributionProfile?.profileId || ""}
        data-distribution-mode={distributionProfile?.packagingMode || ""}
        data-distribution-rule={distributionRule?.ruleId || ""}
        data-distribution-bundle={distributionRule?.bundleId || ""}
        data-distribution-report-tier={distributionReport?.activeTier || ""}
        data-distribution-report-channel={distributionReport?.activeDistribution?.channel || ""}
        data-integrity-artifact-signature={integritySignatures?.artifactManifest?.signature || ""}
        data-integrity-bundle-signature={integritySignatures?.bundleManifest?.signature || ""}
        data-integrity-release-signature={integritySignatures?.releaseMetadata?.signature || ""}
        data-integrity-telemetry-signature={integritySignatures?.telemetrySchema?.signature || ""}
        data-artifact-verification-id={artifactVerification?.verificationId || ""}
        data-tier-bundle-integrity-valid={tierBundleIntegrity?.isValid ? "true" : "false"}
        data-tier-bundle-integrity-profile={tierBundleIntegrity?.profileId || ""}
    >
      {children}
    </div>
  );
}
