import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { requireReviewer } from "@/lib/auth";
import { getInvestigationSummary, type InvestigationSummary } from "@/lib/investigations";
import { QueueShell } from "../investigation-queue/shell";

export const metadata: Metadata = { title: "Command Centre" };

type SourceReport = {
  source_file: string;
  source_sha256: string;
  parser_version: string;
  retained_records: number;
  detail_records: number;
  summary_records: number;
  rejected_records: number;
  records_with_validation_issues: number;
};

type DataOverview = {
  source_batches: number;
  retained_records: number;
  detail_records: number;
  summary_records: number;
  rejected_records: number;
  records_with_validation_issues: number;
  sources: SourceReport[];
};

type OverviewResult =
  | { status: "ready"; data: DataOverview; summary: InvestigationSummary }
  | { status: "error" };

const integer = new Intl.NumberFormat("en-IN");

function isOverview(value: unknown): value is DataOverview {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<DataOverview>;
  return (
    typeof candidate.source_batches === "number" &&
    typeof candidate.retained_records === "number" &&
    typeof candidate.detail_records === "number" &&
    typeof candidate.summary_records === "number" &&
    typeof candidate.rejected_records === "number" &&
    typeof candidate.records_with_validation_issues === "number" &&
    Array.isArray(candidate.sources) &&
    candidate.sources.every(
      (source) =>
        typeof source.source_file === "string" &&
        typeof source.source_sha256 === "string" &&
        typeof source.parser_version === "string" &&
        typeof source.retained_records === "number" &&
        typeof source.detail_records === "number" &&
        typeof source.summary_records === "number" &&
        typeof source.rejected_records === "number" &&
        typeof source.records_with_validation_issues === "number",
    )
  );
}

async function getOverview(): Promise<OverviewResult> {
  await connection();
  const baseUrl = process.env.MPLADS_API_BASE_URL ?? "http://127.0.0.1:8000";
  try {
    const [response, summary] = await Promise.all([
      fetch(`${baseUrl}/data-overview`, {
        cache: "no-store",
        signal: AbortSignal.timeout(5000),
      }),
      getInvestigationSummary(),
    ]);
    if (!response.ok) return { status: "error" };
    const data: unknown = await response.json();
    return isOverview(data) ? { status: "ready", data, summary } : { status: "error" };
  } catch {
    return { status: "error" };
  }
}

function Metric({ label, value, note }: { label: string; value: number; note: string }) {
  return (
    <article className="metric">
      <p className="metric-label">{label}</p>
      <p className="metric-value">{integer.format(value)}</p>
      <p className="metric-note">{note}</p>
    </article>
  );
}

function SourceRows({ sources }: { sources: SourceReport[] }) {
  return (
    <>
      <div className="table-wrap">
        <table className="source-table">
          <caption className="sr-only">Ingested MPLADS source report summary</caption>
          <thead>
            <tr>
              <th scope="col">Source report</th>
              <th scope="col">Detail</th>
              <th scope="col">Summary</th>
              <th scope="col">Rejected</th>
              <th scope="col">Needs data review</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={`${source.source_sha256}-${source.parser_version}`}>
                <td>
                  <div className="source-name">{source.source_file}</div>
                  <div className="provenance">
                    SHA-256 {source.source_sha256.slice(0, 12)}... · parser v{source.parser_version}
                  </div>
                </td>
                <td className="number-cell">{integer.format(source.detail_records)}</td>
                <td className="number-cell">{integer.format(source.summary_records)}</td>
                <td className="number-cell">{integer.format(source.rejected_records)}</td>
                <td className="number-cell review-count">
                  {integer.format(source.records_with_validation_issues)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="source-cards" aria-label="Ingested source reports">
        {sources.map((source) => (
          <article className="source-card" key={`card-${source.source_sha256}-${source.parser_version}`}>
            <h3>{source.source_file}</h3>
            <p className="provenance">
              SHA-256 {source.source_sha256.slice(0, 12)}... · parser v{source.parser_version}
            </p>
            <dl>
              <dt>Detail records</dt><dd>{integer.format(source.detail_records)}</dd>
              <dt>Summary records</dt><dd>{integer.format(source.summary_records)}</dd>
              <dt>Rejected records</dt><dd>{integer.format(source.rejected_records)}</dd>
              <dt>Needs data review</dt>
              <dd className="review-count">{integer.format(source.records_with_validation_issues)}</dd>
            </dl>
          </article>
        ))}
      </div>
    </>
  );
}

function Dashboard({ data, summary }: { data: DataOverview; summary: InvestigationSummary }) {
  if (data.sources.length === 0) {
    return (
      <section className="empty-panel" aria-labelledby="empty-title">
        <h2 id="empty-title">No staged source reports</h2>
        <p>The data service is connected, but no source batches are available for review.</p>
      </section>
    );
  }

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

      <section className="metrics" aria-label="Ingestion summary">
        <Metric label="Retained records" value={data.retained_records} note="Across all staged sources" />
        <Metric label="Detail records" value={data.detail_records} note="Available for validated analysis" />
        <Metric label="Needs data review" value={data.records_with_validation_issues} note="Not risk flags" />
        <Metric label="Summary records" value={data.summary_records} note="Retained separately" />
        <Metric label="Rejected records" value={data.rejected_records} note="Preserved when present" />
      </section>

      <div className="analysis-grid">
        <section className="panel" id="data-quality" aria-labelledby="sources-title">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="sources-title">Ingested source reports</h2>
              <p className="panel-description">Counts are read live from PostgreSQL. Original source values remain separate from cleaned and derived values.</p>
            </div>
            <span className="count-badge">{integer.format(data.source_batches)} sources</span>
          </div>
          <SourceRows sources={data.sources} />
        </section>

        <aside className="analysis-rail" aria-label="Data readiness analysis">
          <section className="panel rail-panel" aria-labelledby="review-title">
            <div className="panel-header">
              <div>
                <h2 className="panel-title" id="review-title">Validation review by source</h2>
                <p className="panel-description">Share of detail records with one or more reported validation issues.</p>
              </div>
            </div>
            <ol className="review-list">
              {data.sources.map((source) => {
                const rate = source.detail_records
                  ? (source.records_with_validation_issues / source.detail_records) * 100
                  : 0;
                return (
                  <li key={`review-${source.source_sha256}`}>
                    <div className="review-row">
                      <span>{source.source_file.replace(".csv", "")}</span>
                      <strong>{integer.format(source.records_with_validation_issues)}</strong>
                    </div>
                    <div className="review-track" aria-label={`${rate.toFixed(1)} per cent of detail records require data review`}>
                      <span style={{ width: `${Math.min(rate, 100)}%` }} />
                    </div>
                    <p>{rate.toFixed(1)}% of detail records</p>
                  </li>
                );
              })}
            </ol>
          </section>

          <section className="panel rail-panel" aria-labelledby="pipeline-title">
            <div className="panel-header">
              <div>
                <h2 className="panel-title" id="pipeline-title">Pipeline status</h2>
                <p className="panel-description">Current implementation state, not a risk assessment.</p>
              </div>
            </div>
            <dl className="status-list">
              <div><dt>Raw source preservation</dt><dd className="status-ok">Verified</dd></div>
              <div><dt>PostgreSQL staging</dt><dd className="status-ok">Operational</dd></div>
              <div><dt>Potential duplicate detector</dt><dd className="status-ok">Operational</dd></div>
              <div><dt>Investigation Queue</dt><dd className="status-ok">Operational</dd></div>
            </dl>
          </section>
        </aside>
      </div>

      <section className="panel" aria-labelledby="limits-title">
        <div className="panel-header">
          <div>
            <h2 className="panel-title" id="limits-title">Current evidence boundaries</h2>
            <p className="panel-description">These limits prevent unsupported risk conclusions.</p>
          </div>
        </div>
        <div className="limits">
          <div className="limit-item">
            <strong>Coverage is unverified</strong>
            <p>Portal filters, extraction freshness and national completeness were not supplied.</p>
          </div>
          <div className="limit-item">
            <strong>Formats differ</strong>
            <p>CSV and workbook row counts differ for expenditure and completed-work reports.</p>
          </div>
          <div className="limit-item">
            <strong>Detector coverage is limited</strong>
            <p>Only exact-field potential duplicate screening is active. Other proposed detectors remain unavailable or disabled.</p>
          </div>
        </div>
      </section>
    </>
  );
}

export default async function CommandCentrePage() {
  const username = await requireReviewer();
  const result = await getOverview();
  const connected = result.status === "ready";

  return (
    <QueueShell username={username} active="command-centre" connected={connected}>
          <main className="page-content" id="main-content">
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
                <Link className="retry-link" href="/command-centre">Retry connection</Link>
              </section>
            ) : (
              <Dashboard data={result.data} summary={result.summary} />
            )}
          </main>
    </QueueShell>
  );
}
