import React from "react";

export function LayoutGrid({ columns = "2", gap = "16", children }) {
  const numericColumns = Number(columns) || 2;
  const numericGap = Number(gap) || 16;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${numericColumns}, minmax(0, 1fr))`,
        gap: `${numericGap}px`,
        marginBlock: "1rem",
      }}
    >
      {children}
    </div>
  );
}

export function Panel({ title = "Panel", tone = "neutral", children }) {
  const palette = {
    neutral: "#e2e8f0",
    primary: "#bfdbfe",
    success: "#bbf7d0",
    warning: "#fde68a",
    danger: "#fecaca",
  };

  return (
    <section
      style={{
        border: `1px solid ${palette[tone] || palette.neutral}`,
        borderRadius: "12px",
        padding: "0.9rem",
        background: "#ffffff",
      }}
    >
      <h4 style={{ marginTop: 0, marginBottom: "0.45rem" }}>{title}</h4>
      <div>{children}</div>
    </section>
  );
}

export function Quadrant({ label = "Q", emphasis = "low", children }) {
  const styleByEmphasis = {
    low: "#e2e8f0",
    medium: "#bae6fd",
    high: "#fed7aa",
    critical: "#fca5a5",
  };

  return (
    <article
      style={{
        border: `1px dashed ${styleByEmphasis[emphasis] || styleByEmphasis.low}`,
        borderRadius: "10px",
        padding: "0.7rem",
      }}
    >
      <strong style={{ display: "block", marginBottom: "0.35rem" }}>{label}</strong>
      <div>{children}</div>
    </article>
  );
}

export function ComponentPreview({ component = "Unknown", status = "draft" }) {
  return (
    <div
      style={{
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        fontSize: "0.85rem",
        border: "1px solid #e2e8f0",
        borderRadius: "8px",
        padding: "0.45rem 0.6rem",
        background: "#f8fafc",
      }}
    >
      preview: {component} ({status})
    </div>
  );
}
