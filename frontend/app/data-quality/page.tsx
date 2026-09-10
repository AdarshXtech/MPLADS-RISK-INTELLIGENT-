import type { Metadata } from "next";
import Link from "next/link";
import { requireReviewer } from "@/lib/auth";
import { getDataOverview } from "@/lib/data-overview";
import { QueueShell } from "../investigation-queue/shell";
import { DataQualityContent } from "./data-quality-content";

export const metadata: Metadata = { title: "Data Quality" };

export default async function DataQualityPage() {
  const username = await requireReviewer();
  const result = await getDataOverview();
  const connected = result.status === "ready";

  return (
    <QueueShell username={username} active="data-quality" connected={connected}>
      <main className="page-content" id="main-content" tabIndex={-1}>
        <div className="page-heading-row">
          <div>
            <p className="eyebrow">Source validation</p>
            <h1>Data Quality</h1>
            <p className="page-intro">Review ingestion coverage, validation issues and the evidence limits that affect analysis.</p>
          </div>
          <p className="view-label">Source-backed evidence view</p>
        </div>

        {result.status === "error" ? (
          <section className="error-panel" role="alert" aria-labelledby="service-error-title">
            <h2 id="service-error-title">Data service unavailable</h2>
            <p>The page could not read the verified ingestion summary. Confirm that FastAPI and PostgreSQL are running, then retry.</p>
            <Link className="retry-link" href="/data-quality?retry=1">Retry connection</Link>
          </section>
        ) : (
          <DataQualityContent data={result.data} />
        )}
      </main>
    </QueueShell>
  );
}
