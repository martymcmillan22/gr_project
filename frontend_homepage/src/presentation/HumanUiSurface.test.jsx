import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import React from "react";

import HumanUiSurface from "./HumanUiSurface";

describe("HumanUiSurface", () => {
  it("renders the human design principles and office model on the human route", () => {
    const markup = renderToStaticMarkup(<HumanUiSurface />);

    expect(markup).toContain("Human-first governed UI");
    expect(markup).toContain("Start with creative freedom");
    expect(markup).toContain("Use Veil as progressive disclosure");
    expect(markup).toContain("Twist, Museum, Garden, and Meta");
    expect(markup).toContain("Idea");
    expect(markup).toContain("Enterprise");
  });
});