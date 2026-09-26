import type { Metadata } from "next";
import Link from "next/link";
import { requireReviewer } from "@/lib/auth";
import { getDataOverview, type DataOverview } from "@/lib/data-overview";
import {
  getInvestigationSummary,
  type InvestigationSummary,
} from "@/lib/investigations";
import { DataQualityContent, integer, Metric } from "../data-quality/data-quality-content";
import { QueueShell } from "../investigation-queue/shell";

export const metadata: Metadata = { title: "Command Centre" };

type OverviewResult =
  | { status: "ready"; data: DataOverview; summary: InvestigationSummary }
  | { status: "error" };

async function getOverview(): Promise<OverviewResult> {
  try {
    const [overview, summary] = await Promise.all([
      getDataOverview(),
      getInvestigationSummary(),
    ]);
    return overview.status === "ready"
      ? { status: "ready", data: overview.data, summary }
      : { status: "error" };
  } catch {
    return { status: "error" };
  }
}

function Dashboard({ data, summary }: { data: DataOverview; summary: InvestigationSummary }) {
  if (data.sources.length === 0) return <DataQualityContent data={data} />;

  return (
    <>
      <section className="panel workload-panel" aria-labelledby="workload-title">
        <div className="panel-header">
          <div>
            <h2 className="panel-title" id="workload-title">Investigation workload</h2>
            <p className="panel-description">Current state of the latest reviewable detector run. Counts are not findings of duplication or misuse.</p>
          </div>
          <Link className="row-action" href="/investigation-queue">Open Investigation Queue</Link>
        </div>
        <section className="metrics workload-metrics" aria-label="Investigation review status">
          <Metric label="Candidate groups" value={summary.total_candidates} note="Require verification" />
          <Metric label="Not reviewed" value={summary.new} note="No review event recorded" />
          <Metric label="Under review" value={summary.under_review} note="Review has started" />
          <Metric label="Verification requested" value={summary.verification_requested} note="Awaiting or checking evidence" />
          <Metric label="Closed" value={summary.resolved + summary.dismissed} note={`${integer.format(summary.resolved)} resolved, ${integer.format(summary.dismissed)} dismissed`} />
        </section>
      </section>
      <DataQualityContent data={data} />
    </>
  );
}

export default async function CommandCentrePage() {
  const username = await requireReviewer();
  const result = await getOverview();
  const connected = result.status === "ready";

  return (
    <QueueShell username={username} active="command-centre" connected={connected}>
      <main className="page-content" id="main-content" tabIndex={-1}>
        <div className="page-heading-row">
          <div>
            <p className="eyebrow">Data readiness</p>
            <h1>Risk Command Centre</h1>
            <p className="page-intro">Verified ingestion status for the MPLADS reports currently available to this project.</p>
          </div>
          <p className="view-label">Source-backed evidence view</p>
        </div>
        <section className="scope-strip" aria-label="Operational scope and analysis status">
          <div><span>Data scope</span><strong>Supplied MPLADS exports</strong></div>
          <div><span>Report coverage</span><strong>Unverified</strong></div>
          <div><span>Risk analysis</span><strong>Potential duplicate screening only</strong></div>
        </section>
        <aside className="notice" aria-labelledby="risk-notice-title">
          <span className="notice-mark" aria-hidden="true">i</span>
          <div>
            <strong id="risk-notice-title">Risk coverage is intentionally limited</strong>
            <p>The active deterministic detector identifies potential duplicate groups for verification. No composite score exists, and data-quality issues do not indicate fraud or misuse.</p>
          </div>
        </aside>

        {result.status === "error" ? (
          <section className="error-panel" role="alert" aria-labelledby="service-error-title">
            <h2 id="service-error-title">Data service unavailable</h2>
            <p>The command centre could not read the verified ingestion summary. Confirm that FastAPI and PostgreSQL are running, then retry.</p>
            <Link className="retry-link" href="/command-centre?retry=1">Retry connection</Link>
          </section>
        ) : (
          <Dashboard data={result.data} summary={result.summary} />
        )}
      </main>
    </QueueShell>
  );
}
