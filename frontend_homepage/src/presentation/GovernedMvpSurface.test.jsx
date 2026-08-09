import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import React from "react";

import GovernedMvpSurface from "./GovernedMvpSurface";

describe("GovernedMvpSurface", () => {
  it("renders governed phases and contract values for the MVP UI scaffold", () => {
    const markup = renderToStaticMarkup(<GovernedMvpSurface />);

    expect(markup).toContain("Governed MVP UI Surfaces");
    expect(markup).toContain("IdeaPanel");
    expect(markup).toContain("SeedPanel");
    expect(markup).toContain("ProjectPanel");
    expect(markup).toContain("MvpPanel");
    expect(markup).toContain("StudioPanel");
    expect(markup).toContain("EnterprisePanel");
    expect(markup).toContain("4 subjects");
    expect(markup).toContain("256 sub-industries");
    expect(markup).toContain("Unified acceptance orchestration");
    expect(markup).toContain("Overall readiness");
  });
});
