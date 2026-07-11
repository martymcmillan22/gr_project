export type SettingsField = {
  id: string;
  label: string;
  value: string;
};

export type SettingsPanelProps = {
  title: string;
  fields: SettingsField[];
};

export function SettingsPanel({ title, fields }: SettingsPanelProps) {
  return (
    <section className="gr-settings-panel">
      <h2>{title}</h2>
      <dl>
        {fields.map((field) => (
          <div key={field.id}>
            <dt>{field.label}</dt>
            <dd>{field.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
