import { expect, test, type Page, type TestInfo } from "@playwright/test";
import { resolve } from "node:path";

const sizes = [
  { name: "small-phone", width: 320, height: 568 },
  { name: "phone", width: 390, height: 844 },
  { name: "phone-landscape", width: 844, height: 390 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "tablet-landscape", width: 1024, height: 768 },
  { name: "laptop", width: 1280, height: 800 },
  { name: "desktop", width: 1440, height: 900 },
  { name: "large-desktop", width: 1920, height: 1080 },
];

async function scenario(page: Page, paths: Record<string, object> = {}, reset = false) {
  const response = await page.request.post("http://127.0.0.1:8012/__scenario", {
    headers: { "X-MPLADS-Review-Key": process.env.MPLADS_E2E_API_KEY! },
    data: { paths, reset },
  });
  expect(response.ok()).toBe(true);
}

async function signIn(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Username").fill(process.env.MPLADS_E2E_USERNAME!);
  await page.getByLabel("Password").fill(process.env.MPLADS_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Investigation Queue", exact: true })).toBeVisible();
}

async function capture(page: Page, info: TestInfo, size: string, state: string) {
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth), `${size}/${state}: horizontal overflow`).toBeLessThanOrEqual(1);
  const outside = await page.locator("button, input:not([type=hidden]), select, textarea, .nav-link, .source-card").evaluateAll((elements) => elements.filter((element) => {
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && (rect.left < -1 || rect.right > innerWidth + 1);
  }).map((element) => element.outerHTML.slice(0, 150)));
  expect(outside, `${size}/${state}: clipped controls or cards`).toEqual([]);
  if (process.env.CAPTURE_UI === "1") {
    await page.screenshot({
      path: resolve("../output/responsiveness", info.project.name, size, `${state}.png`),
      fullPage: true, animations: "disabled",
      style: 'body::before { content: "SYNTHETIC TEST DATA / UI VERIFICATION"; display: block; background: #24145c; color: white; padding: 5px; text-align: center; font: 10px Arial; }',
    });
  }
}

test.beforeEach(async ({ page }) => { await scenario(page, {}, true); });
test.afterEach(async ({ page }) => { await scenario(page, {}, true); });

for (const size of sizes) {
  test(`responsive routes: ${size.name} ${size.width}x${size.height}`, async ({ page }, info) => {
    test.setTimeout(90_000);
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.setViewportSize(size);
    await page.goto("/login");
    await capture(page, info, size.name, "01-login");
    await signIn(page);
    await capture(page, info, size.name, "02-queue");
    await page.getByRole("link", { name: "Review evidence", exact: true }).filter({ visible: true }).first().click();
    await expect(page.getByRole("heading", { name: "Why this was flagged" })).toBeVisible();
    await capture(page, info, size.name, "03-evidence");
    await page.getByLabel("Reviewer notes").fill("Synthetic responsive verification only.");
    await page.getByRole("button", { name: "Save review action" }).click();
    await expect(page.getByRole("status")).toContainText("saved");
    await capture(page, info, size.name, "04-review-saved");
    await page.getByRole("link", { name: "Command Centre", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Investigation workload" })).toBeVisible();
    await capture(page, info, size.name, "05-command-centre");
    await page.getByRole("link", { name: "Data Quality", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Data Quality", exact: true })).toBeVisible();
    await capture(page, info, size.name, "05-data-quality");
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/login/);
    expect(errors).toEqual([]);
  });
}

for (const size of sizes.filter(({ name }) => ["phone", "tablet", "desktop"].includes(name))) {
  test(`responsive states: ${size.name}`, async ({ page }, info) => {
    test.setTimeout(120_000);
    await page.setViewportSize(size);
    await page.goto("/login");
    await page.getByLabel("Username").fill("incorrect");
    await page.getByLabel("Password").fill("incorrect");
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.locator("main").getByRole("alert")).toContainText("incorrect");
    await capture(page, info, size.name, "06-login-error");
    await signIn(page);
    await page.getByLabel("Search evidence").fill("no-matching-record");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await expect(page.getByRole("heading", { name: "No candidates match these filters" })).toBeVisible();
    await capture(page, info, size.name, "07-queue-empty");
    await page.getByRole("link", { name: "Clear", exact: true }).click();
    await page.getByLabel("State", { exact: true }).selectOption("Test State Two");
    await page.getByLabel("Order by").selectOption("state");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await expect(page).toHaveURL(/state=Test/);
    await capture(page, info, size.name, "08-queue-filtered");
    await page.route("**/investigation-queue/export?*", async (route) => {
      await new Promise((done) => setTimeout(done, 1500));
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ error: "Synthetic export failure. Retry." }) });
    });
    await page.getByRole("button", { name: "Export filtered CSV" }).click();
    await expect(page.getByRole("button", { name: "Preparing CSV..." })).toBeDisabled();
    await capture(page, info, size.name, "09-export-loading");
    await expect(page.locator("main").getByRole("alert")).toContainText("Synthetic export failure");
    await capture(page, info, size.name, "10-export-error");
    await page.unroute("**/investigation-queue/export?*");
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Export filtered CSV" }).click();
    await download;
    await expect(page.getByRole("status")).toContainText("download started");
    await capture(page, info, size.name, "11-export-success");
    await page.goto("/investigation-queue/synthetic-candidate-01");
    await scenario(page, { "/investigation-candidates/synthetic-candidate-01/events": { status: 503 } });
    await page.getByRole("button", { name: "Save review action" }).click();
    await expect(page.locator("main").getByRole("alert")).toContainText("Synthetic service failure");
    await capture(page, info, size.name, "12-review-error");
    await scenario(page);
    await page.goto("/investigation-queue/missing-candidate");
    await expect(page.getByRole("heading", { name: "Candidate not found" })).toBeVisible();
    await capture(page, info, size.name, "13-candidate-not-found");
    for (const [api, route, heading, file] of [
      ["/investigation-candidates", "/investigation-queue", "Investigation Queue unavailable", "14-queue-error"],
      ["/investigation-candidates/synthetic-candidate-01", "/investigation-queue/synthetic-candidate-01", "Candidate unavailable", "15-evidence-error"],
      ["/data-overview", "/command-centre", "Data service unavailable", "16-command-error"],
      ["/data-overview", "/data-quality", "Data service unavailable", "16-data-quality-error"],
    ]) {
      await scenario(page, { [api]: { status: 503 } });
      await page.goto(route);
      await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
      await capture(page, info, size.name, file);
      await scenario(page);
      await page.getByRole("link", { name: /^(Retry|Return to queue|Retry connection)$/ }).click();
      await expect(page.locator(".error-panel")).toHaveCount(0);
    }
    await scenario(page, { "/data-overview": { body: { source_batches: 0, retained_records: 0, detail_records: 0, summary_records: 0, rejected_records: 0, records_with_validation_issues: 0, sources: [] } } });
    await page.goto("/data-quality");
    await expect(page.getByRole("heading", { name: "No staged source reports" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Data Quality", exact: true })).toHaveAttribute("aria-current", "page");
    await capture(page, info, size.name, "17-data-quality-empty");
    for (const [api, route, label, file] of [
      ["/data-overview", "/command-centre", "Loading command centre", "18-command-loading"],
      ["/data-overview", "/data-quality", "Loading Data Quality", "18-data-quality-loading"],
      ["/investigation-candidates", "/investigation-queue", "Loading Investigation Queue", "19-queue-loading"],
    ]) {
      await scenario(page, { [api]: { delay: 2500 } });
      await page.goto(route, { waitUntil: "commit" });
      await expect(page.getByRole("main", { name: label })).toBeVisible();
      await capture(page, info, size.name, file);
      await expect(page.locator("main[aria-busy=true]")).toHaveCount(0);
    }
    await scenario(page);
    await page.goto("/investigation-queue");
    await page.getByRole("link", { name: "Next", exact: true }).click();
    await expect(page.getByText("Page 2 of 2")).toBeVisible();
    await capture(page, info, size.name, "20-queue-page-two");
    await page.goto("/investigation-queue/synthetic-candidate-01");
    await page.getByRole("button", { name: "Save review action" }).click();
    await expect(page.getByRole("status")).toContainText("saved");
    for (const [status, file] of [
      ["VERIFICATION_REQUESTED", "21-verification-requested"],
      ["RESOLVED", "22-review-resolved"],
      ["UNDER_REVIEW", "23-review-reopened"],
      ["DISMISSED", "24-review-dismissed"],
    ]) {
      await page.getByLabel("Next status").selectOption(status);
      await page.getByLabel("Decision, required when resolving or dismissing").selectOption("INSUFFICIENT_EVIDENCE");
      await page.getByLabel("Reason code, required when dismissing").selectOption("DOCUMENTS_UNAVAILABLE");
      await page.getByLabel("Reviewer notes").fill("Synthetic UI transition test only. No official case was reviewed.");
      await page.getByRole("button", { name: "Save review action" }).click();
      await expect(page.locator(".page-heading-row .status-chip")).toHaveText(status.toLowerCase().replaceAll("_", " "));
      await capture(page, info, size.name, file);
    }
  });
}

test("reflow and long evidence remain readable with keyboard access", async ({ page }, info) => {
  await page.setViewportSize({ width: 640, height: 450 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await signIn(page);
  await page.goto("/investigation-queue");
  await expect(page.getByRole("heading", { name: "Candidates requiring review" })).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to main content" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("main#main-content")).toBeFocused();
  await capture(page, info, "reflow-200-percent", "01-queue-keyboard");
  await page.goto("/investigation-queue/synthetic-candidate-01");
  const response = await page.request.get("http://127.0.0.1:8012/investigation-candidates/synthetic-candidate-01", { headers: { "X-MPLADS-Review-Key": process.env.MPLADS_E2E_API_KEY! } });
  const detail = await response.json();
  detail.evidence.matched_values["Long synthetic identifier"] = "SYNTHETIC".repeat(40);
  detail.source_records[0].work_id = "SYNTHETIC".repeat(40);
  await scenario(page, { "/investigation-candidates/synthetic-candidate-01": { body: detail } });
  await page.reload();
  await capture(page, info, "reflow-200-percent", "02-long-evidence");
});
