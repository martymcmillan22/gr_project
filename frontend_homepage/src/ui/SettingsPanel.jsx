export default function SettingsPanel({ settings, onChange }) {
  return (
    <section className="panel settings-panel">
      <h2>Settings Panel</h2>
      <label>
        <span>Notifications</span>
        <input
          type="checkbox"
          checked={Boolean(settings.notifications)}
          onChange={(event) => onChange("notifications", event.target.checked)}
        />
      </label>
      <label>
        <span>Dark Mode</span>
        <input
          type="checkbox"
          checked={Boolean(settings.dark_mode)}
          onChange={(event) => onChange("dark_mode", event.target.checked)}
        />
      </label>
    </section>
  );
}
