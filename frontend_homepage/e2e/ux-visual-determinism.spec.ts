import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

// Screenshot updates require explicit approval.
// Do not update snapshots during UX or logic changes unless intentional.

async function stubHomepageApi(page: Page) {
  await page.route("**/homepage/api/overview/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        welcome: "stub overview",
        flow: { status: "active", progress: 1, message: "stub" },
        tasks: [],
        settings: { notifications: true, dark_mode: false },
      }),
    });
  });

  await page.route("**/homepage/api/presentation-slides/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        count: 0,
        results: [],
      }),
    });
  });
}

test.describe("BaseTrue UX visual determinism", () => {
  test("Novice visual baseline surfaces", async ({ page }) => {
    await stubHomepageApi(page);
    await page.goto("/basetrue/public/bos/1/novice");

    await expect(page.getByRole("heading", { name: "Compartment Lens" })).toBeVisible();
    await expect(page.locator('.compartment-page[data-tier="novice"]')).toBeVisible();
    await expect(page.locator(".pipeline-navigation")).toBeVisible();

    await expect(await page.locator('.compartment-page[data-tier="novice"]').screenshot()).toMatchSnapshot(
      "novice-compartment-baseline.png",
    );
    await expect(await page.locator(".pipeline-navigation").screenshot()).toMatchSnapshot(
      "novice-pipeline-navigation-baseline.png",
    );

    // Novice drift guards: no studio or enterprise workspace surfaces.
    await expect(page.locator(".studio-workspace")).toHaveCount(0);
    await expect(page.locator(".enterprise-workspace")).toHaveCount(0);
    await expect(page.locator(".enterprise-zone-rail")).toHaveCount(0);
  });

  test("Intermediate visual baseline surfaces", async ({ page }) => {
    await stubHomepageApi(page);
    await page.goto("/basetrue/public/boe/3/intermediate");

    await expect(page.getByRole("heading", { name: "Compartment Lens" })).toBeVisible();
    await expect(page.locator('.compartment-page[data-tier="intermediate"]')).toBeVisible();
    await expect(page.locator(".pipeline-navigation")).toBeVisible();

    await expect(await page.locator('.compartment-page[data-tier="intermediate"]').screenshot()).toMatchSnapshot(
      "intermediate-compartment-baseline.png",
    );
    await expect(await page.locator(".pipeline-navigation").screenshot()).toMatchSnapshot(
      "intermediate-pipeline-navigation-baseline.png",
    );

    // Intermediate drift guards: no studio or enterprise workspace surfaces.
    await expect(page.locator(".studio-workspace")).toHaveCount(0);
    await expect(page.locator(".enterprise-workspace")).toHaveCount(0);
    await expect(page.locator(".enterprise-zone-rail")).toHaveCount(0);
  });

  test("Studio visual baseline surfaces", async ({ page }) => {
    await stubHomepageApi(page);
    await page.goto("/basetrue/studio");

    await expect(page.getByRole("heading", { name: "Studio Workspace" })).toBeVisible();
    await expect(page.locator(".studio-workspace")).toBeVisible();
    await expect(page.locator(".studio-summary-grid")).toBeVisible();

    await expect(await page.locator(".studio-workspace").screenshot()).toMatchSnapshot("studio-workstation-baseline.png");
    await expect(await page.locator(".studio-summary-grid").screenshot()).toMatchSnapshot("studio-overlays-baseline.png");
    await expect(await page.locator(".studio-owner-pill").screenshot()).toMatchSnapshot("studio-qc-qa-indicator-baseline.png");

    // Studio drift guards: enterprise tower surfaces must not appear.
    await expect(page.locator(".tower-floor-selector")).toHaveCount(0);
    await expect(page.locator(".enterprise-zone-rail")).toHaveCount(0);
    await expect(page.locator(".enterprise-chain-panel")).toHaveCount(0);
  });

  test("Enterprise visual baseline surfaces", async ({ page }) => {
    await stubHomepageApi(page);
    await page.goto("/basetrue/enterprise");

    await expect(page.getByRole("heading", { name: "Enterprise Tower Workspace" })).toBeVisible();
    await expect(page.locator(".enterprise-workspace")).toBeVisible();
    await expect(page.locator(".enterprise-zone-rail")).toBeVisible();
    await expect(page.locator(".enterprise-chain-panel")).toBeVisible();
    await expect(page.locator(".enterprise-floor-slice-grid")).toBeVisible();

    await expect(await page.locator(".enterprise-workspace").screenshot()).toMatchSnapshot("enterprise-tower-baseline.png");
    await expect(await page.locator(".enterprise-zone-rail").screenshot()).toMatchSnapshot("enterprise-zone-rail-baseline.png");
    await expect(await page.locator(".enterprise-chain-panel").screenshot()).toMatchSnapshot("enterprise-guided-chain-baseline.png");
    await expect(await page.locator(".enterprise-floor-slice-grid").screenshot()).toMatchSnapshot(
      "enterprise-floor-slice-baseline.png",
    );

    // Enterprise drift guards: studio workstation overlays must not appear.
    await expect(page.locator(".studio-workspace")).toHaveCount(0);
    await expect(page.getByText("Studio Idea Tags")).toHaveCount(0);
  });
});