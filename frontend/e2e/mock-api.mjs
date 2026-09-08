import { createServer } from "node:http";

const workIds = ["SYNTHETIC/1", "SYNTHETIC/2"];
const statuses = new Map();
const histories = new Map();
// Isolated browser-test controls. This server is never imported by the application.
const scenarios = new Map();
const candidates = Array.from({ length: 25 }, (_, index) => ({
  result_id: `synthetic-candidate-${String(index + 1).padStart(2, "0")}`,
  detector_name: "Potential duplicate work candidate",
  severity: "review",
  confidence: 1,
  explanation: "Two synthetic records have different work IDs but configured fields match.",
  status: "NEW",
  group_size: 2,
  work_ids: workIds,
  work_description: `Synthetic community hall ${index + 1}`,
  state: index % 2 ? "Test State Two" : "Test State One",
  constituency: "Test Constituency",
  ida: "Test Agency",
  sanction_date: "2025-01-02",
  sanction_amount: "100",
  last_reviewed_at: null,
}));

function send(response, code, body) {
  response.writeHead(code, { "Content-Type": "application/json" });
  response.end(JSON.stringify(body));
}

createServer(async (request, response) => {
  const pathname = new URL(request.url, "http://127.0.0.1:8012").pathname;
  if (pathname === "/__scenario" && request.method === "POST") {
    if (request.headers["x-mplads-review-key"] !== process.env.MPLADS_REVIEW_API_KEY) return send(response, 401, {});
    let body = "";
    for await (const chunk of request) body += chunk;
    const configuration = JSON.parse(body);
    scenarios.clear();
    if (configuration.reset) { statuses.clear(); histories.clear(); }
    for (const [path, value] of Object.entries(configuration.paths ?? {})) scenarios.set(path, value);
    return send(response, 200, { configured: true });
  }
  const scenario = scenarios.get(pathname);
  if (scenario?.delay) await new Promise((resolve) => setTimeout(resolve, scenario.delay));
  if (scenario?.status) return send(response, scenario.status, { detail: "Synthetic service failure. Please retry." });
  if (scenario?.body) return send(response, 200, scenario.body);
  if (request.method === "GET" && request.url === "/data-overview") return send(response, 200, {
    source_batches: 1,
    retained_records: 25,
    detail_records: 25,
    summary_records: 0,
    rejected_records: 0,
    records_with_validation_issues: 0,
    sources: [{
      source_file: "Synthetic.csv",
      source_sha256: "synthetic-source-sha256",
      parser_version: "test",
      retained_records: 25,
      detail_records: 25,
      summary_records: 0,
      rejected_records: 0,
      records_with_validation_issues: 0,
    }],
  });
  if (request.headers["x-mplads-review-key"] !== process.env.MPLADS_REVIEW_API_KEY) return send(response, 401, { detail: "Valid review service credentials required" });
  const url = new URL(request.url, "http://127.0.0.1:8012");
  const match = url.pathname.match(/^\/investigation-candidates\/([^/]+)$/);
  if (request.method === "GET" && url.pathname === "/investigation-summary") {
    const current = candidates.map((item) => statuses.get(item.result_id) ?? "NEW");
    return send(response, 200, {
      total_candidates: current.length,
      new: current.filter((status) => status === "NEW").length,
      under_review: current.filter((status) => status === "UNDER_REVIEW").length,
      verification_requested: current.filter((status) => status === "VERIFICATION_REQUESTED").length,
      resolved: current.filter((status) => status === "RESOLVED").length,
      dismissed: current.filter((status) => status === "DISMISSED").length,
    });
  }
  if (request.method === "GET" && ["/investigation-candidates", "/investigation-candidates.csv"].includes(url.pathname)) {
    const page = Number(url.searchParams.get("page") ?? 1);
    const query = (url.searchParams.get("query") ?? "").toLowerCase();
    const state = url.searchParams.get("state") ?? "";
    const requestedStatus = url.searchParams.get("status") ?? "";
    const filtered = candidates.map((item) => ({ ...item, status: statuses.get(item.result_id) ?? "NEW", last_reviewed_at: histories.get(item.result_id)?.[0]?.created_at ?? null })).filter((item) =>
      (!query || JSON.stringify(item).toLowerCase().includes(query)) &&
      (!state || item.state === state) && (!requestedStatus || item.status === requestedStatus));
    const sort = url.searchParams.get("sort") ?? "group_smallest";
    filtered.sort((left, right) => sort === "group_largest"
      ? right.group_size - left.group_size || left.result_id.localeCompare(right.result_id)
      : sort === "state"
        ? left.state.localeCompare(right.state) || left.result_id.localeCompare(right.result_id)
        : sort === "recently_reviewed"
          ? (right.last_reviewed_at ?? "").localeCompare(left.last_reviewed_at ?? "") || left.result_id.localeCompare(right.result_id)
          : left.group_size - right.group_size || left.result_id.localeCompare(right.result_id));
    if (url.pathname.endsWith(".csv")) {
      response.writeHead(200, { "Content-Type": "text/csv" });
      return response.end("\uFEFFresult_id,state,status\r\n" + filtered.map((item) => `${item.result_id},${item.state},${item.status}\r\n`).join(""));
    }
    return send(response, 200, { items: filtered.slice((page - 1) * 20, page * 20), page, page_size: 20, total: filtered.length, states: ["Test State One", "Test State Two"] });
  }
  if (request.method === "GET" && match) {
    const candidate = candidates.find((item) => item.result_id === match[1]);
    if (!candidate) return send(response, 404, { detail: "Investigation candidate not found" });
    return send(response, 200, detail(candidate));
  }
  const eventMatch = url.pathname.match(/^\/investigation-candidates\/([^/]+)\/events$/);
  if (request.method === "POST" && eventMatch) {
    let body = "";
    request.on("data", (chunk) => { body += chunk; });
    request.on("end", () => {
      const event = JSON.parse(body);
      const previous = statuses.get(eventMatch[1]) ?? "NEW";
      statuses.set(eventMatch[1], event.target_status);
      const history = histories.get(eventMatch[1]) ?? [];
      history.unshift({ from_status: previous, to_status: event.target_status, decision: event.decision, reason_code: event.reason_code, documents_checked: event.documents_checked, evidence_references: event.evidence_references, notes: event.notes, reviewer: request.headers["x-mplads-reviewer"], created_at: new Date().toISOString() });
      histories.set(eventMatch[1], history);
      send(response, 200, detail(candidates.find((item) => item.result_id === eventMatch[1])));
    });
    return;
  }
  send(response, 404, { detail: "Not found" });
}).listen(8012, "127.0.0.1");

function detail(candidate) {
  const status = statuses.get(candidate.result_id) ?? "NEW";
  const history = histories.get(candidate.result_id) ?? [];
  return {
    ...candidate, status, detector_id: "duplicate_work_candidate",
    fields_used: ["Work description", "State", "Constituency"],
    evidence: { matched_values: { "Work description": candidate.work_description, State: candidate.state, Constituency: candidate.constituency, IDA: candidate.ida, "Sanction Date": candidate.sanction_date, "Sanction Amount": candidate.sanction_amount } },
    verification_step: "Verify the underlying synthetic records before deciding.",
    limitations: ["Synthetic browser-test fixture only.", "This is not proof of duplication or misuse."],
    source_records: workIds.map((work_id, index) => ({ source_sha256: "synthetic-source-sha256", parser_version: "test", record_number: index + 1, work_id, cleaned_values: { "Work description": candidate.work_description }, derived_values: { work_id }, validation_issues: [] })),
    history,
  };
}
