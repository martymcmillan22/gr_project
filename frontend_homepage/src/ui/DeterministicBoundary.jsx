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
      >
        {children}
      </div>
    );
  }
}

export function DeterministicLoadingSurface({ tier, surface, title, message }) {
  return (
    <DeterministicSurfaceFallback
      tier={tier}
      surface={surface}
      title={title}
      message={message}
      mode="loading"
    />
  );
}

export function DeterministicGuardedSurface({ tier, surface, shellClassName, loading, loadingTitle, loadingMessage, children }) {
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
    >
      {children}
    </div>
  );
}
