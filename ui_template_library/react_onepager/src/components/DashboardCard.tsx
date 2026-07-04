export type DashboardCardProps = {
  title: string;
  description: string;
  metric?: string;
};

export function DashboardCard({ title, description, metric }: DashboardCardProps) {
  return (
    <article className="gr-dashboard-card">
      <div>
        <p className="gr-kicker">Dashboard Card</p>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      {metric ? <strong>{metric}</strong> : null}
    </article>
  );
}
