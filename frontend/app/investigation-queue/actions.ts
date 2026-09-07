"use server";

import { redirect } from "next/navigation";
import { clearSession, requireReviewer } from "@/lib/auth";
import { saveReview } from "@/lib/investigations";

export async function logout() {
  await clearSession();
  redirect("/login");
}

export async function updateCandidate(id: string, formData: FormData) {
  const reviewer = await requireReviewer();
  const expected = String(formData.get("expected_status") ?? "");
  const target = String(formData.get("target_status") ?? "");
  const optional = (name: string) => String(formData.get(name) ?? "").trim() || null;
  try {
    await saveReview(id, reviewer, {
      expected_status: expected,
      target_status: target,
      decision: optional("decision"),
      reason_code: optional("reason_code"),
      documents_checked: optional("documents_checked"),
      evidence_references: optional("evidence_references"),
      notes: optional("notes"),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Review could not be saved";
    redirect(`/investigation-queue/${encodeURIComponent(id)}?error=${encodeURIComponent(message)}`);
  }
  redirect(`/investigation-queue/${encodeURIComponent(id)}?saved=1`);
}
