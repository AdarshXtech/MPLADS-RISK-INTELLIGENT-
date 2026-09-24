import type { SourceRecord } from "@/lib/investigations";

export type MapRecord = Pick<SourceRecord, "source_sha256" | "parser_version" | "record_number" | "work_id" | "location">;
export const sourceKey = (source: MapRecord) => JSON.stringify([source.source_sha256, source.parser_version, source.record_number]);

export function coordinates(source: MapRecord): [number, number] | null {
  const { status, latitude, longitude } = source.location;
  return status === "VERIFIED_COORDINATES" && typeof latitude === "number" && typeof longitude === "number" &&
    Number.isFinite(latitude) && Number.isFinite(longitude) && Math.abs(latitude) <= 90 && Math.abs(longitude) <= 180
    ? [latitude, longitude] : null;
}
