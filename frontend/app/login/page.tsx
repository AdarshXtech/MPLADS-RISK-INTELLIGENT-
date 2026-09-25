import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { sessionUsername } from "@/lib/auth";
import { login } from "./actions";
import { Info, ShieldCheck, UserRound } from "lucide-react";
import { PasswordField } from "./password-field";
import { SubmitButton } from "../submit-button";
import { Brand } from "../brand";

export const metadata: Metadata = { title: "Reviewer sign in" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  if (await sessionUsername()) redirect("/investigation-queue");
  const { error } = await searchParams;
  return (
    <div className="auth-shell">
    <header className="auth-header"><span className="auth-sync"><i aria-hidden="true" />Review service secured</span><span><ShieldCheck size={15} aria-hidden="true" /> Authorised reviewer access</span></header>
    <main className="login-page" id="main-content">
      <section className="login-card" aria-labelledby="login-title">
        <Brand className="login-brand" />
        <p className="login-module">MPLADS Risk Intelligence and Early Warning System</p>
        <p className="eyebrow">Restricted access</p>
        <h1 id="login-title">Reviewer sign in</h1>
        <p className="page-intro">Sign in to inspect potential duplicate candidates and record verification decisions.</p>
        {error === "credentials" && <p className="form-error" role="alert">The username or password is incorrect.</p>}
        {error === "configuration" && <p className="form-error" role="alert">Reviewer access is not configured. Contact the project administrator.</p>}
        <form className="stack-form" action={login}>
          <label htmlFor="username">Username</label>
          <div className="input-with-icon"><UserRound size={17} aria-hidden="true" /><input id="username" name="username" autoComplete="username" required /></div>
          <label htmlFor="password">Password</label>
          <PasswordField />
          <SubmitButton pendingLabel="Signing in..." variant="login">Sign in</SubmitButton>
        </form>
        <p className="boundary-copy"><Info size={17} aria-hidden="true" /><span>Access is limited to authorised reviewers. A risk candidate is not proof of duplication, misuse or fraud.</span></p>
      </section>
    </main>
    <footer className="auth-footer"><span>Suchak AI administrative review</span><span>Screening results require official verification</span></footer>
    </div>
  );
}
