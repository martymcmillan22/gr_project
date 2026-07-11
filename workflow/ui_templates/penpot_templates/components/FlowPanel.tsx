export type FlowNode = {
  id: string;
  label: string;
};

export type FlowPanelProps = {
  title: string;
  nodes: FlowNode[];
};

export function FlowPanel({ title, nodes }: FlowPanelProps) {
  return (
    <section className="gr-flow-panel">
      <h2>{title}</h2>
      <div>
        {nodes.map((node, index) => (
          <span key={node.id}>
            {node.label}
            {index < nodes.length - 1 ? " -> " : ""}
          </span>
        ))}
      </div>
    </section>
  );
}
