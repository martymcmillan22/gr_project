import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

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

test.describe("BaseTrue app route determinism", () => {
  test("Assert_Novice_Route_E2E", async ({ page }) => {
    await stubHomepageApi(page);
    await page.goto("/basetrue/public/bos/1/novice");

    await expect(page.getByRole("heading", { name: "Compartment Lens" })).toBeVisible();
    await expect(page.locator(".compartment-page")).toBeVisible();
    await expect(page.locator('.compartment-page[data-tier="novice"]')).toBeVisible();
    await expect(page.getByText("RR pipeline: disabled", { exact: false })).toBeVisible();
    await expect(page.getByText("QPU: disabled", { exact: false })).toBeVisible();
    await expect(page.getByText("Tower: disabled", { exact: false })).toBeVisible();

    const noviceModeButtons = page.locator('.pipeline-navigation [role="group"][aria-label="Compartment mode"] button');
    await expect(noviceModeButtons).toHaveCount(2);
    await expect(noviceModeButtons.nth(0)).toHaveAttribute("aria-pressed", "true");
    await expect(noviceModeButtons.nth(0)).toBeDisabled();
    await expect(noviceModeButtons.nth(1)).toHaveAttribute("aria-pressed", "false");
    await expect(noviceModeButtons.nth(1)).toBeEnabled();

    // Novice route must not overlap with studio or enterprise workspace surfaces.
    await expect(page.locator(".studio-workspace")).toHaveCount(0);
    await expect(page.locator(".enterprise-workspace")).toHaveCount(0);
    await expect(page.locator(".enterprise-zone-rail")).toHaveCount(0);
    await expect(page.locator(".tower-floor-selector")).toHaveCount(0);
  });

  test("Assert_Intermediate_Route_E2E", async ({ page }) => {
    await stubHomepageApi(page);
    await page.goto("/basetrue/public/boe/3/intermediate");

    await expect(page.getByRole("heading", { name: "Compartment Lens" })).toBeVisible();
    await expect(page.locator(".compartment-page")).toBeVisible();
    await expect(page.locator('.compartment-page[data-tier="intermediate"]')).toBeVisible();
    await expect(page.getByText("RR pipeline: disabled", { exact: false })).toBeVisible();
    await expect(page.getByText("QPU: disabled", { exact: false })).toBeVisible();
    await expect(page.getByText("Tower: disabled", { exact: false })).toBeVisible();

    const intermediateModeButtons = page.locator('.pipeline-navigation [role="group"][aria-label="Compartment mode"] button');
    await expect(intermediateModeButtons).toHaveCount(2);
    await expect(intermediateModeButtons.nth(0)).toHaveAttribute("aria-pressed", "true");
    await expect(intermediateModeButtons.nth(0)).toBeDisabled();
    await expect(intermediateModeButtons.nth(1)).toHaveAttribute("aria-pressed", "false");
    await expect(intermediateModeButtons.nth(1)).toBeEnabled();

    // Intermediate route must not overlap with studio or enterprise workspace surfaces.
    await expect(page.locator(".studio-workspace")).toHaveCount(0);
    await expect(page.locator(".enterprise-workspace")).toHaveCount(0);
    await expect(page.locator(".enterprise-zone-rail")).toHaveCount(0);
    await expect(page.locator(".tower-floor-selector")).toHaveCount(0);
  });

  test("Assert_Studio_Route_E2E", async ({ page }) => {
    await stubHomepageApi(page);
    await page.goto("/basetrue/studio");

    await expect(page.getByRole("heading", { name: "Studio Workspace" })).toBeVisible();
    await expect(page.getByText("Governed apply mode and release workflows are disabled on Studio route.")).toBeVisible();
    await expect(page.getByText("governed apply:disabled")).toBeVisible();
    await expect(page.getByText("release workflows:disabled")).toBeVisible();
    await expect(page.getByText("weekly:allowed")).toBeVisible();
    await expect(page.getByText("Temporal overlay owner: QC")).toBeVisible();

    // Studio route must not render enterprise-only tower badges or enterprise workspace header.
    await expect(page.getByText("Tower Control Room")).toHaveCount(0);
    await expect(page.getByText("tower height", { exact: false })).toHaveCount(0);
    await expect(page.locator(".enterprise-zone-rail")).toHaveCount(0);
    await expect(page.locator(".tower-floor-selector")).toHaveCount(0);
    await expect(page.getByText("Monuments -> Checkout -> Surveys -> Polls", { exact: false })).toHaveCount(0);

    // Studio overlays should be present in Studio route.
    await expect(page.getByText("Studio Idea Tags")).toBeVisible();
    await expect(page.getByText("Studio Seed Tags")).toBeVisible();

    const studioDisabledCommands = page.locator(".studio-command-row .studio-disabled-command");
    await expect(studioDisabledCommands).toHaveCount(3);
    await expect(studioDisabledCommands.nth(0)).toBeDisabled();
    await expect(studioDisabledCommands.nth(1)).toBeDisabled();
    await expect(studioDisabledCommands.nth(2)).toBeDisabled();
  });

  test("Assert_Enterprise_Route_E2E and Assert_Governed_Apply_E2E", async ({ page }) => {
    await stubHomepageApi(page);
    await page.goto("/basetrue/enterprise");

    await expect(page.getByRole("heading", { name: "Enterprise Tower Workspace" })).toBeVisible();
    await expect(page.getByText("Tower Control Room")).toBeVisible();
    await expect(page.getByText("governed apply:enabled")).toBeVisible();
    await expect(page.getByText("release workflows:enabled")).toBeVisible();
    await expect(page.getByRole("button", { name: "improve-all --apply" })).toBeVisible();
    await expect(page.getByRole("button", { name: "release --bump patch" })).toBeVisible();
    await expect(page.getByRole("button", { name: "improve-all --apply" })).toBeEnabled();
    await expect(page.getByRole("button", { name: "release --bump patch" })).toBeEnabled();
    await expect(page.getByText("monthly:allowed")).toBeVisible();
    await expect(page.getByText("quarterly:allowed")).toBeVisible();
    await expect(page.getByText("annual:allowed")).toBeVisible();
    await expect(page.locator(".enterprise-zone-rail")).toBeVisible();
    await expect(page.getByText("Zone 1 · Floors 1-4")).toBeVisible();
    await expect(page.locator(".enterprise-chain-panel")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Monuments -> Checkout -> Surveys -> Polls" })).toBeVisible();
    await expect(page.locator(".tower-floor-selector .enterprise-floor-button").first()).toBeVisible();
    await expect(page.locator(".enterprise-floor-slice-grid")).toBeVisible();

    const selectedFloorButton = page.locator('.tower-floor-selector .enterprise-floor-button[aria-pressed="true"]');
    await expect(selectedFloorButton).toHaveCount(1);
    const secondFloorButton = page.locator(".tower-floor-selector .enterprise-floor-button").nth(1);
    await secondFloorButton.click();
    await expect(secondFloorButton).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator('.tower-floor-selector .enterprise-floor-button[aria-pressed="true"]')).toHaveCount(1);

    // Enterprise route must not render Studio-only overlays.
    await expect(page.getByText("Studio Idea Tags")).toHaveCount(0);
    await expect(page.getByText("Studio Seed Tags")).toHaveCount(0);
    await expect(page.getByText("improve-all --apply (enterprise only)")).toHaveCount(0);
  });

  test("Assert_Tier_Profile_Mismatch_E2E", async ({ page }) => {
    await stubHomepageApi(page);
    const pageError = page.waitForEvent("pageerror");
    await page.goto("/basetrue/studio?tier=enterprise");
    const error = await pageError;

    expect(error.message).toContain("Tier/profile mismatch: Studio route cannot request enterprise tier");
  });
});
