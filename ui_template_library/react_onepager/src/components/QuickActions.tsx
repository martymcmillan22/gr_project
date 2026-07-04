export type QuickAction = {
  id: string;
  label: string;
  onClick: () => void;
};

export type QuickActionsProps = {
  actions: QuickAction[];
};

export function QuickActions({ actions }: QuickActionsProps) {
  return (
    <section className="gr-quick-actions">
      <h2>Quick Actions</h2>
      <div>
        {actions.map((action) => (
          <button key={action.id} type="button" onClick={action.onClick}>
            {action.label}
          </button>
        ))}
      </div>
    </section>
  );
}
