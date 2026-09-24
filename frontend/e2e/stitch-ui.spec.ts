import { expect, test } from "@playwright/test";
import { resolve } from "node:path";

test("password visibility is keyboard accessible and preserves the entered password", async ({ page }) => {
  await page.goto("/login");
  const password = page.getByLabel("Password", { exact: true });
  await password.fill("synthetic-visibility-check");
  await expect(password).toHaveAttribute("type", "password");
  await password.focus();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Show password" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(password).toHaveAttribute("type", "text");
  await expect(password).toHaveValue("synthetic-visibility-check");
  await page.getByRole("button", { name: "Hide password" }).click();
  await expect(password).toHaveAttribute("type", "password");
  await expect(password).toHaveValue("synthetic-visibility-check");
  await expect(page).toHaveURL(/\/login$/);
});

test("review workspace reflows and prevents repeated saves while a review is pending", async ({ page }, info) => {
  const headers = { "X-MPLADS-Review-Key": process.env.MPLADS_E2E_API_KEY! };
  const reset = () => page.request.post("http://127.0.0.1:8012/__scenario", { headers, data: { reset: true } });
  await reset();
  try {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/login");
    await page.getByLabel("Username").fill(process.env.MPLADS_E2E_USERNAME!);
    await page.getByLabel("Password", { exact: true }).fill(process.env.MPLADS_E2E_PASSWORD!);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await page.getByRole("link", { name: "Review evidence" }).filter({ visible: true }).first().click();
    const evidence = page.locator(".case-evidence");
    const review = page.getByRole("complementary", { name: "Reviewer decision and history" });
    const evidenceBox = await evidence.boundingBox();
    const reviewBox = await review.boundingBox();
    expect(evidenceBox).not.toBeNull();
    expect(reviewBox).not.toBeNull();
    expect(reviewBox!.x).toBeGreaterThanOrEqual(evidenceBox!.x + evidenceBox!.width);
    await expect(page.getByRole("definition").filter({ hasText: /^312.4 m$/ })).toHaveCount(2);
    await page.screenshot({ path: resolve("../output/stitch-ui", info.project.name, "evidence-desktop.png"), fullPage: true, style: 'body::before { content: "SYNTHETIC TEST DATA / UI VERIFICATION"; display: block; background: #0b132b; color: white; padding: 5px; text-align: center; font: 10px Arial; }' });
    await page.setViewportSize({ width: 390, height: 844 });
    const mobileEvidence = await evidence.boundingBox();
    const mobileReview = await review.boundingBox();
    expect(mobileReview!.y).toBeGreaterThanOrEqual(mobileEvidence!.y + mobileEvidence!.height);
    const response = await page.request.get("http://127.0.0.1:8012/investigation-candidates/synthetic-candidate-01", { headers });
    const detail = await response.json();
    for (const value of [0, null]) {
      await page.request.post("http://127.0.0.1:8012/__scenario", { headers, data: { paths: { "/investigation-candidates/synthetic-candidate-01": { body: { ...detail, distance_metres: value } } } } });
      await page.reload();
      const expected = value === null ? "Not available" : "0.0 m";
      await expect(page.locator(".case-summary dd").last()).toHaveText(expected);
      await expect(page.locator(".matched-grid div").filter({ has: page.getByText("Calculated distance", { exact: true }) }).locator("dd")).toHaveText(expected);
    }
    await page.screenshot({ path: resolve("../output/stitch-ui", info.project.name, "evidence-phone.png"), fullPage: true, style: 'body::before { content: "SYNTHETIC TEST DATA / UI VERIFICATION"; display: block; background: #0b132b; color: white; padding: 5px; text-align: center; font: 10px Arial; }' });
    await page.request.post("http://127.0.0.1:8012/__scenario", { headers, data: { paths: { "/investigation-candidates/synthetic-candidate-01/events": { delay: 2000 } } } });
    await page.getByRole("button", { name: "Save review action" }).click();
    await expect(page.getByRole("button", { name: "Saving review..." })).toBeDisabled();
    await expect(page.getByRole("status")).toContainText("saved");
    await expect(page.locator(".history-list li")).toHaveCount(1);
    await page.request.post("http://127.0.0.1:8012/__scenario", { headers, data: { paths: { "/investigation-candidates": { status: 503 } } } });
    await page.goto("/investigation-queue");
    await expect(page.locator(".global-header .live-state")).toHaveText("Data service unavailable");
  } finally {
    await reset();
  }
});
