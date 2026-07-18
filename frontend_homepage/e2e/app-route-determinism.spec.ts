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
  test("Assert_Studio_Route_E2E", async ({ page }) => {
    await stubHomepageApi(page);
    await page.goto("/basetrue/studio");

    await expect(page.getByRole("heading", { name: "Studio Workspace" })).toBeVisible();
    await expect(page.getByText("Governed apply mode and release workflows are disabled on Studio route.")).toBeVisible();
    await expect(page.getByText("governed apply:disabled")).toBeVisible();
    await expect(page.getByText("release workflows:disabled")).toBeVisible();

    // Studio route must not render enterprise-only tower badges or enterprise workspace header.
    await expect(page.getByText("Tower Control Room")).toHaveCount(0);
    await expect(page.getByText("tower height", { exact: false })).toHaveCount(0);

    // Studio overlays should be present in Studio route.
    await expect(page.getByText("Studio Idea Tags")).toBeVisible();
    await expect(page.getByText("Studio Seed Tags")).toBeVisible();
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

    // Enterprise route must not render Studio-only overlays.
    await expect(page.getByText("Studio Idea Tags")).toHaveCount(0);
    await expect(page.getByText("Studio Seed Tags")).toHaveCount(0);
  });

  test("Assert_Tier_Profile_Mismatch_E2E", async ({ page }) => {
    await stubHomepageApi(page);
    const pageError = page.waitForEvent("pageerror");
    await page.goto("/basetrue/studio?tier=enterprise");
    const error = await pageError;

    expect(error.message).toContain("Tier/profile mismatch: Studio route cannot request enterprise tier");
  });
});
