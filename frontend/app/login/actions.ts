"use server";

import { redirect } from "next/navigation";
import { createSession, credentialsAreValid, reportLoginFailure } from "@/lib/auth";

export async function login(formData: FormData) {
  const username = String(formData.get("username") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  let valid = false;
  try {
    valid = credentialsAreValid(username, password);
  } catch (error) {
    reportLoginFailure("credentials", error);
    redirect("/login?error=configuration");
  }
  if (!valid) redirect("/login?error=credentials");
  try {
    await createSession(username);
  } catch (error) {
    reportLoginFailure("session", error);
    redirect("/login?error=configuration");
  }
  redirect("/investigation-queue");
}
