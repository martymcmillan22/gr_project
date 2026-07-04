export default function DashboardCard({ title, value }) {
  return (
    <section className="panel dashboard-card">
      <div>
        <p className="eyebrow">Dashboard Of Dashboards</p>
        <h1>{title}</h1>
      </div>
      <div className="glow-value">{value}</div>
    </section>
  );
}
