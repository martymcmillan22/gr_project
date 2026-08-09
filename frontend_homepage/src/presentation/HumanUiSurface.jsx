import React from "react";

const HUMAN_STEPS = [
  { key: "clarity", title: "Clarity", body: "A calm guided experience for humans." },
  { key: "progress", title: "Progress", body: "Simple steps and low cognitive load." },
  { key: "guidance", title: "Guidance", body: "Narrative-first help that reduces overwhelm." },
];

const HUMAN_PRINCIPLES = [
  {
    key: "creative-freedom",
    title: "Start with creative freedom",
    body: "Idea capture stays painless and structure stays out of the way until the user is ready.",
  },
  {
    key: "gradual-structure",
    title: "Increase structure gradually",
    body: "The UI introduces more governance only as the phase becomes more structured.",
  },
  {
    key: "calm-surface",
    title: "Keep the visible surface calm",
    body: "The screen stays visually attractive, legible, and non-overwhelming.",
  },
  {
    key: "veil",
    title: "Use Veil as progressive disclosure",
    body: "Complexity is present but only revealed when the user moves deeper into the flow.",
  },
];

const OFFICE_MODEL = [
  { key: "corporation", title: "Corporation / Twist", body: "Fast idea capture for high-energy entry." },
  { key: "museum", title: "Museum / QC office", body: "Seed review and approval with light structure." },
  { key: "garden", title: "Garden", body: "Project execution for Studio and Enterprise users." },
  { key: "meta", title: "Meta Interface", body: "Enterprise-only governance for read-only meta compartments." },
];

const PHASE_RHYTHM = [
  { key: "idea", title: "Idea", body: "Low structure, high energy, minimal resistance." },
  { key: "seed", title: "Seed", body: "Slightly more structure to validate direction." },
  { key: "project", title: "Project", body: "Governed execution with visible workflow detail." },
  { key: "mvp", title: "MVP", body: "Readiness checks, packaging, and review." },
  { key: "studio", title: "Studio", body: "Publishing and creator synthesis without visual heaviness." },
  { key: "enterprise", title: "Enterprise", body: "Orchestration and coordination that remains understandable." },
];

export default function HumanUiSurface() {
  return (
    <section className="panel" data-testid="human-ui-surface">
      <p className="eyebrow">Human experience</p>
      <h2>Human-first governed UI</h2>
      <p className="status-line">Guided path for humans with reduced complexity.</p>
      <div className="routing-controls">
        {HUMAN_STEPS.map((step) => (
          <article key={step.key} className="panel">
            <h3>{step.title}</h3>
            <p className="status-line">{step.body}</p>
          </article>
        ))}
      </div>
      <div className="routing-controls">
        {HUMAN_PRINCIPLES.map((principle) => (
          <article key={principle.key} className="panel">
            <h3>{principle.title}</h3>
            <p className="status-line">{principle.body}</p>
          </article>
        ))}
      </div>
      <section className="panel">
        <h3>Office model</h3>
        <p className="status-line">Twist, Museum, Garden, and Meta keep the human path legible.</p>
        <div className="routing-controls">
          {OFFICE_MODEL.map((office) => (
            <article key={office.key} className="panel">
              <h4>{office.title}</h4>
              <p className="status-line">{office.body}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="panel">
        <h3>Veil progression</h3>
        <p className="status-line">Complexity rises gradually as the user moves from creative capture to governed execution.</p>
        <div className="routing-controls">
          {PHASE_RHYTHM.map((phase) => (
            <article key={phase.key} className="panel">
              <h4>{phase.title}</h4>
              <p className="status-line">{phase.body}</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
