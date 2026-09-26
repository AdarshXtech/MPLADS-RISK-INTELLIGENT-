"""PostgreSQL-backed investigation queue and append-only review history."""

import argparse
import json
import os
from datetime import datetime
from typing import Literal

import psycopg
from fastapi import HTTPException
from pydantic import BaseModel, Field

from backend.review_export import encode_csv

Status = Literal[
    "NEW", "UNDER_REVIEW", "VERIFICATION_REQUESTED", "RESOLVED", "DISMISSED"
]
Decision = Literal[
    "SEPARATE_WORKS", "POTENTIAL_DUPLICATE", "INSUFFICIENT_EVIDENCE", "DATA_ERROR"
]
ReasonCode = Literal[
    "DIFFERENT_LOCATION",
    "DIFFERENT_ASSET",
    "DIFFERENT_PHASE_OR_QUANTITY",
    "SAME_ASSET_AND_SCOPE",
    "SOURCE_RECORD_ERROR",
    "DOCUMENTS_UNAVAILABLE",
    "OTHER",
]
Sort = Literal["group_smallest", "group_largest", "state", "recently_reviewed"]
LocationStatus = Literal[
    "VERIFIED_COORDINATES",
    "ADMINISTRATIVE_ONLY",
    "ADDRESS_UNVERIFIED",
    "LOCATION_UNAVAILABLE",
]

SORT_SQL = {
    "group_smallest": "jsonb_array_length(r.source_records), r.result_id",
    "group_largest": "jsonb_array_length(r.source_records) DESC, r.result_id",
    "state": "lower(COALESCE(r.evidence->'matched_values'->>'State', '')), r.result_id",
    "recently_reviewed": "last_event.created_at DESC NULLS LAST, r.result_id",
}

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "NEW": {"UNDER_REVIEW"},
    "UNDER_REVIEW": {"VERIFICATION_REQUESTED", "RESOLVED", "DISMISSED"},
    "VERIFICATION_REQUESTED": {"UNDER_REVIEW", "RESOLVED", "DISMISSED"},
    "RESOLVED": {"UNDER_REVIEW"},
    "DISMISSED": {"UNDER_REVIEW"},
}

DDL = """
CREATE TABLE IF NOT EXISTS mplads_review_event (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id text NOT NULL,
    result_id text NOT NULL,
    from_status text NOT NULL CHECK (from_status IN
        ('NEW','UNDER_REVIEW','VERIFICATION_REQUESTED','RESOLVED','DISMISSED')),
    to_status text NOT NULL CHECK (to_status IN
        ('UNDER_REVIEW','VERIFICATION_REQUESTED','RESOLVED','DISMISSED')),
    decision text CHECK (decision IS NULL OR decision IN
        ('SEPARATE_WORKS','POTENTIAL_DUPLICATE','INSUFFICIENT_EVIDENCE','DATA_ERROR')),
    reason_code text,
    documents_checked text,
    evidence_references text,
    notes text,
    reviewer text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id, result_id)
        REFERENCES mplads_detector_result (run_id, result_id)
);
CREATE INDEX IF NOT EXISTS mplads_review_event_candidate_idx
    ON mplads_review_event (run_id, result_id, event_id DESC);
"""


class InvestigationCandidate(BaseModel):
    result_id: str
    detector_name: str
    severity: str
    confidence: float
    explanation: str
    status: Status
    group_size: int
    work_ids: list[str]
    work_description: str
    state: str
    constituency: str
    ida: str
    sanction_date: str
    sanction_amount: str
    locality_level: str
    location_statuses: list[LocationStatus]
    distance_metres: float | None = None
    last_reviewed_at: datetime | None = None


class CandidatePage(BaseModel):
    items: list[InvestigationCandidate]
    page: int
    page_size: int
    total: int
    states: list[str]
    localities: list[str]
    location_statuses: list[LocationStatus]


class InvestigationSummary(BaseModel):
    total_candidates: int
    new: int
    under_review: int
    verification_requested: int
    resolved: int
    dismissed: int


class AuditEvent(BaseModel):
    event_id: int
    run_id: str
    result_id: str
    detector_name: str
    work_description: str
    from_status: Status
    to_status: Status
    decision: Decision | None
    reason_code: str | None
    reviewer: str
    created_at: datetime


class AuditEventPage(BaseModel):
    items: list[AuditEvent]
    page: int
    page_size: int
    total: int


class SourceEvidence(BaseModel):
    source_sha256: str
    parser_version: str
    record_number: int
    work_id: str
    cleaned_values: dict
    derived_values: dict
    validation_issues: list
    location: dict


class ReviewEvent(BaseModel):
    from_status: Status
    to_status: Status
    decision: Decision | None
    reason_code: str | None
    documents_checked: str | None
    evidence_references: str | None
    notes: str | None
    reviewer: str
    created_at: datetime


class CandidateDetail(InvestigationCandidate):
    detector_id: str
    fields_used: list[str]
    evidence: dict
    verification_step: str
    limitations: list[str]
    source_records: list[SourceEvidence]
    history: list[ReviewEvent]


class ReviewEventCreate(BaseModel):
    expected_status: Status
    target_status: Status
    decision: Decision | None = None
    reason_code: ReasonCode | None = None
    documents_checked: str | None = Field(default=None, max_length=4000)
    evidence_references: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)


def _matched_value(evidence: dict, label: str) -> str:
    value = evidence.get("matched_values", {}).get(label)
    return "" if value is None else str(value)


def _amount(evidence: dict) -> str:
    for key, value in evidence.get("matched_values", {}).items():
        if key.startswith("Sanction Amount"):
            return "" if value is None else str(value)
    return ""


def _location_statuses(evidence: dict) -> list[LocationStatus]:
    statuses = evidence.get("location_summary", {}).get("statuses")
    if statuses:
        return statuses
    if _matched_value(evidence, "State"):
        return ["ADMINISTRATIVE_ONLY"]
    return ["LOCATION_UNAVAILABLE"]


def _locality_level(evidence: dict) -> str:
    return evidence.get("locality_evidence", {}).get("level", "EXACT_CONTEXT")


def _candidate(row) -> InvestigationCandidate:
    evidence = row[5]
    return InvestigationCandidate(
        result_id=row[0],
        detector_name=row[1],
        severity=row[2],
        confidence=float(row[3]),
        explanation=row[4],
        status=row[6] or "NEW",
        group_size=evidence.get("matched_record_count", 0),
        work_ids=evidence.get("different_work_ids", []),
        work_description=_matched_value(evidence, "Work description"),
        state=_matched_value(evidence, "State"),
        constituency=_matched_value(evidence, "Constituency"),
        ida=_matched_value(evidence, "IDA"),
        sanction_date=_matched_value(evidence, "Sanction Date"),
        sanction_amount=_amount(evidence),
        locality_level=_locality_level(evidence),
        location_statuses=_location_statuses(evidence),
        distance_metres=(
            float(evidence["spatial_evidence"]["distance_metres"])
            if evidence.get("spatial_evidence", {}).get("distance_metres") is not None
            else None
        ),
        last_reviewed_at=row[7],
    )


BASE_QUERY = """
WITH selected_run AS (
    SELECT run_id FROM mplads_detector_run
    WHERE run_status='reviewable'
    ORDER BY jsonb_array_length(source_batches) DESC, run_id DESC LIMIT 1
)
SELECT r.result_id, r.detector_name, r.severity, r.confidence,
       r.explanation, r.evidence, last_event.to_status, last_event.created_at,
       r.run_id, r.detector_id, r.source_records, r.fields_used,
       r.verification_step, r.limitations, last_event.decision,
       last_event.reason_code, last_event.documents_checked,
       last_event.evidence_references, last_event.notes, last_event.reviewer,
       run.configuration->r.detector_id->>'version' AS detector_version
FROM mplads_detector_result r
JOIN selected_run selected USING (run_id)
JOIN mplads_detector_run run USING (run_id)
LEFT JOIN LATERAL (
    SELECT to_status, created_at, decision, reason_code, documents_checked,
           evidence_references, notes, reviewer FROM mplads_review_event event
    WHERE event.run_id=r.run_id AND event.result_id=r.result_id
    ORDER BY event_id DESC LIMIT 1
) last_event ON true
"""


def investigation_summary(connection) -> InvestigationSummary:
    row = connection.execute(
        "SELECT count(*), "
        "count(*) FILTER (WHERE COALESCE(to_status, 'NEW')='NEW'), "
        "count(*) FILTER (WHERE to_status='UNDER_REVIEW'), "
        "count(*) FILTER (WHERE to_status='VERIFICATION_REQUESTED'), "
        "count(*) FILTER (WHERE to_status='RESOLVED'), "
        "count(*) FILTER (WHERE to_status='DISMISSED') FROM ("
        + BASE_QUERY
        + ") candidates"
    ).fetchone()
    return InvestigationSummary(
        total_candidates=row[0],
        new=row[1],
        under_review=row[2],
        verification_requested=row[3],
        resolved=row[4],
        dismissed=row[5],
    )


AUDIT_QUERY = """
WITH selected_run AS (
    SELECT run_id FROM mplads_detector_run
    WHERE run_status='reviewable'
    ORDER BY jsonb_array_length(source_batches) DESC, run_id DESC LIMIT 1
)
SELECT event.event_id, event.run_id, event.result_id, result.detector_name,
       COALESCE(result.evidence->'matched_values'->>'Work description', ''),
       event.from_status, event.to_status, event.decision, event.reason_code,
       event.reviewer, event.created_at
FROM mplads_review_event event
JOIN selected_run selected USING (run_id)
JOIN mplads_detector_result result
  ON result.run_id=event.run_id AND result.result_id=event.result_id
"""


def list_review_events(
    connection, page: int, page_size: int, query: str = "", status: str = ""
) -> AuditEventPage:
    clauses = ["1=1"]
    parameters: list[object] = []
    if query:
        term = query.strip().lower()
        clauses.append(
            "(strpos(lower(event.result_id), %s) > 0 "
            "OR strpos(lower(event.reviewer), %s) > 0 "
            "OR strpos(lower(result.evidence::text), %s) > 0)"
        )
        parameters.extend([term, term, term])
    if status:
        clauses.append("event.to_status = %s")
        parameters.append(status)
    where = " WHERE " + " AND ".join(clauses)
    total = connection.execute(
        "SELECT count(*) FROM (" + AUDIT_QUERY + where + ") review_events",
        parameters,
    ).fetchone()[0]
    rows = connection.execute(
        AUDIT_QUERY
        + where
        + " ORDER BY event.created_at DESC, event.event_id DESC LIMIT %s OFFSET %s",
        [*parameters, page_size, (page - 1) * page_size],
    ).fetchall()
    return AuditEventPage(
        items=[
            AuditEvent(
                event_id=row[0],
                run_id=row[1],
                result_id=row[2],
                detector_name=row[3],
                work_description=row[4],
                from_status=row[5],
                to_status=row[6],
                decision=row[7],
                reason_code=row[8],
                reviewer=row[9],
                created_at=row[10],
            )
            for row in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


def candidate_filter(
    query: str, state: str, status: str, locality: str, location_status: str
):
    clauses = ["1=1"]
    parameters: list[object] = []
    if query:
        clauses.append("strpos(lower(r.evidence::text), %s) > 0")
        parameters.append(query.strip().lower())
    if state:
        clauses.append("r.evidence->'matched_values'->>'State' = %s")
        parameters.append(state)
    if status:
        clauses.append("COALESCE(last_event.to_status, 'NEW') = %s")
        parameters.append(status)
    if locality:
        clauses.append(
            "COALESCE(r.evidence->'locality_evidence'->>'level', 'EXACT_CONTEXT') = %s"
        )
        parameters.append(locality)
    if location_status:
        clauses.append(
            "COALESCE(r.evidence->'location_summary'->'statuses', "
            "CASE WHEN r.evidence->'matched_values'->>'State' IS NULL "
            "THEN '[\"LOCATION_UNAVAILABLE\"]'::jsonb ELSE '[\"ADMINISTRATIVE_ONLY\"]'::jsonb END) @> jsonb_build_array(%s::text)"
        )
        parameters.append(location_status)
    return " WHERE " + " AND ".join(clauses), parameters


def list_candidates(
    connection,
    page: int,
    page_size: int,
    query: str,
    state: str,
    status: str,
    sort: Sort = "group_smallest",
    locality: str = "",
    location_status: str = "",
):
    where, parameters = candidate_filter(
        query, state, status, locality, location_status
    )
    total = connection.execute(
        "SELECT count(*) FROM (" + BASE_QUERY + where + ") candidates",
        parameters,
    ).fetchone()[0]
    rows = connection.execute(
        BASE_QUERY + where + " ORDER BY " + SORT_SQL[sort] + " LIMIT %s OFFSET %s",
        [*parameters, page_size, (page - 1) * page_size],
    ).fetchall()
    states = [
        row[0]
        for row in connection.execute(
            "WITH selected_run AS (SELECT run_id FROM mplads_detector_run "
            "WHERE run_status='reviewable' ORDER BY jsonb_array_length(source_batches) DESC, run_id DESC LIMIT 1) "
            "SELECT DISTINCT evidence->'matched_values'->>'State' FROM mplads_detector_result "
            "JOIN selected_run USING (run_id) ORDER BY 1"
        ).fetchall()
        if row[0]
    ]
    localities = [
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT COALESCE(evidence->'locality_evidence'->>'level', 'EXACT_CONTEXT') "
            "FROM mplads_detector_result JOIN (SELECT run_id FROM mplads_detector_run "
            "WHERE run_status='reviewable' ORDER BY jsonb_array_length(source_batches) DESC, run_id DESC LIMIT 1) selected "
            "USING (run_id) ORDER BY 1"
        ).fetchall()
    ]
    location_statuses = [
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT status FROM mplads_detector_result result JOIN "
            "(SELECT run_id FROM mplads_detector_run WHERE run_status='reviewable' "
            "ORDER BY jsonb_array_length(source_batches) DESC, run_id DESC LIMIT 1) selected USING (run_id) "
            "CROSS JOIN LATERAL jsonb_array_elements_text(COALESCE(result.evidence->'location_summary'->'statuses', "
            "CASE WHEN result.evidence->'matched_values'->>'State' IS NULL THEN '[\"LOCATION_UNAVAILABLE\"]'::jsonb "
            "ELSE '[\"ADMINISTRATIVE_ONLY\"]'::jsonb END)) AS status ORDER BY 1"
        ).fetchall()
    ]
    return CandidatePage(
        items=[_candidate(row) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
        states=states,
        localities=localities,
        location_statuses=location_statuses,
    )


EXPORT_LIMIT = 10_000
EXPORT_FIELDS = list(InvestigationCandidate.model_fields) + [
    "run_id",
    "detector_id",
    "detector_version",
    "source_records",
    "fields_used",
    "verification_step",
    "limitations",
    "decision",
    "reason_code",
    "documents_checked",
    "evidence_references",
    "notes",
    "reviewer",
    "confidence_meaning",
]


def export_candidates(
    connection,
    query: str,
    state: str,
    status: str,
    sort: Sort = "group_smallest",
    locality: str = "",
    location_status: str = "",
) -> bytes:
    """One statement gives the export a consistent PostgreSQL snapshot."""
    where, parameters = candidate_filter(
        query, state, status, locality, location_status
    )
    # ponytail: bounded in-memory CSV; use a background export if 10,000 groups are exceeded.
    rows = connection.execute(
        BASE_QUERY + where + " ORDER BY " + SORT_SQL[sort] + " LIMIT %s",
        [*parameters, EXPORT_LIMIT + 1],
    ).fetchall()
    if len(rows) > EXPORT_LIMIT:
        raise HTTPException(
            status_code=422, detail="Narrow the filters to at most 10,000 candidates"
        )
    records = []
    for row in rows:
        record = _candidate(row).model_dump(mode="json")
        record.update(
            run_id=row[8],
            detector_id=row[9],
            source_records=row[10],
            fields_used=row[11],
            verification_step=row[12],
            limitations=row[13],
            decision=row[14],
            reason_code=row[15],
            documents_checked=row[16],
            evidence_references=row[17],
            notes=row[18],
            reviewer=row[19],
            detector_version=row[20],
            confidence_meaning="Configured field-match certainty; not probability of misuse",
        )
        records.append(
            {
                key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                if isinstance(value, (list, dict))
                else value
                for key, value in record.items()
            }
        )
    return encode_csv(records, fields=EXPORT_FIELDS)


def candidate_detail(connection, result_id: str) -> CandidateDetail:
    row = connection.execute(
        BASE_QUERY + " WHERE r.result_id=%s", (result_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Investigation candidate not found")
    base = _candidate(row)
    detector = connection.execute(
        "SELECT run_id, detector_id, fields_used, evidence, verification_step, limitations "
        "FROM mplads_detector_result WHERE result_id=%s AND run_id=(SELECT run_id FROM "
        "mplads_detector_run WHERE run_status='reviewable' ORDER BY "
        "jsonb_array_length(source_batches) DESC, run_id DESC LIMIT 1)",
        (result_id,),
    ).fetchone()
    sources = connection.execute(
        "SELECT ref.source_sha256, ref.parser_version, ref.record_number, ref.work_id, "
        "source.cleaned_values, source.derived_values, source.validation_issues, "
        "location.state, location.district, location.constituency, location.block_tehsil, "
        "location.ward_village, location.verified_address_text, location.latitude, location.longitude, "
        "location.location_source, location.location_status, location.last_verified_at "
        "FROM mplads_detector_result result "
        "CROSS JOIN LATERAL jsonb_to_recordset(result.source_records) AS "
        "ref(source_sha256 text, parser_version text, record_number integer, work_id text) "
        "JOIN mplads_source_record source USING (source_sha256, parser_version, record_number) "
        "LEFT JOIN LATERAL (SELECT state,district,constituency,block_tehsil,ward_village,"
        "verified_address_text,latitude,longitude,location_source,location_status,last_verified_at "
        "FROM mplads_work_location WHERE source_sha256=ref.source_sha256 "
        "AND parser_version=ref.parser_version AND record_number=ref.record_number "
        "ORDER BY last_verified_at DESC NULLS LAST, location_id DESC LIMIT 1) location ON true "
        "WHERE result.run_id=%s AND result.result_id=%s ORDER BY ref.record_number",
        (detector[0], result_id),
    ).fetchall()
    history = connection.execute(
        "SELECT from_status,to_status,decision,reason_code,documents_checked,"
        "evidence_references,notes,reviewer,created_at FROM mplads_review_event "
        "WHERE run_id=%s AND result_id=%s ORDER BY event_id DESC",
        (detector[0], result_id),
    ).fetchall()
    return CandidateDetail(
        **base.model_dump(),
        detector_id=detector[1],
        fields_used=detector[2],
        evidence=detector[3],
        verification_step=detector[4],
        limitations=detector[5],
        source_records=[
            SourceEvidence(
                source_sha256=item[0],
                parser_version=item[1],
                record_number=item[2],
                work_id=item[3],
                cleaned_values=item[4],
                derived_values=item[5],
                validation_issues=item[6],
                location={
                    "status": item[16]
                    or (
                        "ADMINISTRATIVE_ONLY"
                        if item[4].get("State") or item[4].get("Constituency")
                        else "LOCATION_UNAVAILABLE"
                    ),
                    "state": item[7] or item[4].get("State"),
                    "district": item[8],
                    "constituency": item[9] or item[4].get("Constituency"),
                    "block_tehsil": item[10],
                    "ward_village": item[11],
                    "verified_address_text": item[12],
                    "latitude": float(item[13]) if item[13] is not None else None,
                    "longitude": float(item[14]) if item[14] is not None else None,
                    "location_source": item[15],
                    "last_verified_at": item[17].isoformat() if item[17] else None,
                },
            )
            for item in sources
        ],
        history=[
            ReviewEvent(
                from_status=item[0],
                to_status=item[1],
                decision=item[2],
                reason_code=item[3],
                documents_checked=item[4],
                evidence_references=item[5],
                notes=item[6],
                reviewer=item[7],
                created_at=item[8],
            )
            for item in history
        ],
    )


def add_review_event(
    connection, result_id: str, event: ReviewEventCreate, reviewer: str
):
    if event.target_status not in ALLOWED_TRANSITIONS[event.expected_status]:
        raise HTTPException(
            status_code=422, detail="Status transition is not permitted"
        )
    if event.target_status in {"RESOLVED", "DISMISSED"} and not event.decision:
        raise HTTPException(status_code=422, detail="A review decision is required")
    if event.target_status not in {"RESOLVED", "DISMISSED"} and event.decision:
        raise HTTPException(
            status_code=422, detail="A decision is allowed only when closing a review"
        )
    if event.target_status == "DISMISSED" and not (event.reason_code or "").strip():
        raise HTTPException(status_code=422, detail="A dismissal reason is required")
    with connection.transaction():
        detector = connection.execute(
            "SELECT run_id FROM mplads_detector_result WHERE result_id=%s AND run_id=(SELECT run_id "
            "FROM mplads_detector_run WHERE run_status='reviewable' ORDER BY "
            "jsonb_array_length(source_batches) DESC, run_id DESC LIMIT 1)",
            (result_id,),
        ).fetchone()
        if detector is None:
            raise HTTPException(
                status_code=404, detail="Investigation candidate not found"
            )
        connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (result_id,)
        )
        latest = connection.execute(
            "SELECT to_status FROM mplads_review_event WHERE run_id=%s AND result_id=%s "
            "ORDER BY event_id DESC LIMIT 1",
            (detector[0], result_id),
        ).fetchone()
        actual = latest[0] if latest else "NEW"
        if actual != event.expected_status:
            raise HTTPException(
                status_code=409,
                detail="The candidate status changed. Reload and try again",
            )
        connection.execute(
            "INSERT INTO mplads_review_event (run_id,result_id,from_status,to_status,decision,"
            "reason_code,documents_checked,evidence_references,notes,reviewer) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                detector[0],
                result_id,
                actual,
                event.target_status,
                event.decision,
                event.reason_code,
                event.documents_checked,
                event.evidence_references,
                event.notes,
                reviewer,
            ),
        )
    return candidate_detail(connection, result_id)


def main():
    parser = argparse.ArgumentParser(
        description="Create the append-only investigation review store"
    )
    parser.add_argument("--create-table", action="store_true", required=True)
    if not os.environ.get("DATABASE_URL"):
        parser.error("Set DATABASE_URL in the process environment")
    with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5) as connection:
        connection.execute(DDL)
    print("Investigation review store is ready")


if __name__ == "__main__":
    main()
