import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import React from "react";

import MetaUiSurface from "./MetaUiSurface";

describe("MetaUiSurface", () => {
  it("renders enterprise-only meta compartments and CRUD controls", () => {
    const markup = renderToStaticMarkup(<MetaUiSurface enterpriseAllowed={true} />);

    expect(markup).toContain("Meta Interface");
    expect(markup).toContain("Compartment 13");
    expect(markup).toContain("Philosophy");
    expect(markup).toContain("Law &amp; Governance: Insurance");
    expect(markup).toContain("Economics");
    expect(markup).toContain("Systemics");
    expect(markup).toContain("Create Meta Artifact");
    expect(markup).toContain("Enterprise access: enabled");
  });

  it("disables CRUD controls when enterprise access is not available", () => {
    const markup = renderToStaticMarkup(<MetaUiSurface enterpriseAllowed={false} />);

    expect(markup).toContain("Enterprise access: disabled");
    expect(markup).toContain("Create Meta Artifact");
  });
});