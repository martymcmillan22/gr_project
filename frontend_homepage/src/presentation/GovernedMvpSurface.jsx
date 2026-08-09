import React from "react";

const PHASES = [
  {
    key: "idea",
    label: "IdeaPanel",
    contract: "Minimal entry state",
    panel: "IspeIdeaScreen",
    sections: [
      "Identity and intentions",
      "Early deliverables",
      "Audience framing",
    ],
  },
  {
    key: "seed",
    label: "SeedPanel",
    contract: "Deterministic promotion path",
    panel: "LfoExpansionPanel",
    sections: [
      "Seed thesis",
      "Semantic alignment",
      "VA guidance",
    ],
  },
  {
    key: "project",
    label: "ProjectPanel",
    contract: "Timeline and workflow scaffolding",
    panel: "SopWorkflowScaffoldPanel",
    sections: [
      "Workflows and SOPs",
      "Timeline governance",
      "LFO surface review",
    ],
  },
  {
    key: "mvp",
    label: "MvpPanel",
    contract: "Investor and product-usage publication",
    panel: "PublishingLayerHooksPanel",
    sections: [
      "Investor book preview",
      "Product usage preview",
      "Identity publication",
    ],
  },
];

const TIERS = [
  {
    key: "studio",
    label: "StudioPanel",
    contract: "Studio tier surface",
    sections: ["Publishing surfaces", "Creator tier synthesis", "Narrative continuity"],
  },
  {
    key: "enterprise",
    label: "EnterprisePanel",
    contract: "Enterprise tier surface",
    sections: ["Multi-team workflows", "Executive synthesis", "Governed orchestration"],
  },
];

const GOVERNANCE_VALUES = [
  { label: "4 subjects", value: 4 },
  { label: "16 branches", value: 16 },
  { label: "64 industries", value: 64 },
  { label: "256 sub-industries", value: 256 },
];

const ACCEPTANCE_ORCHESTRATION = [
  { key: "idea", label: "Idea acceptance", status: "Ready for review" },
  { key: "seed", label: "Seed acceptance", status: "Aligned" },
  { key: "project", label: "Project acceptance", status: "Ready for review" },
  { key: "mvp", label: "MVP acceptance", status: "Ready for review" },
  { key: "studio", label: "Studio acceptance", status: "Ready for review" },
  { key: "enterprise", label: "Enterprise acceptance", status: "Ready for review" },
];

const OVERALL_READINESS = {
  score: 92,
  status: "Overall readiness",
  summary: "Governed and ready for the full MVP acceptance suite.",
};

export default function GovernedMvpSurface() {
  return (
    <section className="panel" data-testid="governed-mvp-surface">
      <p className="eyebrow">Governed MVP UI</p>
      <h2>Governed MVP UI Surfaces</h2>
      <p className="status-line">Deterministic UI scaffolding for the narrative-to-code blueprint.</p>

      <div className="routing-controls">
        {PHASES.map((phase) => (
          <article key={phase.key} className="panel">
            <h3>{phase.label}</h3>
            <p className="status-line">{phase.contract}</p>
            <p className="status-line">Panel: {phase.panel}</p>
            <ul>
              {phase.sections.map((section) => (
                <li key={section}>{section}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>

      <div className="routing-controls">
        {TIERS.map((tier) => (
          <article key={tier.key} className="panel">
            <h3>{tier.label}</h3>
            <p className="status-line">{tier.contract}</p>
            <ul>
              {tier.sections.map((section) => (
                <li key={section}>{section}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>

      <div className="routing-controls">
        <section className="panel">
          <h3>Unified acceptance orchestration</h3>
          <p className="status-line">Cross-tier acceptance summary for the full MVP narrative flow.</p>
          <p className="status-line">
            <strong>{OVERALL_READINESS.status}</strong>: {OVERALL_READINESS.score}% — {OVERALL_READINESS.summary}
          </p>
          <ul>
            {ACCEPTANCE_ORCHESTRATION.map((item) => (
              <li key={item.key}>
                <strong>{item.label}</strong>: {item.status}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="routing-controls">
        {GOVERNANCE_VALUES.map((item) => (
          <article key={item.label} className="panel">
            <h3>{item.label}</h3>
            <p className="status-line">Governed contract</p>
          </article>
        ))}
      </div>
    </section>
  );
}
