import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

const canUseGovernedApplyModeMock = vi.hoisted(() => vi.fn(() => true));

vi.mock("../../../basetrue/logic/pipelineLogic", () => ({
  canUseGovernedApplyMode: canUseGovernedApplyModeMock,
}));

vi.mock("../../../basetrue/workspaces/StudioWorkspace", () => ({
  default: () => <div>STUDIO_WORKSPACE_STUB studio-overlay-badge</div>,
}));

vi.mock("../../../basetrue/workspaces/EnterpriseWorkspace", () => ({
  default: () => <div>ENTERPRISE_WORKSPACE_STUB tower-height-badge</div>,
}));

vi.mock("./api/homepageApi", () => ({
  applyPresetToSlide: vi.fn(),
  comparePresetBundle: vi.fn(),
  deletePresetBundle: vi.fn(),
  fetchPresetBundleHistory: vi.fn(),
  fetchPresetBundleShares: vi.fn(),
  fetchPresetBundleTags: vi.fn(),
  fetchPresetBundles: vi.fn(),
  fetchSemanticPresets: vi.fn(),
  fetchOverview: vi.fn(),
  fetchPresentationSlides: vi.fn(),
  fetchResolvedSlide: vi.fn(),
  generateSlideBundle: vi.fn(),
  postAction: vi.fn(),
  rollbackPresetBundle: vi.fn(),
  savePresetBundleShare: vi.fn(),
  savePresetBundleTag: vi.fn(),
  savePresetBundle: vi.fn(),
  savePreferences: vi.fn(),
}));

vi.mock("./presentation/QpcBlueprint", () => ({ default: () => <div /> }));
vi.mock("./presentation/RoutingLayoutPreview", () => ({ default: () => <div /> }));
vi.mock("./presentation/SquareRootTimelineGrid", () => ({ default: () => <div /> }));
vi.mock("./presentation/StoryHierarchyExplorer", () => ({ default: () => <div /> }));
vi.mock("./presentation/SemanticOperationsPanel", () => ({ default: () => <div /> }));
vi.mock("./presentation/BaseTrueWheelDemo", () => ({ default: () => <div /> }));
vi.mock("./ui/DashboardCard", () => ({ default: () => <div /> }));
vi.mock("./ui/FlowPanel", () => ({ default: () => <div /> }));
vi.mock("./ui/QuickActions", () => ({ default: () => <div /> }));
vi.mock("./ui/SettingsPanel", () => ({ default: () => <div /> }));
vi.mock("./ui/Taskboard", () => ({ default: () => <div /> }));
vi.mock("../../../ui/diagnostics/TemplateGroupInspectorPanel", () => ({
  TemplateGroupInspectorPanel: () => <div />,
}));
vi.mock("../../../basetrue/components/CompartmentPage", () => ({
  default: (props: { tier?: string }) => <div>COMPARTMENT_PAGE_STUB tier:{props?.tier || "unknown"}</div>,
}));

import App from "../App";

function setRoute(pathname: string, search = "") {
  Object.defineProperty(globalThis, "window", {
    value: {
      location: { pathname, search },
    },
    configurable: true,
    writable: true,
  });
}

afterEach(() => {
  canUseGovernedApplyModeMock.mockReset();
  canUseGovernedApplyModeMock.mockReturnValue(true);
});

describe("App route-level determinism", () => {
  it("loads Studio route with Studio workspace only", () => {
    setRoute("/basetrue/studio");

    const html = renderToStaticMarkup(<App />);

    expect(html).toContain("Studio Workspace");
    expect(html).toContain("STUDIO_WORKSPACE_STUB");
    expect(html).not.toContain("ENTERPRISE_WORKSPACE_STUB");
  });

  it("loads Enterprise route with Enterprise workspace only", () => {
    setRoute("/basetrue/enterprise");

    const html = renderToStaticMarkup(<App />);

    expect(html).toContain("Enterprise Tower Workspace");
    expect(html).toContain("ENTERPRISE_WORKSPACE_STUB");
    expect(html).not.toContain("STUDIO_WORKSPACE_STUB");
  });

  it("blocks governed apply messaging on Studio route", () => {
    setRoute("/basetrue/studio");

    const html = renderToStaticMarkup(<App />);

    expect(html).toContain("Governed apply mode and release workflows are disabled on Studio route.");
    expect(html).not.toContain("tower-height-badge");
  });

  it("requires governed apply capability for Enterprise route", () => {
    setRoute("/basetrue/enterprise");
    canUseGovernedApplyModeMock.mockReturnValue(false);

    const html = renderToStaticMarkup(<App />);

    expect(html).toContain("Enterprise route is disabled because governed apply mode is not available.");
    expect(html).not.toContain("ENTERPRISE_WORKSPACE_STUB");
  });

  it("keeps Studio overlays off Enterprise route", () => {
    setRoute("/basetrue/enterprise");

    const html = renderToStaticMarkup(<App />);

    expect(html).not.toContain("studio-overlay-badge");
  });

  it("throws on Studio tier/profile mismatch via query", () => {
    setRoute("/basetrue/studio", "?tier=enterprise");

    expect(() => renderToStaticMarkup(<App />)).toThrow(
      /Tier\/profile mismatch: Studio route cannot request enterprise tier/,
    );
  });

  it("loads Novice compartment route with compartment lens only", () => {
    setRoute("/basetrue/public/bos/1/novice");

    const html = renderToStaticMarkup(<App />);

    expect(html).toContain("Compartment Lens");
    expect(html).toContain("COMPARTMENT_PAGE_STUB tier:novice");
    expect(html).not.toContain("STUDIO_WORKSPACE_STUB");
    expect(html).not.toContain("ENTERPRISE_WORKSPACE_STUB");
  });

  it("loads Intermediate compartment route with compartment lens only", () => {
    setRoute("/basetrue/public/boe/3/intermediate");

    const html = renderToStaticMarkup(<App />);

    expect(html).toContain("Compartment Lens");
    expect(html).toContain("COMPARTMENT_PAGE_STUB tier:intermediate");
    expect(html).not.toContain("STUDIO_WORKSPACE_STUB");
    expect(html).not.toContain("ENTERPRISE_WORKSPACE_STUB");
  });
});
