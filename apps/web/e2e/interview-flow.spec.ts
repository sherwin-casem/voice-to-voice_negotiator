import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const API_URL =
  process.env.E2E_API_URL ??
  process.env.API_PROXY_TARGET ??
  "http://127.0.0.1:8000";

async function apiIsReady(request: APIRequestContext): Promise<boolean> {
  try {
    const response = await request.get(`${API_URL}/api/v1/health/live`, { timeout: 3_000 });
    return response.ok();
  } catch {
    return false;
  }
}

async function registerAccount(page: Page, email: string, password: string) {
  await page.goto("/register");
  await expect(page.getByRole("heading", { name: /create your account/i })).toBeVisible();
  await expect(page.locator("#email")).toBeVisible({ timeout: 20_000 });
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.locator("#confirmPassword").fill(password);
  await page.getByRole("button", { name: /create account/i }).click();
}

test.describe("register → interview → results", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await apiIsReady(request)), "API is not running; start apps/api first");
  });

  test("register, create interview, and open results preview", async ({ page }) => {
    test.setTimeout(90_000);

    const email = `e2e-${Date.now()}@example.com`;
    const password = "password123";

    await registerAccount(page, email, password);
    await page.waitForURL(/\/interviews\/new/, { timeout: 20_000 });
    await expect(page.getByRole("heading", { name: /create interview/i })).toBeVisible();

    await page.locator("#title").fill(`E2E interview ${Date.now()}`);
    await page.getByRole("button", { name: /continue to setup/i }).click();
    await page.waitForURL(/\/interviews\/[^/]+\/setup/, { timeout: 20_000 });

    // Full live voice needs mic + WS; close the product loop via authenticated preview results.
    await page.goto("/interviews/preview-1/results?preview=1");
    await expect(page.getByRole("heading", { name: /interview results/i })).toBeVisible({
      timeout: 20_000,
    });
  });
});

test("marketing surfaces render without auth", async ({ page }) => {
  await page.goto("/features");
  await expect(page.getByRole("heading").first()).toBeVisible({ timeout: 15_000 });
  await page.goto("/pricing");
  await expect(page.getByRole("heading").first()).toBeVisible({ timeout: 15_000 });
});
