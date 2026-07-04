import {
    DashboardCard,
    FlowPanel,
    QuickActions,
    SettingsPanel,
    Taskboard,
} from "../../../ui_template_library/react_onepager/src/index";

export default function HomepageBackendPage() {
    return (
        <div style={{ display: "grid", gap: "1rem" }}>
            <DashboardCard title="HomepageBackend Dashboard" description="Generated one-pager shell" />
            <Taskboard
                title="HomepageBackend Tasks"
                tasks={[
                    { id: "1", label: "Connect API", status: "todo" },
                    { id: "2", label: "Review metrics", status: "doing" },
                ]}
            />
            <FlowPanel
                title="Data Flow"
                nodes={[
                    { id: "capture", label: "Capture" },
                    { id: "validate", label: "Validate" },
                    { id: "publish", label: "Publish" },
                ]}
            />
            <QuickActions
                actions={[
                    { id: "new", label: "New Item", onClick: () => {} },
                    { id: "sync", label: "Sync", onClick: () => {} },
                ]}
            />
            <SettingsPanel
                title="Preferences"
                fields={[
                    { id: "notifications", label: "Notifications", value: "enabled" },
                    { id: "visibility", label: "Visibility", value: "team" },
                ]}
            />
        </div>
    );
}
