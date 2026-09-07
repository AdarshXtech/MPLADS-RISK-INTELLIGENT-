import type { Metadata } from "next";
import Link from "next/link";
import { requireReviewer } from "@/lib/auth";
import { getCandidates, type Sort, type Status } from "@/lib/investigations";
import { QueueShell } from "./shell";
import { ExportButton } from "./export-button";

export const metadata: Metadata = { title: "Investigation Queue" };
const integer = new Intl.NumberFormat("en-IN");
const statuses: Array<{ value: Status | ""; label: string }> = [
  { value: "", label: "All statuses" }, { value: "NEW", label: "New" },
  { value: "UNDER_REVIEW", label: "Under review" },
  { value: "VERIFICATION_REQUESTED", label: "Verification requested" },
  { value: "RESOLVED", label: "Resolved" }, { value: "DISMISSED", label: "Dismissed" },
];
const label = (status: Status) => status.toLowerCase().replaceAll("_", " ");
const sorts: Array<{ value: Sort; label: string }> = [
  { value: "group_smallest", label: "Smallest groups first" },
  { value: "group_largest", label: "Largest groups first" },
  { value: "state", label: "State A to Z" },
  { value: "recently_reviewed", label: "Most recently reviewed" },
];

type Params = { page?: string; query?: string; state?: string; status?: string; sort?: string };
const isSort = (value: string | undefined): value is Sort => sorts.some((sort) => sort.value === value);

export default async function InvestigationQueuePage({ searchParams }: { searchParams: Promise<Params> }) {
  const username = await requireReviewer();
  const supplied = await searchParams;
  const selectedSort: Sort = isSort(supplied.sort) ? supplied.sort : "group_smallest";
  const page = Math.max(1, Number.parseInt(supplied.page ?? "1", 10) || 1);
  const parameters = new URLSearchParams({ page: String(page), page_size: "20" });
  for (const key of ["query", "state", "status"] as const) if (supplied[key]) parameters.set(key, supplied[key]);
  parameters.set("sort", selectedSort);
  let result;
  try {
    result = await getCandidates(parameters);
  } catch {
    return <QueueShell username={username}><main className="page-content" id="main-content"><section className="error-panel" role="alert"><h1>Investigation Queue unavailable</h1><p>The review service could not load candidates. Confirm that FastAPI, PostgreSQL and the review service key are configured.</p><Link className="retry-link" href="/investigation-queue">Retry</Link></section></main></QueueShell>;
  }
  const preserved = new URLSearchParams();
  for (const key of ["query", "state", "status"] as const) if (supplied[key]) preserved.set(key, supplied[key]);
  preserved.set("sort", selectedSort);
  const pageHref = (next: number) => { const nextParams = new URLSearchParams(preserved); nextParams.set("page", String(next)); return `?${nextParams}`; };
  const lastPage = Math.max(1, Math.ceil(result.total / result.page_size));
  return <QueueShell username={username}>
    <main className="page-content" id="main-content">
      <div className="page-heading-row"><div><p className="eyebrow">Administrative triage</p><h1>Investigation Queue</h1><p className="page-intro">Potential duplicate work groups produced by deterministic matching. Each candidate requires verification.</p></div><p className="view-label">{integer.format(result.total)} candidates</p></div>
      <aside className="notice" aria-label="Interpretation notice"><span className="notice-mark" aria-hidden="true">i</span><div><strong>Screening result, not a finding</strong><p>Confidence confirms that configured fields matched. It does not estimate the probability of misuse or fraud.</p></div></aside>
      <form className="filter-bar" method="get" role="search">
        <div><label htmlFor="query">Search evidence</label><input id="query" name="query" defaultValue={supplied.query} placeholder="Work ID, description, constituency or agency" /></div>
        <div><label htmlFor="state">State</label><select id="state" name="state" defaultValue={supplied.state ?? ""}><option value="">All states</option>{result.states.map((state) => <option key={state}>{state}</option>)}</select></div>
        <div><label htmlFor="status">Review status</label><select id="status" name="status" defaultValue={supplied.status ?? ""}>{statuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}</select></div>
        <div><label htmlFor="sort">Order by</label><select id="sort" name="sort" defaultValue={selectedSort}>{sorts.map((sort) => <option key={sort.value} value={sort.value}>{sort.label}</option>)}</select></div>
        <button type="submit">Apply filters</button>
        <Link className="secondary-link" href="/investigation-queue">Clear</Link>
      </form>
      <ExportButton key={preserved.toString()} filters={preserved.toString()} />
      {result.items.length === 0 ? <section className="empty-panel"><h2>No candidates match these filters</h2><p>Change or clear the filters to see other review candidates.</p></section> : <section className="panel" aria-labelledby="candidate-title">
        <div className="panel-header"><div><h2 className="panel-title" id="candidate-title">Candidates requiring review</h2><p className="panel-description">Ordered by {sorts.find((sort) => sort.value === selectedSort)?.label.toLowerCase()}.</p></div><span className="count-badge">Page {result.page} of {lastPage}</span></div>
        <div className="table-wrap queue-table-wrap"><table className="source-table queue-table"><caption className="sr-only">Potential duplicate candidates</caption><thead><tr><th scope="col">Status</th><th scope="col">Matched work</th><th scope="col">Location and agency</th><th scope="col">Records</th><th scope="col">Action</th></tr></thead><tbody>{result.items.map((item) => <tr key={item.result_id}><td><span className={`status-chip status-${item.status.toLowerCase()}`}>{label(item.status)}</span></td><td><strong>{item.work_description}</strong><p className="cell-note">{item.work_ids.slice(0, 3).join(", ")}{item.work_ids.length > 3 ? ` and ${item.work_ids.length - 3} more` : ""}</p></td><td>{item.state}<p className="cell-note">{item.constituency} · {item.ida}</p></td><td>{integer.format(item.group_size)}</td><td><Link className="row-action" href={`/investigation-queue/${item.result_id}`}>Review evidence</Link></td></tr>)}</tbody></table></div>
        <div className="candidate-cards">{result.items.map((item) => <article className="candidate-card" key={`card-${item.result_id}`}><div className="review-row"><span className={`status-chip status-${item.status.toLowerCase()}`}>{label(item.status)}</span><strong>{item.group_size} records</strong></div><h3>{item.work_description}</h3><p>{item.state}, {item.constituency}</p><p className="cell-note">{item.ida}</p><Link className="row-action" href={`/investigation-queue/${item.result_id}`}>Review evidence</Link></article>)}</div>
      </section>}
      <nav className="pagination" aria-label="Candidate pages"><Link className={page <= 1 ? "disabled-link" : "secondary-link"} aria-disabled={page <= 1} tabIndex={page <= 1 ? -1 : undefined} href={page <= 1 ? "#" : pageHref(page - 1)}>Previous</Link><span>Showing {result.total ? (page - 1) * result.page_size + 1 : 0} to {Math.min(page * result.page_size, result.total)} of {integer.format(result.total)}</span><Link className={page >= lastPage ? "disabled-link" : "secondary-link"} aria-disabled={page >= lastPage} tabIndex={page >= lastPage ? -1 : undefined} href={page >= lastPage ? "#" : pageHref(page + 1)}>Next</Link></nav>
    </main>
  </QueueShell>;
}
