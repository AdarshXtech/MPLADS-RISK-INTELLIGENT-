import { expect, test } from "@playwright/test";

test("Data Quality navigation opens the dedicated page", async ({ page }) => {
  await page.goto("/data-quality");
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel("Username").fill(process.env.MPLADS_E2E_USERNAME!);
  await page.getByLabel("Password").fill(process.env.MPLADS_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.getByRole("link", { name: "Data Quality", exact: true }).click();

  await expect(page).toHaveURL(/\/data-quality$/);
  await expect(page.getByRole("heading", { name: "Data Quality", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Data Quality", exact: true })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("heading", { name: "Ingested source reports", exact: true })).toBeVisible();
});
