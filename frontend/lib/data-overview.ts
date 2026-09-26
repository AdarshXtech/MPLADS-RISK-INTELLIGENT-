import "server-only";

import { connection } from "next/server";
import { apiTimeoutMs, resolveApiBaseUrl } from "@/lib/investigations";

export type SourceReport = {
  source_file: string;
  source_sha256: string;
  parser_version: string;
  retained_records: number;
  detail_records: number;
  summary_records: number;
  rejected_records: number;
  records_with_validation_issues: number;
};

export type DataOverview = {
  source_batches: number;
  retained_records: number;
  detail_records: number;
  summary_records: number;
  rejected_records: number;
  records_with_validation_issues: number;
  sources: SourceReport[];
};

export type DataOverviewResult =
  | { status: "ready"; data: DataOverview }
  | { status: "error" };

function isDataOverview(value: unknown): value is DataOverview {
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

export async function getDataOverview(): Promise<DataOverviewResult> {
  await connection();
  try {
    const response = await fetch(`${resolveApiBaseUrl()}/data-overview`, {
      cache: "no-store",
      signal: AbortSignal.timeout(apiTimeoutMs()),
    });
    if (!response.ok) return { status: "error" };
    const data: unknown = await response.json();
    return isDataOverview(data) ? { status: "ready", data } : { status: "error" };
  } catch {
    return { status: "error" };
  }
}
