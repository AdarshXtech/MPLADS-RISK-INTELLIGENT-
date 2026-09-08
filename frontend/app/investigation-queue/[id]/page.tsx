import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { requireReviewer } from "@/lib/auth";
import { getCandidate, type Status } from "@/lib/investigations";
import { updateCandidate } from "../actions";
import { QueueShell } from "../shell";

export const metadata: Metadata = { title: "Candidate evidence" };
const statusLabel = (status: Status) => status.toLowerCase().replaceAll("_", " ");
const transitions: Record<Status, Array<[Status, string]>> = {
  NEW: [["UNDER_REVIEW", "Start review"]],
  UNDER_REVIEW: [["VERIFICATION_REQUESTED", "Request verification"], ["RESOLVED", "Resolve"], ["DISMISSED", "Dismiss"]],
  VERIFICATION_REQUESTED: [["UNDER_REVIEW", "Resume review"], ["RESOLVED", "Resolve"], ["DISMISSED", "Dismiss"]],
  RESOLVED: [["UNDER_REVIEW", "Reopen review"]],
  DISMISSED: [["UNDER_REVIEW", "Reopen review"]],
};

export default async function CandidatePage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ saved?: string; error?: string }> }) {
  const username = await requireReviewer();
  const { id } = await params;
  const message = await searchParams;
  let item;
  try { item = await getCandidate(id); } catch (error) {
    if (error instanceof Error && error.message === "Investigation candidate not found") notFound();
    return <QueueShell username={username}><main className="page-content" id="main-content" tabIndex={-1}><section className="error-panel" role="alert"><h1>Candidate unavailable</h1><p>The review service could not load this evidence. Return to the queue and try again.</p><Link className="retry-link" href="/investigation-queue">Return to queue</Link></section></main></QueueShell>;
  }
  const action = updateCandidate.bind(null, item.result_id);
  const matched = item.evidence.matched_values as Record<string, unknown> | undefined;
  return <QueueShell username={username}><main className="page-content" id="main-content" tabIndex={-1}>
    <Link className="back-link" href="/investigation-queue">Back to Investigation Queue</Link>
    <div className="page-heading-row"><div><p className="eyebrow">Candidate evidence</p><h1>{item.detector_name}</h1><p className="page-intro">Candidate {item.result_id.slice(0, 12)} · {item.group_size} source records</p></div><span className={`status-chip status-${item.status.toLowerCase()}`}>{statusLabel(item.status)}</span></div>
    {message.saved && <p className="success-message" role="status">Review action saved to the audit history.</p>}
    {message.error && <p className="form-error" role="alert">{message.error}</p>}
    <section className="evidence-grid">
      <article className="panel detail-panel"><div className="panel-header"><div><h2 className="panel-title">Why this was flagged</h2><p className="panel-description">Deterministic detector evidence, unchanged by reviewer actions.</p></div></div><div className="panel-body"><p>{item.explanation}</p><dl className="evidence-list"><div><dt>Detector ID</dt><dd>{item.detector_id}</dd></div><div><dt>Severity</dt><dd>{item.severity}</dd></div><div><dt>Match confidence</dt><dd>{Math.round(item.confidence * 100)}%</dd></div><div><dt>Fields used</dt><dd>{item.fields_used.join(", ")}</dd></div></dl></div></article>
      <article className="panel detail-panel"><div className="panel-header"><div><h2 className="panel-title">What to verify next</h2><p className="panel-description">Administrative recommendation, not an accusation.</p></div></div><div className="panel-body"><p>{item.verification_step}</p><h3>Known limitations</h3><ul>{item.limitations.map((limit) => <li key={limit}>{limit}</li>)}</ul></div></article>
    </section>
    <section className="panel"><div className="panel-header"><div><h2 className="panel-title">Matched values</h2><p className="panel-description">The fields that matched after normalisation.</p></div></div><dl className="matched-grid">{Object.entries(matched ?? {}).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{String(value ?? "Not supplied")}</dd></div>)}</dl></section>
    <section className="panel"><div className="panel-header"><div><h2 className="panel-title">Source record provenance</h2><p className="panel-description">Cleaned display values linked to immutable source coordinates.</p></div></div><div className="source-cards always-cards">{item.source_records.map((source) => <article className="source-card" key={`${source.source_sha256}-${source.record_number}`}><h3>{source.work_id}</h3><p>{String(source.cleaned_values["Work description"] ?? "Description not supplied")}</p><dl><dt>Source record</dt><dd>{source.record_number}</dd><dt>Parser</dt><dd>v{source.parser_version}</dd><dt>SHA-256</dt><dd title={source.source_sha256}>{source.source_sha256.slice(0, 12)}...</dd><dt>Validation issues</dt><dd>{source.validation_issues.length}</dd></dl></article>)}</div></section>
    <section className="panel"><div className="panel-header"><div><h2 className="panel-title">Record review action</h2><p className="panel-description">Each save creates a new audit event. Earlier entries cannot be overwritten.</p></div></div><form className="review-form" action={action}>
      <input type="hidden" name="expected_status" value={item.status} />
      <label htmlFor="target_status">Next status</label><select id="target_status" name="target_status" required>{transitions[item.status].map(([value, text]) => <option value={value} key={value}>{text}</option>)}</select>
      <label htmlFor="decision">Decision, required when resolving or dismissing</label><select id="decision" name="decision"><option value="">No final decision</option><option value="SEPARATE_WORKS">Separate works</option><option value="POTENTIAL_DUPLICATE">Potential duplicate</option><option value="INSUFFICIENT_EVIDENCE">Insufficient evidence</option><option value="DATA_ERROR">Data error</option></select>
      <label htmlFor="reason_code">Reason code, required when dismissing</label><select id="reason_code" name="reason_code"><option value="">Select when applicable</option><option value="DIFFERENT_LOCATION">Different location</option><option value="DIFFERENT_ASSET">Different asset</option><option value="DIFFERENT_PHASE_OR_QUANTITY">Different phase or quantity</option><option value="SAME_ASSET_AND_SCOPE">Same asset and scope</option><option value="SOURCE_RECORD_ERROR">Source record error</option><option value="DOCUMENTS_UNAVAILABLE">Documents unavailable</option><option value="OTHER">Other</option></select>
      <label htmlFor="documents_checked">Documents checked</label><textarea id="documents_checked" name="documents_checked" rows={3} maxLength={4000} />
      <label htmlFor="evidence_references">Evidence references</label><textarea id="evidence_references" name="evidence_references" rows={3} maxLength={4000} />
      <label htmlFor="notes">Reviewer notes</label><textarea id="notes" name="notes" rows={4} maxLength={4000} />
      <button type="submit">Save review action</button>
    </form></section>
    <section className="panel"><div className="panel-header"><div><h2 className="panel-title">Review history</h2><p className="panel-description">Newest action first.</p></div></div>{item.history.length === 0 ? <div className="panel-body"><p>No review actions have been recorded.</p></div> : <ol className="history-list">{item.history.map((event, index) => <li key={`${event.created_at}-${index}`}><strong>{statusLabel(event.from_status)} to {statusLabel(event.to_status)}</strong><p>{new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Kolkata" }).format(new Date(event.created_at))} by {event.reviewer}</p>{event.decision && <p>Decision: {event.decision.toLowerCase().replaceAll("_", " ")}</p>}{event.notes && <p>Notes: {event.notes}</p>}</li>)}</ol>}</section>
  </main></QueueShell>;
}
