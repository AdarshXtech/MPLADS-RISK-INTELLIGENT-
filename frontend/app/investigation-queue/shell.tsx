import Link from "next/link";
import { Database, LayoutDashboard, LogOut, Radar, ShieldCheck, UserRound } from "lucide-react";
import { logout } from "./actions";
import { Brand } from "../brand";

export function QueueShell({ username, children, active = "investigation-queue", connected = true }: { username: string; children: React.ReactNode; active?: "command-centre" | "investigation-queue"; connected?: boolean }) {
  return <>
    <a className="skip-link" href="#main-content" tabIndex={0}>Skip to main content</a>
    <header className="global-header">
      <Brand />
      <div className="header-session">
        <span className={`live-state${connected ? "" : " offline"}`}>{connected ? "Data service connected" : "Data service unavailable"}</span>
        <div className="reviewer-identity"><UserRound size={18} aria-hidden="true" /><div><p className="utility-label">Reviewer</p><p className="utility-value">{username}</p></div></div>
        <form action={logout}><button className="header-signout" type="submit"><LogOut size={16} aria-hidden="true" /><span>Sign out</span></button></form>
      </div>
    </header>
    <div className="app-shell">
      <aside className="sidebar">
        <div className="workspace-brand"><ShieldCheck size={24} aria-hidden="true" /><div><strong>Review workspace</strong><p>Administrative verification</p></div></div>
        <p className="nav-section-label">Monitoring &amp; review</p>
        <nav className="primary-nav" aria-label="Primary navigation">
          <Link className="nav-link" href="/command-centre" aria-current={active === "command-centre" ? "page" : undefined}><LayoutDashboard size={18} aria-hidden="true" /><span>Command Centre</span></Link>
          <Link className="nav-link" href="/investigation-queue" aria-current={active === "investigation-queue" ? "page" : undefined}><Radar size={18} aria-hidden="true" /><span>Investigation Queue</span></Link>
          <Link className="nav-link" href="/command-centre#data-quality"><Database size={18} aria-hidden="true" /><span>Data Quality</span></Link>
        </nav>
        <div className="session-status"><ShieldCheck size={18} aria-hidden="true" /><strong>Evidence-led review</strong><p>Screening indicators require verification against source records.</p></div>
      </aside>
      <div className="workspace">
        {children}
        <footer className="workspace-footer"><span>Suchak AI</span><span>MPLADS administrative decision support</span></footer>
      </div>
    </div>
  </>;
}
