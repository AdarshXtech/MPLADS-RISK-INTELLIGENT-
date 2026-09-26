import type { DataOverview, SourceReport } from "@/lib/data-overview";

export const integer = new Intl.NumberFormat("en-IN");

export function Metric({ label, value, note }: { label: string; value: number; note: string }) {
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

export function DataQualityContent({ data }: { data: DataOverview }) {
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
            <span className="count-badge">
              {integer.format(data.source_batches)} {data.source_batches === 1 ? "source" : "sources"}
            </span>
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
