import { randomBytes, randomUUID } from "node:crypto";
import { defineConfig, devices } from "@playwright/test";

process.env.MPLADS_E2E_USERNAME ??= `reviewer-${randomUUID()}`;
process.env.MPLADS_E2E_PASSWORD ??= randomBytes(24).toString("hex");
process.env.MPLADS_E2E_API_KEY ??= randomBytes(24).toString("hex");
process.env.MPLADS_E2E_SESSION_SECRET ??= randomBytes(32).toString("hex");

const frontendEnvironment = {
  MPLADS_API_BASE_URL: "http://127.0.0.1:8012",
  MPLADS_REVIEW_API_KEY: process.env.MPLADS_E2E_API_KEY,
  MPLADS_REVIEW_USERNAME: process.env.MPLADS_E2E_USERNAME,
  MPLADS_REVIEW_PASSWORD: process.env.MPLADS_E2E_PASSWORD,
  MPLADS_SESSION_SECRET: process.env.MPLADS_E2E_SESSION_SECRET,
  MPLADS_SECURE_COOKIES: "false",
};

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:3012", trace: "retain-on-failure" },
  webServer: [
    { command: "node e2e/mock-api.mjs", port: 8012, env: { MPLADS_REVIEW_API_KEY: process.env.MPLADS_E2E_API_KEY }, reuseExistingServer: false },
    { command: "npm run build && npm run start -- --port 3012", port: 3012, env: frontendEnvironment, reuseExistingServer: false, timeout: 120_000 },
  ],
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
