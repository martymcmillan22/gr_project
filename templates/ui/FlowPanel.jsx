export default function FlowPanel({ flow }) {
  if (!flow) {
    return (
      <section className="homepage-card">
        <h3>Flow</h3>
        <p>No active flow yet.</p>
      </section>
    );
  }

  return (
    <section className="homepage-card">
      <h3>Flow</h3>
      <p>Status: {flow.status}</p>
      <p>Progress: {flow.progress}%</p>
      <p>{flow.message}</p>
    </section>
  );
}
