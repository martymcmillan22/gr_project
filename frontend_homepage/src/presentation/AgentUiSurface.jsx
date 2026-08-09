import React from "react";

const AGENT_MODULES = [
  { key: "acceptance", title: "Acceptance orchestration", body: "Full governed acceptance flow for AI agents." },
  { key: "intelligence", title: "Unified intelligence", body: "Dense reasoning surfaces for agent operations." },
  { key: "synthesis", title: "MBSP synthesis", body: "High-detail synthesis and routing controls." },
];

export default function AgentUiSurface() {
  return (
    <section className="panel" data-testid="agent-ui-surface">
      <p className="eyebrow">Agent operations</p>
      <h2>Agent-first governed UI</h2>
      <p className="status-line">Dense, orchestrated, and acceptance-oriented for Copilot and VS Code AI.</p>
      <div className="routing-controls">
        {AGENT_MODULES.map((module) => (
          <article key={module.key} className="panel">
            <h3>{module.title}</h3>
            <p className="status-line">{module.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
