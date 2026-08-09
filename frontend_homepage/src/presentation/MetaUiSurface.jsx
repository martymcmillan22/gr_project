import React from "react";

const META_COMPARTMENTS = [
  {
    index: 13,
    title: "Philosophy",
    body: "Read-only meta artifacts for first principles and worldview framing.",
    artifacts: ["Axioms", "Ethics", "Meaning"],
  },
  {
    index: 14,
    title: "Law & Governance: Insurance",
    body: "Read-only meta artifacts for policy, governance, and insurance logic.",
    artifacts: ["Policy", "Compliance", "Coverage"],
  },
  {
    index: 15,
    title: "Economics",
    body: "Read-only meta artifacts for value flow, incentives, and resource economics.",
    artifacts: ["Incentives", "Allocation", "Exchange"],
  },
  {
    index: 16,
    title: "Systemics",
    body: "Read-only meta artifacts for systems integration and cross-layer coherence.",
    artifacts: ["Feedback", "Systems", "Coherence"],
  },
];

const CRUD_OPERATIONS = ["Create", "Update", "Review", "Archive"];

export default function MetaUiSurface({ enterpriseAllowed = false }) {
  return (
    <section className="panel" data-testid="meta-ui-surface">
      <p className="eyebrow">Enterprise interface</p>
      <h2>Meta Interface</h2>
      <p className="status-line">Enterprise-only CRUD surface for meta artifacts with read-only compartments 13 through 16.</p>

      <section className="panel">
        <h3>Interface controls</h3>
        <p className="status-line">
          CRUD happens here. Compartments stay read-only and only reflect artifacts.
        </p>
        <p className="status-line">Enterprise access: {enterpriseAllowed ? "enabled" : "disabled"}</p>
        <div className="routing-controls">
          {CRUD_OPERATIONS.map((operation) => (
            <button key={operation} type="button" className="panel" disabled={!enterpriseAllowed}>
              {operation} Meta Artifact
            </button>
          ))}
        </div>
      </section>

      <section className="panel">
        <h3>Read-only meta compartments</h3>
        <p className="status-line">Compartments 13 to 16 are display surfaces only.</p>
        <div className="routing-controls">
          {META_COMPARTMENTS.map((compartment) => (
            <article key={compartment.index} className="panel">
              <p className="eyebrow">Compartment {compartment.index}</p>
              <h4>{compartment.title}</h4>
              <p className="status-line">{compartment.body}</p>
              <ul>
                {compartment.artifacts.map((artifact) => (
                  <li key={artifact}>{artifact}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h3>Office access model</h3>
        <p className="status-line">QC sees past and present-past. QA sees present-future and future. Meta remains enterprise-only.</p>
        <div className="routing-controls">
          <article className="panel">
            <h4>QC office</h4>
            <p className="status-line">Past and present-past compartment review.</p>
          </article>
          <article className="panel">
            <h4>QA office</h4>
            <p className="status-line">Present-future and future compartment review.</p>
          </article>
        </div>
      </section>
    </section>
  );
}