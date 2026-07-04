export default function DashboardCard({ title, value }) {
  return (
    <article className="homepage-card homepage-dashboard-card">
      <div>
        <p className="homepage-kicker">Dashboard Card</p>
        <h2>{title}</h2>
      </div>
      <strong>{value}</strong>
    </article>
  );
}
