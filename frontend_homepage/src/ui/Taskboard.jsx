export default function Taskboard({ tasks }) {
  return (
    <section className="panel">
      <h2>Taskboard</h2>
      <ul className="task-list">
        {tasks.map((task) => (
          <li key={task.id}>
            <h3>{task.title}</h3>
            <p>{task.description}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
