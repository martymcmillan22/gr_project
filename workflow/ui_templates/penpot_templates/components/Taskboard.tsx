export type TaskItem = {
  id: string;
  label: string;
  status: "todo" | "doing" | "done";
};

export type TaskboardProps = {
  title: string;
  tasks: TaskItem[];
};

export function Taskboard({ title, tasks }: TaskboardProps) {
  return (
    <section className="gr-taskboard">
      <h2>{title}</h2>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            <span>{task.label}</span>
            <em>{task.status}</em>
          </li>
        ))}
      </ul>
    </section>
  );
}
