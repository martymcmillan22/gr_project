import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import React from "react";

import PhasePanelScreen from "./PhasePanelScreen";

describe("PhasePanelScreen", () => {
  it("renders the dedicated route content for each phase panel", () => {
    const markup = renderToStaticMarkup(<PhasePanelScreen phase="project" />);

    expect(markup).toContain("ProjectPanel");
    expect(markup).toContain("Workflows");
    expect(markup).toContain("Timeline viewer");
  });

  it("renders richer governed module controls for the active phase", () => {
    const markup = renderToStaticMarkup(<PhasePanelScreen phase="idea" />);

    expect(markup).toContain("Add deliverable");
    expect(markup).toContain("Review module");
    expect(markup).toContain("Identity editor");
  });

  it("renders an acceptance summary for the active subsystem", () => {
    const markup = renderToStaticMarkup(<PhasePanelScreen phase="idea" />);

    expect(markup).toContain("Acceptance summary");
    expect(markup).toContain("Ready for review");
  });
});
