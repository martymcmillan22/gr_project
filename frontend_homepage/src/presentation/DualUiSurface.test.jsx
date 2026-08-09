import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import React from "react";

import HumanUiSurface from "./HumanUiSurface";
import AgentUiSurface from "./AgentUiSurface";

describe("Dual UI surfaces", () => {
  it("renders a human-first guided experience", () => {
    const markup = renderToStaticMarkup(<HumanUiSurface />);

    expect(markup).toContain("Human experience");
    expect(markup).toContain("Guided path");
  });

  it("renders an agent-focused orchestrated experience", () => {
    const markup = renderToStaticMarkup(<AgentUiSurface />);

    expect(markup).toContain("Agent operations");
    expect(markup).toContain("Acceptance orchestration");
  });
});
