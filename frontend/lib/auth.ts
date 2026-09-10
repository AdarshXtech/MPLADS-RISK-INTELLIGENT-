import "server-only";

import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const COOKIE_NAME = "mplads_review_session";
const SESSION_SECONDS = 8 * 60 * 60;

export function reportLoginFailure(stage: "credentials" | "session", error: unknown): void {
  // Log binding availability only, never credentials, cookies or raw exceptions.
  console.error("[mplads-auth]", JSON.stringify({
    stage,
    errorType: error instanceof TypeError ? "TypeError"
      : error instanceof ReferenceError ? "ReferenceError"
      : error instanceof Error ? "Error" : "UnknownError",
    configured: {
      MPLADS_REVIEW_USERNAME: Boolean(process.env.MPLADS_REVIEW_USERNAME),
      MPLADS_REVIEW_PASSWORD: Boolean(process.env.MPLADS_REVIEW_PASSWORD),
      MPLADS_SESSION_SECRET: Boolean(process.env.MPLADS_SESSION_SECRET),
    },
  }));
}

function secret(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is not configured`);
  return value;
}

function same(left: string, right: string): boolean {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

function signature(payload: string): string {
  return createHmac("sha256", secret("MPLADS_SESSION_SECRET"))
    .update(payload)
    .digest("base64url");
}

export function credentialsAreValid(username: string, password: string): boolean {
  return same(username, secret("MPLADS_REVIEW_USERNAME")) &&
    same(password, secret("MPLADS_REVIEW_PASSWORD"));
}

export async function createSession(username: string): Promise<void> {
  const payload = Buffer.from(JSON.stringify({
    username,
    expires: Math.floor(Date.now() / 1000) + SESSION_SECONDS,
  })).toString("base64url");
  (await cookies()).set(COOKIE_NAME, `${payload}.${signature(payload)}`, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production" && process.env.MPLADS_SECURE_COOKIES !== "false",
    path: "/",
    maxAge: SESSION_SECONDS,
  });
}

export async function sessionUsername(): Promise<string | null> {
  const token = (await cookies()).get(COOKIE_NAME)?.value;
  if (!token) return null;
  const [payload, suppliedSignature] = token.split(".");
  if (!payload || !suppliedSignature || !same(signature(payload), suppliedSignature)) return null;
  try {
    const session = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    return typeof session.username === "string" &&
      typeof session.expires === "number" && session.expires > Date.now() / 1000
      ? session.username : null;
  } catch {
    return null;
  }
}

export async function requireReviewer(): Promise<string> {
  const username = await sessionUsername();
  if (!username) redirect("/login");
  return username;
}

export async function clearSession(): Promise<void> {
  (await cookies()).delete(COOKIE_NAME);
}
