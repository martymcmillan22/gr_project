import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { fileURLToPath } from "node:url";

import CompartmentPage from "../../../basetrue/components/CompartmentPage";
import StudioWorkspace from "../../../basetrue/workspaces/StudioWorkspace";
import EnterpriseWorkspace from "../../../basetrue/workspaces/EnterpriseWorkspace";

// CSS snapshot updates require explicit approval.
// Do not update snapshots during UX or logic changes unless intentional.

function extractSurfaceByClass(html: string, className: string): string {
  const classPattern = new RegExp(`class=["'][^"']*\\b${className}\\b[^"']*["']`);
  const classMatch = classPattern.exec(html);
  if (!classMatch || classMatch.index < 0) {
    throw new Error(`Surface with class '${className}' not found`);
  }

  const tagStart = html.lastIndexOf("<", classMatch.index);
  if (tagStart < 0) {
    throw new Error(`Unable to find tag start for class '${className}'`);
  }

  const openTagMatch = /^<([a-zA-Z0-9]+)([^>]*)>/.exec(html.slice(tagStart));
  if (!openTagMatch) {
    throw new Error(`Unable to parse opening tag for class '${className}'`);
  }

  const tagName = openTagMatch[1];
  const openTagLength = openTagMatch[0].length;
  let scanIndex = tagStart;
  let depth = 0;
  const tokenRegex = /<\/?([a-zA-Z0-9]+)(?:\s[^>]*)?>/g;

  while (true) {
    tokenRegex.lastIndex = scanIndex;
    const token = tokenRegex.exec(html);
    if (!token || token.index < 0) {
      break;
    }

    const raw = token[0];
    const tokenTagName = token[1];
    const isClosing = raw.startsWith("</");
    const isSelfClosing = raw.endsWith("/>");

    if (tokenTagName === tagName) {
      if (!isClosing) {
        depth += 1;
      }
      if (isClosing) {
        depth -= 1;
        if (depth === 0) {
          return html.slice(tagStart, tokenRegex.lastIndex);
        }
      }
      if (isSelfClosing) {
        depth -= 1;
      }
    }

    scanIndex = tokenRegex.lastIndex;
  }

  return html.slice(tagStart, tagStart + openTagLength);
}

function normalizeStructure(html: string): string {
  const tokens: string[] = [];
  const tagRegex = /<\/?([a-zA-Z0-9]+)([^>]*)>/g;
  let depth = 0;

  while (true) {
    const match = tagRegex.exec(html);
    if (!match) {
      break;
    }

    const raw = match[0];
    const tagName = match[1].toLowerCase();
    const attrBlob = match[2] || "";
    const isClosing = raw.startsWith("</");
    const isSelfClosing = raw.endsWith("/>");

    if (isClosing) {
      depth = Math.max(0, depth - 1);
      tokens.push(`${"  ".repeat(depth)}</${tagName}>`);
      continue;
    }

    const classAttr = /\sclass="([^"]+)"/.exec(attrBlob)?.[1] || "";
    const idAttr = /\sid="([^"]+)"/.exec(attrBlob)?.[1] || "";
    const ariaAttr = /\saria-label="([^"]+)"/.exec(attrBlob)?.[1] || "";
    const dataTierAttr = /\sdata-tier="([^"]+)"/.exec(attrBlob)?.[1] || "";
    const classValue = classAttr
      .split(/\s+/)
      .filter(Boolean)
      .join(" ");

    const attrParts = [
      classValue ? `class=\"${classValue}\"` : "",
      idAttr ? `id=\"${idAttr}\"` : "",
      ariaAttr ? `aria-label=\"${ariaAttr}\"` : "",
      dataTierAttr ? `data-tier=\"${dataTierAttr}\"` : "",
    ].filter(Boolean);

    tokens.push(`${"  ".repeat(depth)}<${tagName}${attrParts.length ? ` ${attrParts.join(" ")}` : ""}>`);

    if (!isSelfClosing) {
      depth += 1;
    }
  }

  return tokens.join("\n");
}

function snapshotPath(fileName: string): string {
  return fileURLToPath(new URL(`../../tests/css-snapshots/${fileName}`, import.meta.url));
}

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

  it("locks deterministic CSS selector surfaces for Studio and Enterprise", () => {
    const studioHtml = renderToStaticMarkup(<StudioWorkspace initialTier="studio" initialCompartmentIndex={5} />);
    const enterpriseHtml = renderToStaticMarkup(<EnterpriseWorkspace accessTier="enterprise" profile="public" />);

    expect(studioHtml).toContain('class="studio-workspace"');
    expect(studioHtml).toContain('class="studio-summary-grid"');
    expect(studioHtml).toContain('class="studio-stage-rail"');

    expect(enterpriseHtml).toContain('class="enterprise-workspace"');
    expect(enterpriseHtml).toContain('class="enterprise-zone-rail"');
    expect(enterpriseHtml).toContain('class="enterprise-chain-panel"');
    expect(enterpriseHtml).toContain('class="enterprise-floor-slice-grid"');
    expect(enterpriseHtml).toContain('class="tower-floor-selector"');
  });

  it("enforces tier-specific CSS drift guards", () => {
    const studioHtml = renderToStaticMarkup(<StudioWorkspace initialTier="studio" initialCompartmentIndex={5} />);
    const enterpriseHtml = renderToStaticMarkup(<EnterpriseWorkspace accessTier="enterprise" profile="public" />);

    expect(studioHtml).not.toContain("enterprise-zone-rail");
    expect(studioHtml).not.toContain("enterprise-chain-panel");
    expect(studioHtml).not.toContain("tower-floor-selector");

    expect(enterpriseHtml).not.toContain("studio-workspace");
    expect(enterpriseHtml).not.toContain("studio-summary-grid");
    expect(enterpriseHtml).not.toContain("studio-stage-rail");
  });

  it("matches Studio CSS structure snapshot baseline", async () => {
    const studioHtml = renderToStaticMarkup(<StudioWorkspace initialTier="studio" initialCompartmentIndex={5} />);
    const studioSurface = extractSurfaceByClass(studioHtml, "studio-workspace");

    await expect(normalizeStructure(studioSurface)).toMatchFileSnapshot(snapshotPath("studio-css-baseline.snap"));
  });

  it("matches Enterprise CSS structure snapshot baseline", async () => {
    const enterpriseHtml = renderToStaticMarkup(<EnterpriseWorkspace accessTier="enterprise" profile="public" />);
    const enterpriseSurface = extractSurfaceByClass(enterpriseHtml, "enterprise-workspace");

    await expect(normalizeStructure(enterpriseSurface)).toMatchFileSnapshot(snapshotPath("enterprise-css-baseline.snap"));
  });

  it("matches zone rail CSS structure snapshot baseline", async () => {
    const enterpriseHtml = renderToStaticMarkup(<EnterpriseWorkspace accessTier="enterprise" profile="public" />);
    const zoneSurface = extractSurfaceByClass(enterpriseHtml, "enterprise-zone-rail");

    await expect(normalizeStructure(zoneSurface)).toMatchFileSnapshot(snapshotPath("zone-rail-css-baseline.snap"));
  });

  it("matches guided chain CSS structure snapshot baseline", async () => {
    const enterpriseHtml = renderToStaticMarkup(<EnterpriseWorkspace accessTier="enterprise" profile="public" />);
    const chainSurface = extractSurfaceByClass(enterpriseHtml, "enterprise-chain-panel");

    await expect(normalizeStructure(chainSurface)).toMatchFileSnapshot(snapshotPath("guided-chain-css-baseline.snap"));
  });

  it("matches floor slice CSS structure snapshot baseline", async () => {
    const enterpriseHtml = renderToStaticMarkup(<EnterpriseWorkspace accessTier="enterprise" profile="public" />);
    const floorSliceSurface = extractSurfaceByClass(enterpriseHtml, "enterprise-floor-slice-grid");

    await expect(normalizeStructure(floorSliceSurface)).toMatchFileSnapshot(snapshotPath("floor-slice-css-baseline.snap"));
  });

  it("locks deterministic CSS selectors for Novice and Intermediate compartment routes", () => {
    const noviceHtml = renderToStaticMarkup(
      <CompartmentPage profile="public" name="BOS" index={1} tier="novice" />,
    );
    const intermediateHtml = renderToStaticMarkup(
      <CompartmentPage profile="public" name="BOE" index={3} tier="intermediate" />,
    );

    expect(noviceHtml).toContain('class="compartment-page"');
    expect(noviceHtml).toContain('data-tier="novice"');
    expect(noviceHtml).toContain('class="pipeline-navigation"');

    expect(intermediateHtml).toContain('class="compartment-page"');
    expect(intermediateHtml).toContain('data-tier="intermediate"');
    expect(intermediateHtml).toContain('class="pipeline-navigation"');

    expect(noviceHtml).not.toContain("studio-workspace");
    expect(noviceHtml).not.toContain("enterprise-workspace");
    expect(intermediateHtml).not.toContain("studio-workspace");
    expect(intermediateHtml).not.toContain("enterprise-workspace");
  });

  it("matches Novice CSS structure snapshot baseline", async () => {
    const noviceHtml = renderToStaticMarkup(
      <CompartmentPage profile="public" name="BOS" index={1} tier="novice" />,
    );
    const noviceSurface = extractSurfaceByClass(noviceHtml, "compartment-page");

    await expect(normalizeStructure(noviceSurface)).toMatchFileSnapshot(snapshotPath("novice-css-baseline.snap"));
  });

  it("matches Intermediate CSS structure snapshot baseline", async () => {
    const intermediateHtml = renderToStaticMarkup(
      <CompartmentPage profile="public" name="BOE" index={3} tier="intermediate" />,
    );
    const intermediateSurface = extractSurfaceByClass(intermediateHtml, "compartment-page");

    await expect(normalizeStructure(intermediateSurface)).toMatchFileSnapshot(
      snapshotPath("intermediate-css-baseline.snap"),
    );
  });

  it("matches Novice pipeline navigation CSS structure snapshot baseline", async () => {
    const noviceHtml = renderToStaticMarkup(
      <CompartmentPage profile="public" name="BOS" index={1} tier="novice" />,
    );
    const novicePipelineSurface = extractSurfaceByClass(noviceHtml, "pipeline-navigation");

    await expect(normalizeStructure(novicePipelineSurface)).toMatchFileSnapshot(
      snapshotPath("novice-pipeline-navigation-css-baseline.snap"),
    );
  });

  it("matches Intermediate pipeline navigation CSS structure snapshot baseline", async () => {
    const intermediateHtml = renderToStaticMarkup(
      <CompartmentPage profile="public" name="BOE" index={3} tier="intermediate" />,
    );
    const intermediatePipelineSurface = extractSurfaceByClass(intermediateHtml, "pipeline-navigation");

    await expect(normalizeStructure(intermediatePipelineSurface)).toMatchFileSnapshot(
      snapshotPath("intermediate-pipeline-navigation-css-baseline.snap"),
    );
  });
});
