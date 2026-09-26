"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FileSearch, RotateCw } from "lucide-react";
import type { SourceRecord } from "@/lib/investigations";
import { coordinates, sourceKey, type MapRecord } from "./location-types";
import MapCanvas from "./location-map-canvas";

type DetailState = { status: "idle" } | { status: "loading"; record: MapRecord } | { status: "ready"; record: MapRecord; source: SourceRecord } | { status: "error"; record: MapRecord; expired: boolean };
const display = (value: unknown) => value === null || value === undefined || value === "" ? "Not supplied" : typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
const cleaned = (record: SourceRecord, name: string) => display(record.cleaned_values[name]);
const sanctionAmount = (record: SourceRecord) => {
  const match = Object.entries(record.cleaned_values).find(([key]) => key.startsWith("Sanction Amount"));
  return display(match?.[1]);
};

function Fields({ values }: { values: Record<string, unknown> }) {
  return <dl className="map-detail-fields">{Object.entries(values).map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{display(value)}</dd></div>)}</dl>;
}

export function LocationComparison({ candidateId, sources }: { candidateId: string; sources: SourceRecord[] }) {
  const [pair, setPair] = useState<[number, number]>([0, 1]);
  const [detail, setDetail] = useState<DetailState>({ status: "idle" });
  const requestRef = useRef<AbortController | null>(null);
  const records = useMemo(() => pair.flatMap((index) => sources[index] ? [sources[index]] : []), [pair, sources]);
  useEffect(() => () => requestRef.current?.abort(), []);

  const loadSource = useCallback(async (record: MapRecord) => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setDetail({ status: "loading", record });
    try {
      const query = new URLSearchParams({ sha: record.source_sha256, parser: record.parser_version, record: String(record.record_number) });
      const response = await fetch(`/investigation-queue/${encodeURIComponent(candidateId)}/source?${query}`, { cache: "no-store", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]) });
      if (!response.ok) {
        if (!controller.signal.aborted) setDetail({ status: "error", record, expired: response.status === 401 });
        return;
      }
      const body = await response.json();
      if (!body.source || sourceKey(body.source) !== sourceKey(record)) throw new Error("Unexpected source response");
      if (!controller.signal.aborted) setDetail({ status: "ready", record, source: body.source });
    } catch {
      if (!controller.signal.aborted) setDetail({ status: "error", record, expired: false });
    }
  }, [candidateId]);

  function changePair(slot: number, index: number) {
    requestRef.current?.abort();
    setDetail({ status: "idle" });
    setPair((current) => slot === 0 ? [index, current[1]] : [current[0], index]);
  }

  return <div className="location-comparison">
    <div className="duplicate-comparison-alert" role="note"><strong>Potential duplicate work candidate</strong><span>Compare Work A and Work B, then verify the source records before recording a decision.</span></div>
    {sources.length > 2 && <div className="comparison-selectors">{[0, 1].map((slot) => <div key={slot}><label htmlFor={`comparison-${slot}`}>Work {slot === 0 ? "A" : "B"}</label><select id={`comparison-${slot}`} value={pair[slot]} onChange={(event) => changePair(slot, Number(event.target.value))}>{sources.map((source, index) => <option key={sourceKey(source)} value={index} disabled={index === pair[1 - slot]}>{source.work_id} (record {source.record_number})</option>)}</select></div>)}</div>}
    <MapCanvas records={records} selectedKey={"record" in detail ? sourceKey(detail.record) : null} onSelect={loadSource} />
    <div className="map-records">{records.map((source, index) => {
      const point = coordinates(source);
      const selected = "record" in detail && sourceKey(detail.record) === sourceKey(source);
      return <div className={`map-record map-record-${index === 0 ? "a" : "b"}`} key={sourceKey(source)}>
        <div className="map-record-title"><span className="point-label">{index === 0 ? "A" : "B"}</span><strong>{source.work_id}</strong></div>
        <p className="map-work-title">{cleaned(source, "Work description")}</p>
        <dl className="map-record-fields"><div><dt>Location</dt><dd>{[source.location.ward_village, source.location.block_tehsil, source.location.district, source.location.state].filter(Boolean).join(", ") || "Not supplied"}</dd></div><div><dt>Coordinates</dt><dd className="map-coordinate">{point ? `${point[0]}, ${point[1]}` : "Exact point unavailable: verified coordinates required."}</dd></div><div><dt>Location status</dt><dd>{source.location.status.replaceAll("_", " ").toLowerCase()}</dd></div><div><dt>Sanction amount</dt><dd>{sanctionAmount(source)}</dd></div><div><dt>Constituency</dt><dd>{source.location.constituency ?? cleaned(source, "Constituency")}</dd></div><div><dt>District authority</dt><dd>{cleaned(source, "IDA")}</dd></div></dl>
        <button className="secondary-button" type="button" aria-pressed={selected} aria-controls="comparison-source-detail" onClick={() => void loadSource(source)}><FileSearch size={16} aria-hidden="true" />View source {index === 0 ? "A" : "B"}</button>
      </div>;
    })}</div>
    {sources.length === 0 && <p className="map-note">No source records are available for location comparison.</p>}
    <div className="map-source-detail" id="comparison-source-detail" aria-live="polite" aria-busy={detail.status === "loading"}>
      {detail.status === "idle" && <p className="map-note">Source details: no record selected.</p>}
      {detail.status === "loading" && <p>Loading source details for {detail.record.work_id}...</p>}
      {detail.status === "error" && <div role="alert"><p>{detail.expired ? "Your session has expired. Sign in again to view source details." : "Source details could not be loaded. Please retry."}</p>{detail.expired ? <Link href="/login" className="secondary-link">Sign in again</Link> : <button className="secondary-button" type="button" onClick={() => void loadSource(detail.record)}><RotateCw size={16} aria-hidden="true" />Retry source details</button>}</div>}
      {detail.status === "ready" && <>
        <h3>Source record details: {detail.source.work_id}</h3>
        <Fields values={{ "Work ID": detail.source.work_id, "Source SHA-256": detail.source.source_sha256, "Source record": detail.source.record_number, "Parser version": detail.source.parser_version }} />
        <h4>Location and verification</h4><Fields values={detail.source.location} />
        <h4>Cleaned source values</h4><Fields values={detail.source.cleaned_values} />
        <h4>Derived values</h4>{Object.keys(detail.source.derived_values).length ? <Fields values={detail.source.derived_values} /> : <p>Not supplied.</p>}
        <h4>Validation issues</h4>{detail.source.validation_issues.length ? <ul>{detail.source.validation_issues.map((issue, index) => <li key={index}><pre>{display(issue)}</pre></li>)}</ul> : <p>No validation issues reported for this record.</p>}
      </>}
    </div>
  </div>;
}
