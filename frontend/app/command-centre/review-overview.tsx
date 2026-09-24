import Link from "next/link";
import { ArrowUpRight, ChartNoAxesColumn, ClipboardCheck } from "lucide-react";
import type { InvestigationSummary } from "@/lib/investigations";

const integer = new Intl.NumberFormat("en-IN");

export function ReviewOverview({ summary }: { summary: InvestigationSummary }) {
  const statuses = [
    { label: "New", count: summary.new, style: "new" },
    { label: "Under review", count: summary.under_review, style: "under_review" },
    { label: "Verification requested", count: summary.verification_requested, style: "verification_requested" },
    { label: "Resolved", count: summary.resolved, style: "resolved" },
    { label: "Dismissed", count: summary.dismissed, style: "dismissed" },
  ];
  const links = [
    { label: "Review new candidates", count: summary.new, status: "NEW", note: "No review action recorded" },
    { label: "Continue active reviews", count: summary.under_review, status: "UNDER_REVIEW", note: "Evidence assessment in progress" },
    { label: "Check requested verification", count: summary.verification_requested, status: "VERIFICATION_REQUESTED", note: "Supporting evidence requested" },
  ];
  const closed = summary.resolved + summary.dismissed;
  return <div className="review-overview">
    <section className="panel" aria-labelledby="review-distribution-title">
      <div className="panel-header"><div><h2 className="panel-title icon-heading" id="review-distribution-title"><ChartNoAxesColumn size={18} aria-hidden="true" />Review progress</h2><p className="panel-description">Recorded review states in the latest available screening run.</p></div><span className="count-badge">{integer.format(summary.total_candidates)} candidates</span></div>
      <div className="review-distribution">{statuses.map((status) => <div className="distribution-row" key={status.label}><div><span>{status.label}</span><strong>{integer.format(status.count)}</strong></div><div className="distribution-track" role="meter" aria-label={status.label} aria-valuemin={0} aria-valuemax={Math.max(1, summary.total_candidates)} aria-valuenow={status.count} aria-valuetext={`${status.count} of ${summary.total_candidates} candidates`}><span className={`distribution-${status.style}`} style={{ width: `${summary.total_candidates ? status.count / summary.total_candidates * 100 : 0}%` }} /></div></div>)}</div>
      <p className="review-completion">{summary.total_candidates ? `${(closed / summary.total_candidates * 100).toFixed(1)}% closed` : "No candidates available"}<span>{integer.format(closed)} resolved or dismissed</span></p>
    </section>
    <section className="panel" aria-labelledby="verification-workload-title">
      <div className="panel-header"><div><h2 className="panel-title icon-heading" id="verification-workload-title"><ClipboardCheck size={18} aria-hidden="true" />Verification workload</h2><p className="panel-description">Candidate groups awaiting administrative action.</p></div></div>
      <ul className="workload-actions">{links.map((link) => <li key={link.status}><div><Link href={`/investigation-queue?status=${link.status}`} className="row-action">{link.label}<ArrowUpRight size={16} aria-hidden="true" /></Link><p>{link.note}</p></div><strong>{integer.format(link.count)}</strong></li>)}</ul>
      <p className="review-completion">Review decisions remain linked to source evidence.</p>
    </section>
  </div>;
}
