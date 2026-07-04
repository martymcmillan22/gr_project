export default function QuickActions({ actions }) {
  return (
    <section className="panel">
      <h2>Quick Actions</h2>
      <div className="action-grid">
        {actions.map((action) => (
          <button key={action.id} className="action-btn" type="button" onClick={action.onClick}>
            {action.label}
          </button>
        ))}
      </div>
    </section>
  );
}
