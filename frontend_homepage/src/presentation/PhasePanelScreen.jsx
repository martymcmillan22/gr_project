import React, { useMemo, useState } from "react";

const PANEL_CONTENT = {
  idea: {
    title: "IdeaPanel",
    subtitle: "Identity, intentions, and early deliverables",
    sections: [
      {
        heading: "Identity",
        body: "Capture the audience, purpose, and core editorial or product intent.",
      },
      {
        heading: "Intentions",
        body: "Frame the early narrative and define the first governed next steps.",
      },
      {
        heading: "Early deliverables",
        body: "Outline the initial outputs, milestones, and handcrafted starter assets.",
      },
    ],
  },
  seed: {
    title: "SeedPanel",
    subtitle: "Thesis, semantic alignment, and VA guidance",
    sections: [
      {
        heading: "Seed thesis",
        body: "Document the evolving thesis and preserve the deterministic core idea.",
      },
      {
        heading: "Semantic alignment",
        body: "Bind the seed to the MBSP intelligence and route it through the governed backbone.",
      },
      {
        heading: "VA guidance",
        body: "Surface the activation hints that help shape the next delivery actions.",
      },
    ],
  },
  project: {
    title: "ProjectPanel",
    subtitle: "Workflows, timeline governance, and LFO review",
    sections: [
      {
        heading: "Workflows",
        body: "Display the workflow scaffolding, associated SOPs, and delivery dependencies.",
      },
      {
        heading: "Timeline governance",
        body: "Show the governed timeline state and the progression toward the MVP milestone.",
      },
      {
        heading: "LFO review",
        body: "Expose the deterministic LFO surfaces and the route-level reasoning behind them.",
      },
    ],
  },
  mvp: {
    title: "MvpPanel",
    subtitle: "Investor and product-usage previews",
    sections: [
      {
        heading: "Investor preview",
        body: "Present the investor-facing narrative and the packaged value story.",
      },
      {
        heading: "Product usage preview",
        body: "Show how the system will be used operationally and where it creates value.",
      },
      {
        heading: "Identity publication",
        body: "Publish the deterministic identity package for downstream delivery surfaces.",
      },
    ],
  },
  studio: {
    title: "StudioPanel",
    subtitle: "Publishing surfaces and creator-tier synthesis",
    sections: [
      {
        heading: "Publishing surfaces",
        body: "Outline the creator-facing publishing interfaces and review surfaces.",
      },
      {
        heading: "Creator-tier synthesis",
        body: "Summarize the Studio tier synthesis and show the underlying governance state.",
      },
      {
        heading: "Narrative continuity",
        body: "Keep the story coherent across Studio and the wider deterministic platform.",
      },
    ],
  },
  enterprise: {
    title: "EnterprisePanel",
    subtitle: "Multi-team workflows and governed orchestration",
    sections: [
      {
        heading: "Multi-team workflows",
        body: "Surface the cross-team orchestration model and the operational coordination flows.",
      },
      {
        heading: "Executive synthesis",
        body: "Present the governance and delivery summary for enterprise-scale execution.",
      },
      {
        heading: "Governed orchestration",
        body: "Reveal the controlled release and routing model that ensures deterministic execution.",
      },
    ],
  },
};

export default function PhasePanelScreen({ phase = "idea" }) {
  const content = PANEL_CONTENT[phase] || PANEL_CONTENT.idea;
  const [values, setValues] = useState(() => ({
    identity: "Editorial intent",
    intentions: "Governed progression",
    deliverables: "Starter asset set",
    thesis: "Deterministic thesis",
    alignment: "MBSP aligned",
    guidance: "VA-ready",
    workflows: "Workflow scaffold",
    timeline: "Timeline active",
    lfo: "LFO review ready",
    investor: "Investor narrative",
    usage: "Product-value story",
    publication: "Identity package",
    publishing: "Studio publishing",
    synthesis: "Creator synthesis",
    continuity: "Narrative coherence",
    teams: "Cross-team orchestration",
    executive: "Executive summary",
    orchestration: "Governed release",
  }));

  const interactiveFields = useMemo(() => {
    switch (phase) {
      case "seed":
        return [
          { key: "thesis", label: "Thesis" },
          { key: "alignment", label: "Semantic alignment" },
          { key: "guidance", label: "VA guidance" },
        ];
      case "project":
        return [
          { key: "workflows", label: "Workflows" },
          { key: "timeline", label: "Timeline" },
          { key: "lfo", label: "LFO" },
        ];
      case "mvp":
        return [
          { key: "investor", label: "Investor preview" },
          { key: "usage", label: "Product usage" },
          { key: "publication", label: "Publication" },
        ];
      case "studio":
        return [
          { key: "publishing", label: "Publishing" },
          { key: "synthesis", label: "Synthesis" },
          { key: "continuity", label: "Continuity" },
        ];
      case "enterprise":
        return [
          { key: "teams", label: "Teams" },
          { key: "executive", label: "Executive" },
          { key: "orchestration", label: "Orchestration" },
        ];
      case "idea":
      default:
        return [
          { key: "identity", label: "Identity" },
          { key: "intentions", label: "Intentions" },
          { key: "deliverables", label: "Deliverables" },
        ];
    }
  }, [phase]);

  const moduleActions = useMemo(() => {
    switch (phase) {
      case "seed":
        return ["Review module", "Promote seed", "Route guidance"];
      case "project":
        return ["Review module", "Approve timeline", "Inspect LFO"];
      case "mvp":
        return ["Review module", "Publish preview", "Queue release"];
      case "studio":
        return ["Review module", "Publish studio", "Sync continuity"];
      case "enterprise":
        return ["Review module", "Escalate orchestration", "Approve teams"];
      case "idea":
      default:
        return ["Review module", "Add deliverable", "Confirm identity"];
    }
  }, [phase]);

  const subsystemSections = useMemo(() => {
    switch (phase) {
      case "seed":
        return [
          { heading: "Thesis builder", body: "Compose the deterministic thesis and route it through the semantic backbone." },
          { heading: "Semantic alignment engine", body: "Align the tier with MBSP intelligence and the governed narrative contract." },
          { heading: "VA guidance module", body: "Provide activation hints and evidence-backed next actions." },
        ];
      case "project":
        return [
          { heading: "Workflow editor", body: "Manage the SOP workflow structure and delivery dependencies." },
          { heading: "Timeline viewer", body: "Observe the governed progression toward the MVP milestone." },
          { heading: "LFO surface interactions", body: "Inspect routing signals and controlled review surfaces." },
        ];
      case "mvp":
        return [
          { heading: "Investor book preview", body: "Preview the investor-facing narrative and value story." },
          { heading: "Product usage preview", body: "Show how the system is used operationally and where value appears." },
          { heading: "Publication controls", body: "Publish and stage the output package for downstream delivery." },
        ];
      case "studio":
        return [
          { heading: "Publishing controls", body: "Shape the Studio-facing release and review surfaces." },
          { heading: "Creator-tier synthesis", body: "Merge the narrative state into a reusable creator-ready synthesis." },
          { heading: "Continuity review", body: "Ensure the creator surfaces preserve coherent messaging." },
        ];
      case "enterprise":
        return [
          { heading: "Multi-team workflow controls", body: "Coordinate the relationship between teams and the shared narrative contract." },
          { heading: "Orchestration interactions", body: "Drive the governed orchestration path across the enterprise surface." },
          { heading: "Executive summary view", body: "Provide a concise enterprise-level view of readiness and release state." },
        ];
      case "idea":
      default:
        return [
          { heading: "Identity editor", body: "Capture the core identity and intended audience in a dedicated editor surface." },
          { heading: "Intentions editor", body: "Define the governing intent and the initial narrative direction." },
          { heading: "Deliverable builder", body: "Create and refine the starter asset set for the next governed step." },
        ];
    }
  }, [phase]);

  const updateValue = (key, nextValue) => {
    setValues((current) => ({ ...current, [key]: nextValue }));
  };

  const acceptanceSummary = useMemo(() => {
    const filledCount = interactiveFields.filter((field) => (values[field.key] || "").trim().length > 0).length;
    const readinessScore = Math.min(100, Math.round((filledCount / interactiveFields.length) * 100));

    switch (phase) {
      case "seed":
        return {
          label: "Semantic readiness",
          status: readinessScore >= 70 ? "Ready for review" : "Needs more alignment",
          score: readinessScore,
        };
      case "project":
        return {
          label: "Workflow readiness",
          status: readinessScore >= 70 ? "Ready for review" : "Needs more workflow detail",
          score: readinessScore,
        };
      case "mvp":
        return {
          label: "Publication readiness",
          status: readinessScore >= 70 ? "Ready for review" : "Needs more preview detail",
          score: readinessScore,
        };
      case "studio":
        return {
          label: "Publishing readiness",
          status: readinessScore >= 70 ? "Ready for review" : "Needs more publishing detail",
          score: readinessScore,
        };
      case "enterprise":
        return {
          label: "Orchestration readiness",
          status: readinessScore >= 70 ? "Ready for review" : "Needs more orchestration detail",
          score: readinessScore,
        };
      case "idea":
      default:
        return {
          label: "Identity readiness",
          status: readinessScore >= 70 ? "Ready for review" : "Needs more identity detail",
          score: readinessScore,
        };
    }
  }, [interactiveFields, phase, values]);

  return (
    <main className="homepage-wrap">
      <section className="panel" data-testid={`phase-panel-${phase}`}>
        <p className="eyebrow">Governed UI</p>
        <h2>{content.title}</h2>
        <p className="status-line">{content.subtitle}</p>

        <div className="routing-controls">
          {interactiveFields.map((field) => (
            <label key={field.key} className="panel">
              <strong>{field.label}</strong>
              <input
                type="text"
                value={values[field.key] || ""}
                onChange={(event) => updateValue(field.key, event.target.value)}
              />
            </label>
          ))}
        </div>

        <div className="routing-controls">
          <section className="panel">
            <h3>Governed module actions</h3>
            <div className="routing-controls">
              {moduleActions.map((action) => (
                <button key={action} type="button" className="panel">
                  {action}
                </button>
              ))}
            </div>
          </section>
        </div>

        <div className="routing-controls">
          <section className="panel">
            <h3>Acceptance summary</h3>
            <p className="status-line">{acceptanceSummary.label}: {acceptanceSummary.score}%</p>
            <p className="status-line">{acceptanceSummary.status}</p>
          </section>
        </div>

        <div className="routing-controls">
          {subsystemSections.map((section) => (
            <article key={section.heading} className="panel">
              <h3>{section.heading}</h3>
              <p className="status-line">{section.body}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
