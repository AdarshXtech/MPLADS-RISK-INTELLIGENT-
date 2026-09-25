import assert from "node:assert/strict";
import { randomBytes } from "node:crypto";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { chromium } from "@playwright/test";
import { unstable_dev } from "wrangler";

// Synthetic credentials and local Workers only. No official data or remote API.
const temporaryRoot = path.resolve(".wrangler");
mkdirSync(temporaryRoot, { recursive: true });
const directory = mkdtempSync(path.join(temporaryRoot, "auth-test-"));
const credentials = {
  MPLADS_REVIEW_USERNAME: "synthetic-reviewer",
  MPLADS_REVIEW_PASSWORD: randomBytes(24).toString("hex"),
  MPLADS_SESSION_SECRET: randomBytes(32).toString("hex"),
  MPLADS_REVIEW_API_KEY: randomBytes(24).toString("hex"),
  MPLADS_API_BASE_URL: "http://127.0.0.1:1",
  MPLADS_SECURE_COOKIES: "false",
};
const browser = await chromium.launch({
  channel: process.env.MPLADS_E2E_BROWSER_CHANNEL || undefined,
});
const output = [];
const originalWrites = [process.stdout.write, process.stderr.write];
for (const [index, stream] of [process.stdout, process.stderr].entries()) {
  stream.write = function (chunk, ...args) {
    output.push(String(chunk));
    return originalWrites[index].call(this, chunk, ...args);
  };
}

try {
  for (const missing of [null, "MPLADS_REVIEW_USERNAME", "MPLADS_REVIEW_PASSWORD", "MPLADS_SESSION_SECRET"]) {
    const vars = { ...credentials };
    // An explicit empty binding also overrides any build-time environment value.
    if (missing) vars[missing] = "";
    const envFile = path.join(directory, "synthetic.env");
    writeFileSync(envFile, Object.entries(vars).map(([key, value]) => `${key}=${value}`).join("\n"));
    const worker = await unstable_dev(".open-next/worker.js", {
      config: "wrangler.jsonc",
      envFiles: [envFile],
      port: 0,
      inspectorPort: 0,
      local: true,
      persist: false,
      logLevel: "error",
      experimental: { disableExperimentalWarning: true, disableDevRegistry: true, watch: false },
    });
    const context = await browser.newContext();
    const start = output.length;
    try {
      const page = await context.newPage();
      await page.goto(`http://${worker.address}:${worker.port}/login`);
      if (!missing) {
        await page.getByLabel("Username", { exact: true }).fill("synthetic-wrong-reviewer");
        await page.getByLabel("Password", { exact: true }).fill("synthetic-wrong-password");
        await page.getByRole("button", { name: "Sign in", exact: true }).click();
        await page.waitForURL("**/login?error=credentials");
        assert.equal((await context.cookies()).some(cookie => cookie.name === "mplads_review_session"), false);
      }
      await page.getByLabel("Username", { exact: true }).fill(credentials.MPLADS_REVIEW_USERNAME);
      await page.getByLabel("Password", { exact: true }).fill(credentials.MPLADS_REVIEW_PASSWORD);
      await page.getByRole("button", { name: "Sign in", exact: true }).click();
      await page.waitForURL(missing ? "**/login?error=configuration" : "**/investigation-queue");
      const session = (await context.cookies()).find(cookie => cookie.name === "mplads_review_session");
      assert.equal(Boolean(session), !missing);
      if (session) {
        assert.equal(session.httpOnly, true);
        assert.equal(session.sameSite, "Lax");
      }
    } finally {
      await context.close();
      await worker.stop();
    }
    const logs = output.slice(start).join("");
    if (missing) {
      assert.ok(logs.includes("[mplads-auth]"), "Login failure must produce a safe server diagnostic");
      assert.ok(logs.includes(`\"${missing}\":false`), "Diagnostic must identify the unavailable variable");
      const stage = missing === "MPLADS_SESSION_SECRET" ? "session" : "credentials";
      assert.ok(logs.includes(`\"stage\":\"${stage}\"`), "Diagnostic must identify the failed stage");
    } else {
      assert.equal(logs.includes("[mplads-auth]"), false);
    }
    for (const value of [credentials.MPLADS_REVIEW_PASSWORD, credentials.MPLADS_SESSION_SECRET, credentials.MPLADS_REVIEW_API_KEY]) {
      assert.equal(logs.includes(value), false, "Secret values must not appear in logs");
    }
    console.log(`PASS: ${missing ? `missing ${missing}` : "valid login and invalid credentials"}`);
  }
} finally {
  process.stdout.write = originalWrites[0];
  process.stderr.write = originalWrites[1];
  await browser.close();
  assert.equal(path.dirname(directory), temporaryRoot);
  rmSync(directory, { recursive: true, force: true });
}
