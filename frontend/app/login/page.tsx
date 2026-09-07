import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { sessionUsername } from "@/lib/auth";
import { login } from "./actions";

export const metadata: Metadata = { title: "Reviewer sign in" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  if (await sessionUsername()) redirect("/investigation-queue");
  const { error } = await searchParams;
  return (
    <main className="login-page" id="main-content">
      <section className="login-card" aria-labelledby="login-title">
        <div className="brand login-brand"><span className="brand-mark" aria-hidden="true">M</span><div><p className="brand-name">MPLADS RISK</p><p className="brand-context">Administrative review</p></div></div>
        <p className="eyebrow">Restricted access</p>
        <h1 id="login-title">Reviewer sign in</h1>
        <p className="page-intro">Sign in to inspect potential duplicate candidates and record verification decisions.</p>
        {error === "credentials" && <p className="form-error" role="alert">The username or password is incorrect.</p>}
        {error === "configuration" && <p className="form-error" role="alert">Reviewer access is not configured. Contact the project administrator.</p>}
        <form className="stack-form" action={login}>
          <label htmlFor="username">Username</label>
          <input id="username" name="username" autoComplete="username" required />
          <label htmlFor="password">Password</label>
          <input id="password" name="password" type="password" autoComplete="current-password" required />
          <button type="submit">Sign in</button>
        </form>
        <p className="boundary-copy">Access is limited to authorised reviewers. A risk candidate is not proof of duplication, misuse or fraud.</p>
      </section>
    </main>
  );
}
