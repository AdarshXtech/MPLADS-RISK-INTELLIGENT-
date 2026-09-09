import "server-only";

export type Status = "NEW" | "UNDER_REVIEW" | "VERIFICATION_REQUESTED" | "RESOLVED" | "DISMISSED";
export type Sort = "group_smallest" | "group_largest" | "state" | "recently_reviewed";

export type Candidate = {
  result_id: string;
  detector_name: string;
  severity: string;
  confidence: number;
  explanation: string;
  status: Status;
  group_size: number;
  work_ids: string[];
  work_description: string;
  state: string;
  constituency: string;
  ida: string;
  sanction_date: string;
  sanction_amount: string;
  last_reviewed_at: string | null;
};

export type CandidatePage = {
  items: Candidate[];
  page: number;
  page_size: number;
  total: number;
  states: string[];
};

export type InvestigationSummary = {
  total_candidates: number;
  new: number;
  under_review: number;
  verification_requested: number;
  resolved: number;
  dismissed: number;
};

export type CandidateDetail = Candidate & {
  detector_id: string;
  fields_used: string[];
  evidence: Record<string, unknown>;
  verification_step: string;
  limitations: string[];
  source_records: Array<{
    source_sha256: string;
    parser_version: string;
    record_number: number;
    work_id: string;
    cleaned_values: Record<string, unknown>;
    derived_values: Record<string, unknown>;
    validation_issues: unknown[];
  }>;
  history: Array<{
    from_status: Status;
    to_status: Status;
    decision: string | null;
    reason_code: string | null;
    documents_checked: string | null;
    evidence_references: string | null;
    notes: string | null;
    reviewer: string;
    created_at: string;
  }>;
};

export function resolveApiBaseUrl(): string {
  const raw = process.env.MPLADS_API_BASE_URL ?? "http://127.0.0.1:8000";
  const trimmed = raw.trim().replace(/\/+$/, "");
  if (!trimmed) return "http://127.0.0.1:8000";
  return trimmed.startsWith("http://") || trimmed.startsWith("https://")
    ? trimmed
    : `https://${trimmed}`;
}

export function apiTimeoutMs(): number {
  const val = Number(process.env.MPLADS_API_TIMEOUT_MS);
  return Number.isFinite(val) && val > 0 ? val : 45000;
}

function configuration() {
  const key = process.env.MPLADS_REVIEW_API_KEY;
  if (!key) throw new Error("MPLADS_REVIEW_API_KEY is not configured");
  return {
    baseUrl: resolveApiBaseUrl(),
    key,
  };
}

async function requestResponse(path: string, init?: RequestInit): Promise<Response> {
  const { baseUrl, key } = configuration();
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    cache: "no-store",
    signal: AbortSignal.timeout(apiTimeoutMs()),
    headers: { "Content-Type": "application/json", "X-MPLADS-Review-Key": key, ...init?.headers },
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({}));
    throw new Error(typeof problem.detail === "string" ? problem.detail : "Review service request failed");
  }
  return response;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  return (await requestResponse(path, init)).json() as Promise<T>;
}

export async function getCandidateCsv(parameters: URLSearchParams): Promise<ArrayBuffer> {
  return (await requestResponse(`/investigation-candidates.csv?${parameters}`)).arrayBuffer();
}

export function getCandidates(parameters: URLSearchParams): Promise<CandidatePage> {
  return request(`/investigation-candidates?${parameters.toString()}`);
}

export function getInvestigationSummary(): Promise<InvestigationSummary> {
  return request("/investigation-summary");
}

export function getCandidate(id: string): Promise<CandidateDetail> {
  return request(`/investigation-candidates/${encodeURIComponent(id)}`);
}

export function saveReview(id: string, reviewer: string, body: object): Promise<CandidateDetail> {
  return request(`/investigation-candidates/${encodeURIComponent(id)}/events`, {
    method: "POST",
    headers: { "X-MPLADS-Reviewer": reviewer },
    body: JSON.stringify(body),
  });
}
