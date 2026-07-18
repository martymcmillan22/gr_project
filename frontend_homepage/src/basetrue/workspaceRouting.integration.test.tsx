import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import StudioWorkspace from "../../../basetrue/workspaces/StudioWorkspace";
import EnterpriseWorkspace from "../../../basetrue/workspaces/EnterpriseWorkspace";

describe("BaseTrue workspace runtime routing", () => {
  it("renders Studio with Studio-only governance and disabled governed actions", () => {
    const html = renderToStaticMarkup(<StudioWorkspace initialTier="studio" initialCompartmentIndex={5} />);

    expect(html).toContain("Governance profiles: weekly");
    expect(html).toContain("Temporal overlay owner: QC");
    expect(html).toContain("governed apply:disabled");
    expect(html).toContain("release workflows:disabled");
    expect(html).toContain("improve-all --apply (enterprise only)");
    expect(html).toContain("release --bump patch (enterprise only)");
    expect(html).toContain("release-notes (enterprise only)");
  });

  it("renders Enterprise with governed apply, tower routing, and maintenance chain", () => {
    const html = renderToStaticMarkup(<EnterpriseWorkspace accessTier="enterprise" profile="public" />);

    expect(html).toContain("Governance profiles: monthly, quarterly, annual");
    expect(html).toContain("governed apply:enabled");
    expect(html).toContain("release workflows:enabled");
    expect(html).toContain("Active zone: 1");
    expect(html).toContain("Garden maintenance route: manufacturing");
    expect(html).toContain("Guided chain: Monuments -&gt; Checkout -&gt; Surveys -&gt; Polls");
  });

  it("blocks non-enterprise access to Enterprise workspace", () => {
    const html = renderToStaticMarkup(
      <EnterpriseWorkspace accessTier={"studio" as unknown as "enterprise"} profile="public" />,
    );

    expect(html).toContain("Enterprise Workspace Access Required");
    expect(html).toContain("Only tier enterprise can access this workspace.");
  });
});
