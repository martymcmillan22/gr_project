const ROUTE_CHAIN = [
  "phase",
  "mlas",
  "color",
  "dewey",
  "industry",
  "metaphor",
  "category",
  "layout_archetype",
  "component_pack",
];

function pretty(value) {
  if (!value) {
    return "n/a";
  }
  return String(value).replace(/_/g, " ");
}

function MatrixLayout({ slide }) {
  return (
    <div className="routing-layout routing-layout-matrix">
      <article className="routing-cell">
        <h4>Phase</h4>
        <p>{pretty(slide.phase_resolved)}</p>
      </article>
      <article className="routing-cell">
        <h4>MLAS</h4>
        <p>{pretty(slide.mlas?.subject)} / {pretty(slide.mlas?.branch)}</p>
      </article>
      <article className="routing-cell">
        <h4>Dewey</h4>
        <p>{slide.dewey?.code ?? "n/a"}</p>
      </article>
      <article className="routing-cell">
        <h4>Industry</h4>
        <p>{pretty(slide.industry?.super_sector)}</p>
      </article>
    </div>
  );
}

function JourneyLayout({ slide }) {
  const steps = [
    `Phase: ${pretty(slide.phase_resolved)}`,
    `Metaphor: ${pretty(slide.metaphor)}`,
    `Category: ${pretty(slide.ui?.category_resolved)}`,
    `Layout: ${pretty(slide.ui?.layout_archetype)}`,
    `Pack: ${pretty(slide.ui?.component_pack)}`,
  ];

  return (
    <ol className="routing-layout routing-layout-journey">
      {steps.map((step) => (
        <li key={step}>{step}</li>
      ))}
    </ol>
  );
}

function PipelineLayout({ slide }) {
  const lanes = [
    { label: "Input", value: `${pretty(slide.mlas?.subject)} / ${pretty(slide.mlas?.branch)}` },
    { label: "Transform", value: `${pretty(slide.color_primary)} + ${pretty(slide.metaphor)}` },
    { label: "Route", value: `${pretty(slide.ui?.category_resolved)} / ${pretty(slide.ui?.layout_archetype)}` },
    { label: "Delivery", value: `${pretty(slide.ui?.component_pack)} / ${pretty(slide.industry?.page_signature)}` },
  ];

  return (
    <div className="routing-layout routing-layout-pipeline">
      {lanes.map((lane) => (
        <div key={lane.label} className="routing-pipeline-lane">
          <h4>{lane.label}</h4>
          <p>{lane.value}</p>
        </div>
      ))}
    </div>
  );
}

export default function RoutingLayoutPreview({ slide }) {
  if (!slide) {
    return null;
  }

  const phase = String(slide.phase_resolved || "").toLowerCase();

  return (
    <section className="routing-preview-panel panel">
      <p className="eyebrow">Resolved Routing</p>
      <h3>{slide.title || "Untitled Slide"}</h3>
      <div className="routing-chip-row">
        <span>phase: {pretty(slide.phase_resolved)}</span>
        <span>color: {pretty(slide.color_primary)}</span>
        <span>metaphor: {pretty(slide.metaphor)}</span>
        <span>category: {pretty(slide.ui?.category_resolved)}</span>
      </div>

      <div className="routing-chain">
        {ROUTE_CHAIN.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>

      {phase === "create" ? <MatrixLayout slide={slide} /> : null}
      {phase === "post" ? <JourneyLayout slide={slide} /> : null}
      {phase === "work" ? <PipelineLayout slide={slide} /> : null}
      {!phase || !["create", "post", "work"].includes(phase) ? <MatrixLayout slide={slide} /> : null}
    </section>
  );
}
