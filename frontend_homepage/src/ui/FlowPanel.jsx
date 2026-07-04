export default function FlowPanel({ flow }) {
  const progress = Math.max(0, Math.min(100, flow?.progress ?? 0));
  const status = flow?.status || "active";
  const message = flow?.message || "In progress";

  return (
    <section className="panel">
      <h2>Flow Panel</h2>
      <p className="status-line">Status: <strong>{status}</strong></p>
      <div className="progress-track" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>
      <p>{message}</p>
    </section>
  );
}
