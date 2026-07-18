import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import StudioWorkspace from "../../../basetrue/workspaces/StudioWorkspace";
import EnterpriseWorkspace from "../../../basetrue/workspaces/EnterpriseWorkspace";

describe("BaseTrue workspace runtime routing", () => {
  it("renders Studio with Studio-only governance and disabled governed actions", () => {
    const html = renderToStaticMarkup(<StudioWorkspace initialTier="studio" initialCompartmentIndex={5} />);

    expect(html).toContain('class="studio-workspace"');
    expect(html).toContain('class="studio-stage-rail"');
    expect(html).toContain("Linear flow: Idea -&gt; Seed -&gt; Project -&gt; Work");
    expect(html).toContain("Compartment group drives QC/QA overlay ownership.");
    expect(html).toContain("Governance profiles: weekly");
    expect(html).toContain("Temporal overlay owner: QC");
    expect(html).toContain("governed apply:disabled");
    expect(html).toContain("release workflows:disabled");
    expect(html).toContain("weekly:allowed");
    expect(html).toContain("improve-all --apply (enterprise only)");
    expect(html).toContain("release --bump patch (enterprise only)");
    expect(html).toContain("release-notes (enterprise only)");

    expect(html).not.toContain("Tower Control Room");
    expect(html).not.toContain("enterprise-zone-rail");
    expect(html).not.toContain("Monuments -&gt; Checkout -&gt; Surveys -&gt; Polls");
    expect(html).not.toContain("class=\"tower-floor-selector\"");
    expect(html).not.toContain("governed apply:enabled");
    expect(html).not.toContain("release workflows:enabled");
  });

  it("renders Enterprise with governed apply, tower routing, and maintenance chain", () => {
    const html = renderToStaticMarkup(<EnterpriseWorkspace accessTier="enterprise" profile="public" />);

    expect(html).toContain('class="enterprise-workspace"');
    expect(html).toContain('class="enterprise-summary-grid"');
    expect(html).toContain('class="enterprise-zone-rail"');
    expect(html).toContain('class="enterprise-chain-panel"');
    expect(html).toContain('class="enterprise-tower-layout"');
    expect(html).toContain('class="enterprise-floor-slice-grid"');
    expect(html).toContain('class="tower-floor-selector"');
    expect(html).toContain('class="enterprise-floor-button is-active"');
    expect(html).toContain("Governance profiles: monthly, quarterly, annual");
    expect(html).toContain("monthly:allowed");
    expect(html).toContain("quarterly:allowed");
    expect(html).toContain("annual:allowed");
    expect(html).toContain("governed apply:enabled");
    expect(html).toContain("release workflows:enabled");
    expect(html).toContain("Active zone: 1");
    expect(html).toContain("Zone 1 · Floors 1-4");
    expect(html).toContain("Floor 1");
    expect(html).toContain("#01");
    expect(html).toContain("Garden maintenance route: manufacturing");
    expect(html).toContain("Guided chain: Monuments -&gt; Checkout -&gt; Surveys -&gt; Polls");
    expect(html).toContain("Monuments -&gt; Checkout -&gt; Surveys -&gt; Polls");
    expect(html).toContain("Prepare monument-safe artifacts before transactional handoff.");

    expect(html).not.toContain("Studio Idea Tags");
    expect(html).not.toContain("Studio Seed Tags");
    expect(html).not.toContain("improve-all --apply (enterprise only)");
    expect(html).not.toContain("release workflows:disabled");
  });

  it("blocks non-enterprise access to Enterprise workspace", () => {
    const html = renderToStaticMarkup(
      <EnterpriseWorkspace accessTier={"studio" as unknown as "enterprise"} profile="public" />,
    );

    expect(html).toContain("Enterprise Workspace Access Required");
    expect(html).toContain("Only tier enterprise can access this workspace.");
  });
});
