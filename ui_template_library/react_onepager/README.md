# One-Pager UI Template Library

Reusable React templates for new one-pager apps.

## Included Components
- Taskboard
- FlowPanel
- SettingsPanel
- QuickActions
- DashboardCard

## Quick Usage

```tsx
import {
  DashboardCard,
  FlowPanel,
  QuickActions,
  SettingsPanel,
  Taskboard,
} from "@grassroots/onepager-ui-templates";

export function LandingPage() {
  return (
    <>
      <DashboardCard
        title="Operations"
        description="Single source of truth for app metrics."
        metric="97%"
      />
      <Taskboard
        title="Current Sprint"
        tasks={[
          { id: "1", label: "Create app", status: "done" },
          { id: "2", label: "Wire API", status: "doing" },
        ]}
      />
      <FlowPanel
        title="Pipeline"
        nodes={[
          { id: "ingest", label: "Ingest" },
          { id: "validate", label: "Validate" },
          { id: "ship", label: "Ship" },
        ]}
      />
      <SettingsPanel
        title="Environment"
        fields={[
          { id: "mode", label: "Mode", value: "local" },
          { id: "region", label: "Region", value: "us-central1" },
        ]}
      />
      <QuickActions
        actions={[
          { id: "a", label: "New Task", onClick: () => {} },
          { id: "b", label: "Open Logs", onClick: () => {} },
        ]}
      />
    </>
  );
}
```

## Scaffold Output

The scaffold generator creates page and route stubs in `ui_apps/<app_name>/` so each Django app starts with matching frontend screens.
