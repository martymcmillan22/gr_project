export default function QuickActions({ actions }) {
  return (
    <section className="homepage-card">
      <h3>Quick Actions</h3>
      <div className="homepage-actions">
        {actions.map((action) => (
          <button key={action.id} type="button" onClick={action.onClick}>
            {action.label}
          </button>
        ))}
      </div>
    </section>
  );
}
