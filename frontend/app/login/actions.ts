"use server";

import { redirect } from "next/navigation";
import { createSession, credentialsAreValid } from "@/lib/auth";

export async function login(formData: FormData) {
  const username = String(formData.get("username") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  let valid = false;
  try {
    valid = credentialsAreValid(username, password);
  } catch {
    redirect("/login?error=configuration");
  }
  if (!valid) redirect("/login?error=credentials");
  try {
    await createSession(username);
  } catch {
    redirect("/login?error=configuration");
  }
  redirect("/investigation-queue");
}
