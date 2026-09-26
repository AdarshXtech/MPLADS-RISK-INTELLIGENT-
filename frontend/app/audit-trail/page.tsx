import type { Metadata } from "next";
import Link from "next/link";
import { History, ListFilter } from "lucide-react";
import { requireReviewer } from "@/lib/auth";
import { getReviewEvents, type Status } from "@/lib/investigations";
import { QueueShell } from "../investigation-queue/shell";

export const metadata: Metadata = { title: "Review Audit Trail" };
const integer = new Intl.NumberFormat("en-IN");
const dateTime = new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Kolkata" });
const statusLabel = (status: Status) => status.toLowerCase().replaceAll("_", " ");
const statuses: Array<{ value: Exclude<Status, "NEW"> | ""; label: string }> = [
  { value: "", label: "All recorded actions" },
  { value: "UNDER_REVIEW", label: "Under review" },
  { value: "VERIFICATION_REQUESTED", label: "Verification requested" },
  { value: "RESOLVED", label: "Resolved" },
  { value: "DISMISSED", label: "Dismissed" },
];
type Params = { page?: string; query?: string; status?: string };

export default async function AuditTrailPage({ searchParams }: { searchParams: Promise<Params> }) {
  const username = await requireReviewer();
  const supplied = await searchParams;
  const page = Math.max(1, Number.parseInt(supplied.page ?? "1", 10) || 1);
  const parameters = new URLSearchParams({ page: String(page), page_size: "20" });
  if (supplied.query) parameters.set("query", supplied.query);
  if (supplied.status) parameters.set("status", supplied.status);
  let result;
  try {
    result = await getReviewEvents(parameters);
  } catch {
    return <QueueShell username={username} active="audit-trail" connected={false}><main className="page-content" id="main-content" tabIndex={-1}><section className="error-panel" role="alert"><h1>Review Audit Trail unavailable</h1><p>The review service could not load recorded actions. Existing review records have not been changed.</p><Link className="retry-link" href="/audit-trail?retry=1">Retry</Link></section></main></QueueShell>;
  }
  const preserved = new URLSearchParams();
  if (supplied.query) preserved.set("query", supplied.query);
  if (supplied.status) preserved.set("status", supplied.status);
  const pageHref = (next: number) => { const nextParams = new URLSearchParams(preserved); nextParams.set("page", String(next)); return `?${nextParams}`; };
  const lastPage = Math.max(1, Math.ceil(result.total / result.page_size));

  return <QueueShell username={username} active="audit-trail"><main className="page-content" id="main-content" tabIndex={-1}>
    <div className="page-heading-row"><div><p className="eyebrow">Append-only review history</p><h1>Review Audit Trail</h1><p className="page-intro">Recorded reviewer transitions for the latest reviewable screening run. Detector evidence remains unchanged.</p></div><p className="view-label"><History size={15} aria-hidden="true" /> {integer.format(result.total)} events</p></div>
    <aside className="notice" aria-label="Audit trail boundary"><span className="notice-mark" aria-hidden="true">i</span><div><strong>Administrative record, not a statutory ledger</strong><p>This view reports stored review events. It does not claim cryptographic certification or legal attestation.</p></div></aside>
    <form className="filter-bar audit-filter-bar" key={preserved.toString()} method="get" role="search">
      <div className="filter-heading"><ListFilter size={17} aria-hidden="true" /><span>Audit filters</span></div>
      <div><label htmlFor="query">Search recorded actions</label><input id="query" name="query" defaultValue={supplied.query} placeholder="Candidate, work, reviewer or evidence" /></div>
      <div><label htmlFor="status">Recorded status</label><select id="status" name="status" defaultValue={supplied.status ?? ""}>{statuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}</select></div>
      <button type="submit">Apply filters</button><Link className="secondary-link" href="/audit-trail">Clear</Link>
    </form>
    {result.items.length === 0 ? <section className="empty-panel"><h2>No review actions recorded</h2><p>{supplied.query || supplied.status ? "Change or clear the filters to inspect other recorded actions." : "Review events will appear here after an authorised reviewer records a candidate transition."}</p></section> : <section className="panel" aria-labelledby="audit-events-title">
      <div className="panel-header"><div><h2 className="panel-title" id="audit-events-title">Sequential review events</h2><p className="panel-description">Newest action first. Each row links back to its candidate evidence.</p></div><span className="count-badge">Page {result.page} of {lastPage}</span></div>
      <div className="table-wrap audit-table-wrap"><table className="source-table audit-table"><caption className="sr-only">Append-only candidate review events</caption><thead><tr><th scope="col">Recorded</th><th scope="col">Transition</th><th scope="col">Candidate and work</th><th scope="col">Reviewer</th><th scope="col">Decision</th><th scope="col">Action</th></tr></thead><tbody>{result.items.map((event) => <tr key={event.event_id}><td><time dateTime={event.created_at}>{dateTime.format(new Date(event.created_at))}</time></td><td><span className={`status-chip status-${event.to_status.toLowerCase()}`}>{statusLabel(event.to_status)}</span><p className="cell-note">From {statusLabel(event.from_status)}</p></td><td><strong>{event.work_description || "Description not supplied"}</strong><p className="cell-note">{event.result_id}</p></td><td>{event.reviewer}</td><td>{event.decision?.replaceAll("_", " ").toLowerCase() ?? "No final decision"}{event.reason_code && <p className="cell-note">{event.reason_code.replaceAll("_", " ").toLowerCase()}</p>}</td><td><Link className="row-action" href={`/investigation-queue/${event.result_id}`}>Inspect evidence</Link></td></tr>)}</tbody></table></div>
      <div className="audit-cards">{result.items.map((event) => <article className="candidate-card audit-card" key={`card-${event.event_id}`}><div className="review-row"><span className={`status-chip status-${event.to_status.toLowerCase()}`}>{statusLabel(event.to_status)}</span><time dateTime={event.created_at}>{dateTime.format(new Date(event.created_at))}</time></div><h3>{event.work_description || "Description not supplied"}</h3><p className="cell-note">Candidate {event.result_id}</p><p>Reviewer: {event.reviewer}</p><p className="cell-note">From {statusLabel(event.from_status)}. {event.decision ? `Decision: ${event.decision.replaceAll("_", " ").toLowerCase()}.` : "No final decision recorded."}</p><Link className="row-action" href={`/investigation-queue/${event.result_id}`}>Inspect evidence</Link></article>)}</div>
    </section>}
    <nav className="pagination" aria-label="Audit event pages"><Link className={page <= 1 ? "disabled-link" : "secondary-link"} aria-disabled={page <= 1} tabIndex={page <= 1 ? -1 : undefined} href={page <= 1 ? "#" : pageHref(page - 1)}>Previous</Link><span>Showing {result.total ? (page - 1) * result.page_size + 1 : 0} to {Math.min(page * result.page_size, result.total)} of {integer.format(result.total)}</span><Link className={page >= lastPage ? "disabled-link" : "secondary-link"} aria-disabled={page >= lastPage} tabIndex={page >= lastPage ? -1 : undefined} href={page >= lastPage ? "#" : pageHref(page + 1)}>Next</Link></nav>
  </main></QueueShell>;
}
