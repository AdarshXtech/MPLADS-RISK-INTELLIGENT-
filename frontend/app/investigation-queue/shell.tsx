import Link from "next/link";
import { logout } from "./actions";

export function QueueShell({ username, children, active = "investigation-queue", connected = true }: { username: string; children: React.ReactNode; active?: "command-centre" | "investigation-queue"; connected?: boolean }) {
  return <>
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark" aria-hidden="true">M</span><div><p className="brand-name">MPLADS RISK</p><p className="brand-context">Monitoring support</p></div></div>
        <p className="nav-section-label">Triage console</p>
        <nav className="primary-nav" aria-label="Primary navigation">
          <Link className="nav-link" href="/command-centre" aria-current={active === "command-centre" ? "page" : undefined}>Command Centre</Link>
          <Link className="nav-link" href="/investigation-queue" aria-current={active === "investigation-queue" ? "page" : undefined}>Investigation Queue</Link>
          <Link className="nav-link" href="/command-centre#data-quality">Data Quality</Link>
        </nav>
        <div className="session-status"><span className={`live-state${connected ? "" : " offline"}`}>{connected ? "Data service connected" : "Data service unavailable"}</span><p>Signed in as</p><strong>{username}</strong></div>
      </aside>
      <div className="workspace">
        <header className="utility-bar"><div><p className="utility-label">Review session</p><p className="utility-value">{username}</p></div><form action={logout}><button className="secondary-button" type="submit">Sign out</button></form></header>
        {children}
      </div>
    </div>
  </>;
}
