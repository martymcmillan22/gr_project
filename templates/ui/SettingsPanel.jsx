export default function SettingsPanel({ settings, onChange }) {
  return (
    <section className="homepage-card">
      <h3>Settings</h3>
      <label>
        <input
          type="checkbox"
          checked={Boolean(settings.notifications)}
          onChange={(event) => onChange("notifications", event.target.checked)}
        />
        Notifications
      </label>
      <label>
        <input
          type="checkbox"
          checked={Boolean(settings.dark_mode)}
          onChange={(event) => onChange("dark_mode", event.target.checked)}
        />
        Dark mode
      </label>
    </section>
  );
}
