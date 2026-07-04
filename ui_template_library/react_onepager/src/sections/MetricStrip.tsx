export type MetricCard = {
  label: string;
  value: string;
};

export type MetricStripProps = {
  metrics: MetricCard[];
};

export function MetricStrip({ metrics }: MetricStripProps) {
  return (
    <section className="gr-metric-strip">
      {metrics.map((metric) => (
        <article key={`${metric.label}-${metric.value}`} className="gr-metric-card">
          <p>{metric.label}</p>
          <h3>{metric.value}</h3>
        </article>
      ))}
    </section>
  );
}
