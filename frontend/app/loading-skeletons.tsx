import type { CSSProperties } from "react";

function SkeletonLine({ className = "" }: { className?: string }) {
  return <span className={`skeleton skeleton-line ${className}`} />;
}

function SkeletonPanel({ lines = 3, className = "" }: { lines?: number; className?: string }) {
  return (
    <section className={`panel skeleton-panel ${className}`}>
      <div className="panel-header">
        <div>
          <SkeletonLine className="skeleton-kicker" />
          <SkeletonLine className="skeleton-title" />
        </div>
        <SkeletonLine className="skeleton-chip" />
      </div>
      <div className="panel-body">
        {Array.from({ length: lines }, (_, index) => <SkeletonLine key={index} />)}
      </div>
    </section>
  );
}

function SkeletonTable({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  const style: CSSProperties & Record<"--skeleton-columns", number> = { "--skeleton-columns": columns };
  return (
    <div className="table-wrap skeleton-table-wrap">
      <div className="skeleton-table" aria-hidden="true" style={style}>
        <div className="skeleton-table-row skeleton-table-head">
          {Array.from({ length: columns }, (_, index) => <SkeletonLine key={index} />)}
        </div>
        {Array.from({ length: rows }, (_, row) => (
          <div className="skeleton-table-row" key={row}>
            {Array.from({ length: columns }, (_, column) => <SkeletonLine key={column} />)}
          </div>
        ))}
      </div>
    </div>
  );
}

function PageStart({ label, title }: { label: string; title: string }) {
  return (
    <div className="page-heading-row skeleton-heading-row">
      <div>
        <SkeletonLine className="skeleton-kicker" />
        <h1 className="sr-only">{title}</h1>
        <div className="skeleton skeleton-heading" />
        <div className="skeleton skeleton-copy" />
      </div>
      <span className="view-label skeleton-view-label">{label}</span>
    </div>
  );
}

function ScopeStripSkeleton() {
  return (
    <div className="scope-strip skeleton-scope" aria-hidden="true">
      {[0, 1, 2].map((item) => (
        <div key={item}>
          <SkeletonLine className="skeleton-kicker" />
          <SkeletonLine />
        </div>
      ))}
    </div>
  );
}

function NoticeSkeleton() {
  return (
    <aside className="notice skeleton-notice" aria-hidden="true">
      <span className="notice-mark">i</span>
      <div>
        <SkeletonLine className="skeleton-title" />
        <SkeletonLine />
      </div>
    </aside>
  );
}

export function CommandCentreSkeleton({ label }: { label: string }) {
  return (
    <main className="page-content" id="main-content" aria-busy="true" aria-label={label}>
      <PageStart label="Source-backed evidence view" title={label} />
      <ScopeStripSkeleton />
      <NoticeSkeleton />
      <section className="metrics" aria-hidden="true">
        {Array.from({ length: 5 }, (_, item) => (
          <article className="metric skeleton-metric" key={item}>
            <SkeletonLine className="skeleton-kicker" />
            <SkeletonLine className="skeleton-number" />
            <SkeletonLine />
          </article>
        ))}
      </section>
      <div className="review-overview command-analysis">
        <SkeletonPanel lines={2} className="workload-panel" />
        <SkeletonPanel lines={4} className="analysis-rail" />
      </div>
      <section className="panel" aria-hidden="true">
        <div className="panel-header">
          <div>
            <SkeletonLine className="skeleton-title" />
            <SkeletonLine />
          </div>
          <SkeletonLine className="skeleton-chip" />
        </div>
        <SkeletonTable rows={6} columns={5} />
      </section>
      <span className="sr-only">Loading current service data</span>
    </main>
  );
}

export function DataQualitySkeleton() {
  return (
    <main className="page-content" id="main-content" aria-busy="true" aria-label="Loading Data Quality">
      <PageStart label="Source quality checks" title="Loading Data Quality" />
      <ScopeStripSkeleton />
      <div className="review-overview command-analysis">
        <section className="panel" id="data-quality" aria-hidden="true">
          <div className="panel-header">
            <div>
              <SkeletonLine className="skeleton-title" />
              <SkeletonLine />
            </div>
            <SkeletonLine className="skeleton-chip" />
          </div>
          <SkeletonTable rows={6} columns={5} />
        </section>
        <SkeletonPanel lines={6} className="analysis-rail" />
      </div>
      <span className="sr-only">Loading current data-quality information</span>
    </main>
  );
}

export function QueueSkeleton() {
  return (
    <main className="page-content" id="main-content" aria-busy="true" aria-label="Loading Investigation Queue">
      <PageStart label="Review candidates" title="Loading Investigation Queue" />
      <NoticeSkeleton />
      <div className="filter-bar skeleton-filter" aria-hidden="true">
        <SkeletonLine className="filter-heading" />
        {Array.from({ length: 6 }, (_, item) => (
          <div key={item}>
            <SkeletonLine className="skeleton-kicker" />
            <SkeletonLine className="skeleton-input" />
          </div>
        ))}
        <SkeletonLine className="skeleton-button" />
        <SkeletonLine className="skeleton-button" />
      </div>
      <section className="panel" aria-hidden="true">
        <div className="panel-header">
          <div>
            <SkeletonLine className="skeleton-title" />
            <SkeletonLine />
          </div>
          <SkeletonLine className="skeleton-chip" />
        </div>
        <SkeletonTable rows={7} columns={6} />
        <div className="candidate-cards skeleton-card-list">
          {Array.from({ length: 4 }, (_, item) => <SkeletonPanel key={item} lines={3} />)}
        </div>
      </section>
      <span className="sr-only">Loading candidates requiring review</span>
    </main>
  );
}

export function CandidateSkeleton() {
  return (
    <main className="page-content" id="main-content" aria-busy="true" aria-label="Loading candidate evidence">
      <SkeletonLine className="skeleton-back-link" />
      <PageStart label="Review status" title="Loading candidate evidence" />
      <div className="case-summary skeleton-case-summary" aria-hidden="true">
        {Array.from({ length: 4 }, (_, item) => (
          <div key={item}>
            <SkeletonLine className="skeleton-kicker" />
            <SkeletonLine className="skeleton-number" />
            <SkeletonLine />
          </div>
        ))}
      </div>
      <div className="case-layout">
        <div className="case-evidence">
          <SkeletonPanel lines={5} />
          <section className="evidence-grid">
            <SkeletonPanel lines={4} />
            <SkeletonPanel lines={4} />
          </section>
          <SkeletonPanel lines={6} />
          <SkeletonPanel lines={5} />
        </div>
        <aside className="case-review" aria-hidden="true">
          <SkeletonPanel lines={7} />
          <SkeletonPanel lines={3} />
        </aside>
      </div>
      <span className="sr-only">Loading candidate evidence and review form</span>
    </main>
  );
}

export function AuditTrailSkeleton() {
  return (
    <main className="page-content" id="main-content" aria-busy="true" aria-label="Loading Review Audit Trail">
      <PageStart label="Recorded actions" title="Loading Review Audit Trail" />
      <NoticeSkeleton />
      <div className="filter-bar audit-filter-bar skeleton-filter" aria-hidden="true">
        <SkeletonLine className="filter-heading" />
        <div>
          <SkeletonLine className="skeleton-kicker" />
          <SkeletonLine className="skeleton-input" />
        </div>
        <div>
          <SkeletonLine className="skeleton-kicker" />
          <SkeletonLine className="skeleton-input" />
        </div>
        <SkeletonLine className="skeleton-button" />
        <SkeletonLine className="skeleton-button" />
      </div>
      <section className="panel" aria-hidden="true">
        <div className="panel-header">
          <div>
            <SkeletonLine className="skeleton-title" />
            <SkeletonLine />
          </div>
          <SkeletonLine className="skeleton-chip" />
        </div>
        <SkeletonTable rows={7} columns={6} />
      </section>
      <span className="sr-only">Loading recorded review events</span>
    </main>
  );
}
