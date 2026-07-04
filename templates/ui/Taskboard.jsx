export default function Taskboard({ tasks }) {
  return (
    <section className="homepage-card">
      <h3>Taskboard</h3>
      <ul className="homepage-task-list">
        {tasks.map((task) => (
          <li key={task.id}>
            <strong>{task.title}</strong>
            <p>{task.description}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
