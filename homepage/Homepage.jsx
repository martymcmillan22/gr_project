import { useCallback, useEffect, useState } from "react";

import Taskboard from "../templates/ui/Taskboard";
import FlowPanel from "../templates/ui/FlowPanel";
import SettingsPanel from "../templates/ui/SettingsPanel";
import QuickActions from "../templates/ui/QuickActions";
import DashboardCard from "../templates/ui/DashboardCard";

import "./homepage.css";
import { createHomepageAction, getHomepageOverview, updateHomepagePreferences } from "./homepage_api";

export default function Homepage() {
  const [data, setData] = useState({
    welcome: "Your daily overview",
    quick_actions: [],
    flow: null,
    tasks: [],
    settings: { notifications: true, dark_mode: false },
  });

  useEffect(() => {
    let cancelled = false;
    getHomepageOverview()
      .then((payload) => {
        if (!cancelled && payload) {
          setData((current) => ({ ...current, ...payload }));
        }
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, []);

  const handleSettingChange = useCallback((key, value) => {
    setData((current) => {
      const next = {
        ...current,
        settings: {
          ...(current.settings || {}),
          [key]: value,
        },
      };
      updateHomepagePreferences(next.settings).catch(() => {});
      return next;
    });
  }, []);

  const actions = [
    { id: 1, label: "Start Flow", onClick: () => createHomepageAction("Start Flow") },
    { id: 2, label: "Open Taskboard", onClick: () => createHomepageAction("Open Taskboard") },
  ];

  return (
    <main className="homepage">
      <DashboardCard title="Welcome" value={data.welcome || "Your daily overview"} />

      <QuickActions actions={actions} />

      <FlowPanel flow={data.flow || { status: "active", progress: 42, message: "In progress" }} />

      <Taskboard
        tasks={
          data.tasks.length
            ? data.tasks.map((task) => ({
                id: task.id,
                title: task.title,
                description: task.description,
              }))
            : [
                { id: 1, title: "Review Notes", description: "Check today's flow" },
                { id: 2, title: "Update Settings", description: "Adjust preferences" },
              ]
        }
      />

      <SettingsPanel
        settings={data.settings || { notifications: true, dark_mode: false }}
        onChange={handleSettingChange}
      />
    </main>
  );
}
