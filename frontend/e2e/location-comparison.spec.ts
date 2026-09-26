import { expect, test, type Page } from "@playwright/test";
import { resolve } from "node:path";

const candidatePath = "/investigation-candidates/synthetic-candidate-01";
const headers = () => ({ "X-MPLADS-Review-Key": process.env.MPLADS_E2E_API_KEY! });
async function scenario(page: Page, paths: Record<string, object> = {}, reset = false) {
  const response = await page.request.post("http://127.0.0.1:8012/__scenario", { headers: headers(), data: { paths, reset } });
  expect(response.ok()).toBe(true);
}
async function candidate(page: Page) {
  const response = await page.request.get(`http://127.0.0.1:8012${candidatePath}`, { headers: headers() });
  expect(response.ok()).toBe(true);
  return response.json();
}
async function signIn(page: Page) {
  await page.goto("/login");
  await expect(page).toHaveTitle(/Suchak AI/);
  await expect(page.getByRole("img", { name: "Suchak AI", exact: true })).toBeVisible();
  expect(await page.getByRole("img", { name: "Suchak AI", exact: true }).evaluate((image) => (image as HTMLImageElement).naturalWidth)).toBe(1254);
  await page.getByLabel("Username").fill(process.env.MPLADS_E2E_USERNAME!);
  await page.getByLabel("Password", { exact: true }).fill(process.env.MPLADS_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Investigation Queue", exact: true })).toBeVisible();
}
async function openMap(page: Page) {
  await page.goto("/investigation-queue/synthetic-candidate-01");
  await expect(page.getByRole("region", { name: "India work location comparison map" })).toHaveAttribute("aria-busy", "false", { timeout: 20_000 });
}

test.beforeEach(async ({ page }) => { await scenario(page, {}, true); });
test.afterEach(async ({ page }) => { await scenario(page, {}, true); });

test("Suchak AI branding, map controls, exact markers and fetched source details work", async ({ page }, info) => {
  test.setTimeout(90_000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  const detail = await candidate(page);
  detail.source_records[1].location.latitude = 20.11;
  detail.source_records[1].location.longitude = 78.12;
  detail.source_records[1].location.last_verified_at = "2026-09-25T00:00:00+05:30";
  detail.source_records[1].cleaned_values["Source-only detail"] = "Synthetic fetched evidence B";
  await scenario(page, { [candidatePath]: { body: detail } });
  await signIn(page);
  await page.getByRole("link", { name: "Command Centre", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Review progress" })).toBeVisible();
  for (const [name, status] of [["Review new candidates", "NEW"], ["Continue active reviews", "UNDER_REVIEW"], ["Check requested verification", "VERIFICATION_REQUESTED"]]) {
    await page.getByRole("link", { name }).click();
    await expect(page.getByRole("combobox", { name: "Review status", exact: true })).toHaveValue(status);
    await page.getByRole("link", { name: "Command Centre", exact: true }).click();
  }
  await page.screenshot({ path: resolve("../output/suchak-ui", info.project.name, "command-centre.png"), fullPage: true, style: 'body::before { content: "SYNTHETIC TEST DATA"; display: block; background: #0b132b; color: white; padding: 6px; text-align: center; }' });
  await openMap(page);
  const map = page.getByRole("region", { name: "India work location comparison map" });
  await expect(map.locator(".leaflet-overlay-pane path").first()).toBeVisible();
  await expect(map.getByRole("button", { name: "Point A: SYNTHETIC/1", exact: true })).toBeVisible();
  await expect(map.getByRole("button", { name: "Point B: SYNTHETIC/2", exact: true })).toBeVisible();
  await expect(page.locator(".duplicate-comparison-alert").getByText("Potential duplicate work candidate", { exact: true })).toBeVisible();
  await expect(page.getByText("The map automatically fits the selected verified locations.", { exact: false })).toBeVisible();
  await expect(page.getByText("Distance between works:", { exact: false }).last()).toBeVisible();
  await expect(page.locator(".distance-tooltip")).toContainText("Distance between works:");
  await expect(page.locator(".map-record-a")).toContainText("Synthetic community hall 1");
  await expect(page.locator(".map-record-a")).toContainText("Test Constituency");
  await expect(page.locator(".map-record-a")).toContainText("Test Agency");
  await page.getByRole("button", { name: "Fit locations", exact: true }).click();
  await map.getByRole("button", { name: "Zoom in", exact: true }).click();
  await map.getByRole("button", { name: "Zoom out", exact: true }).click();
  const fetched = page.waitForResponse((response) => response.url().includes("/source?") && response.url().includes("record=2"));
  await map.getByRole("button", { name: "Point B: SYNTHETIC/2", exact: true }).click();
  expect((await fetched).status()).toBe(200);
  await expect(page.locator("#comparison-source-detail")).toContainText("Synthetic fetched evidence B");
  await expect(page.locator("#comparison-source-detail")).toContainText("20.11");
  await expect(page.locator("#comparison-source-detail")).toContainText("2026-09-25T00:00:00+05:30");
  await page.getByRole("button", { name: "India view", exact: true }).click();
  const pointA = map.getByRole("button", { name: "Point A: SYNTHETIC/1", exact: true });
  await pointA.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Source record details: SYNTHETIC/1", exact: true })).toBeVisible();
  await map.getByRole("button", { name: "Point B: SYNTHETIC/2", exact: true }).focus();
  await page.keyboard.press("Space");
  await expect(page.getByRole("heading", { name: "Source record details: SYNTHETIC/2", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "View source B", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Source record details: SYNTHETIC/2", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "View source A", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Source record details: SYNTHETIC/1", exact: true })).toBeVisible();
  await page.route("https://tile.openstreetmap.org/**", (route) => route.abort());
  await page.getByLabel("Street map", { exact: true }).check();
  await expect(page.getByText("Street tiles are unavailable.", { exact: false })).toBeVisible();
  await page.getByLabel("Street map", { exact: true }).uncheck();
  await expect(map.locator(".leaflet-tile-pane img")).toHaveCount(0);
  await expect(map.getByRole("link", { name: "OpenStreetMap contributors", exact: true })).toHaveCount(0);
  await page.locator(".location-map-tool").screenshot({ path: resolve("../output/suchak-ui", info.project.name, "map-desktop.png"), style: '.location-map-tool::before { content: "SYNTHETIC TEST LOCATIONS"; display: block; padding: 8px; }' });
  await page.screenshot({ path: resolve("../output/suchak-ui", info.project.name, "comparison-desktop.png"), fullPage: true, style: 'body::before { content: "SYNTHETIC TEST DATA"; display: block; background: #0b132b; color: white; padding: 6px; text-align: center; }' });
  expect(errors).toEqual([]);
});

test("co-located sources remain selectable and unavailable coordinates are never fabricated", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  await openMap(page);
  await expect(page.getByText("Both records have the same verified coordinates.", { exact: false })).toBeVisible();
  for (const [letter, id] of [["A", "1"], ["B", "2"]]) {
    await page.getByRole("button", { name: `Point ${letter}: SYNTHETIC/${id}`, exact: true }).click();
    await expect(page.getByRole("heading", { name: `Source record details: SYNTHETIC/${id}`, exact: true })).toBeVisible();
  }
  await page.locator(".location-map-tool").screenshot({ path: resolve("../output/suchak-ui", info.project.name, "map-phone-coincident.png"), style: '.location-map-tool::before { content: "SYNTHETIC TEST LOCATIONS"; display: block; padding: 8px; }' });
  const detail = await candidate(page);
  detail.source_records[0].location.status = "ADMINISTRATIVE_ONLY";
  detail.source_records[1].location.latitude = 200;
  await scenario(page, { [candidatePath]: { body: detail } });
  await page.reload();
  await expect(page.getByRole("region", { name: "India work location comparison map" })).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".comparison-marker")).toHaveCount(0);
  await expect(page.getByText("Exact point unavailable: verified coordinates required.", { exact: true })).toHaveCount(2);
  await expect(page.getByRole("button", { name: "Fit locations", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "View source A", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Source record details: SYNTHETIC/1", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: resolve("../output/suchak-ui", info.project.name, "comparison-phone-unavailable.png"), fullPage: true, style: 'body::before { content: "SYNTHETIC TEST DATA"; display: block; background: #0b132b; color: white; padding: 6px; text-align: center; }' });
});

test("larger groups support pair selection and stale detail requests cannot replace the current source", async ({ page }) => {
  const detail = await candidate(page);
  detail.source_records.push({ ...detail.source_records[1], record_number: 3, work_id: "SYNTHETIC/3", location: { ...detail.source_records[1].location, latitude: 21, longitude: 79 } });
  await scenario(page, { [candidatePath]: { body: detail } });
  await signIn(page);
  await openMap(page);
  await page.getByLabel("Work B", { exact: true }).selectOption("2");
  await expect(page.getByRole("button", { name: "Point B: SYNTHETIC/3", exact: true })).toBeVisible();
  await expect(page.locator(".distance-tooltip")).toContainText("Distance between works:");
  await expect(page.getByLabel("Work A", { exact: true }).locator('option[value="2"]')).toBeDisabled();
  await page.getByLabel("Work A", { exact: true }).selectOption("1");
  let finishDelayedRequest!: () => void;
  const delayedRequest = new Promise<void>((resolveRequest) => { finishDelayedRequest = resolveRequest; });
  await page.route("**/source?*", async (route) => {
    const delayed = new URL(route.request().url()).searchParams.get("record") === "2";
    if (delayed) await new Promise((resolveDelay) => setTimeout(resolveDelay, 700));
    await route.continue().catch(() => undefined);
    if (delayed) finishDelayedRequest();
  });
  await page.getByRole("button", { name: "View source A", exact: true }).click();
  await expect(page.locator("#comparison-source-detail")).toHaveAttribute("aria-busy", "true");
  await page.getByRole("button", { name: "View source B", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Source record details: SYNTHETIC/3", exact: true })).toBeVisible();
  await delayedRequest;
  await page.getByRole("button", { name: "India view", exact: true }).click();
  await expect(page.locator("#comparison-source-detail")).not.toContainText("Source record details: SYNTHETIC/2");
});

test("map and details recover from failures and source requests require authenticated membership", async ({ page }) => {
  const sourceUrl = "/investigation-queue/synthetic-candidate-01/source?sha=synthetic-source-sha256&parser=test&record=1";
  expect((await page.request.get(sourceUrl)).status()).toBe(401);
  await signIn(page);
  expect((await page.request.get(sourceUrl.replace("record=1", "record=0"))).status()).toBe(400);
  expect((await page.request.get(sourceUrl.replace("record=1", "record=99"))).status()).toBe(404);
  const authenticated = await page.request.get(sourceUrl);
  expect(authenticated.headers()["cache-control"]).toContain("no-store");
  expect((await authenticated.json()).source.record_number).toBe(1);
  await page.route("**/maps/india.geojson", (route) => route.fulfill({ status: 503, body: "Unavailable" }));
  await openMap(page);
  await expect(page.getByText("India outline could not be loaded.", { exact: false })).toBeVisible();
  await page.unroute("**/maps/india.geojson");
  await page.getByRole("button", { name: "Retry map", exact: true }).click();
  await expect(page.locator(".map-load-error")).toHaveCount(0);
  await expect(page.locator(".comparison-marker")).toHaveCount(2);
  await scenario(page, { [candidatePath]: { status: 503 } });
  await page.getByRole("button", { name: "View source B", exact: true }).click();
  await expect(page.locator("#comparison-source-detail")).toContainText("Source details could not be loaded.");
  await scenario(page);
  await page.getByRole("button", { name: "Retry source details", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Source record details: SYNTHETIC/2", exact: true })).toBeVisible();
  await page.route("**/source?*", (route) => route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ error: "Session expired" }) }));
  await page.getByRole("button", { name: "View source A", exact: true }).click();
  await expect(page.getByRole("link", { name: "Sign in again", exact: true })).toBeVisible();
  await page.context().clearCookies();
  await page.getByRole("link", { name: "Sign in again", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("map loading does not shift the tablet review form", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1024 });
  await signIn(page);
  let release!: () => void;
  const delayed = new Promise<void>((resolveDelay) => { release = resolveDelay; });
  await page.route("**/maps/india.geojson", async (route) => { await delayed; await route.continue(); });
  await page.goto("/investigation-queue/synthetic-candidate-01");
  await expect(page.getByText("Loading India map...", { exact: true })).toBeVisible();
  const save = page.getByRole("button", { name: "Save review action", exact: true });
  await save.scrollIntoViewIfNeeded();
  const before = await save.evaluate((element) => element.getBoundingClientRect().top + scrollY);
  release();
  await expect(page.getByRole("region", { name: "India work location comparison map" })).toHaveAttribute("aria-busy", "false");
  const after = await save.evaluate((element) => element.getBoundingClientRect().top + scrollY);
  expect(Math.abs(after - before)).toBeLessThanOrEqual(1);
  await save.click();
  await expect(page.getByRole("status")).toContainText("saved");
});
