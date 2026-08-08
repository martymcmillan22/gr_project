import { useEffect, useState } from "react";

import { fetchRrCardSpec } from "../api/homepageApi";

export default function RrCardSpecPanel({ panelId = "rr-card-spec-panel" }) {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");
  const [layoutMode, setLayoutMode] = useState("compact");

  useEffect(() => {
    let active = true;
    fetchRrCardSpec()
      .then((nextPayload) => {
        if (active) {
          setPayload(nextPayload);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err?.message || "Unable to load RR card spec");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">RR Card Color Spec</p>
          <h2>Unified Card Layout Contract</h2>
        </div>
        <label className="semantic-select-field">
          Card Mode
          <select value={layoutMode} onChange={(event) => setLayoutMode(event.target.value)}>
            <option value="compact">Compact</option>
            <option value="expanded">Expanded</option>
          </select>
        </label>
      </div>

      {error ? <p className="status-line">{error}</p> : null}
      {payload ? (
        <div className="rr-card-spec-grid">
          {(payload.cards || []).map((item) => {
            const accent = item.spec?.accent_rgb || { r: 80, g: 80, b: 80 };
            return (
              <article
                key={item.compartment_id}
                className={layoutMode === "expanded" ? "is-expanded" : "is-compact"}
                style={{ borderTopColor: `rgb(${accent.r}, ${accent.g}, ${accent.b})` }}
              >
                <h3>{item.subject}</h3>
                <p>C{item.compartment_id} · {item.phase}</p>
                <p className="status-line">
                  Accent rgb({accent.r}, {accent.g}, {accent.b})
                </p>
                <p className="status-line">
                  Integrity palette: ok {item.spec?.integrity_indicator?.ok}, mismatch {item.spec?.integrity_indicator?.mismatch}
                </p>
                <div className="rr-node-chip-row">
                  <span>{item.subject}</span>
                  <span>{item.phase}</span>
                  <span>C{item.compartment_id}</span>
                </div>
                <div className="rr-node-chip-row">
                  <span>Workflow link-ready</span>
                  <span>SOP link-ready</span>
                  <span>Modes {(item.layout_modes || []).join(" / ") || "compact / expanded"}</span>
                </div>
              </article>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
