import hmac
import os
from collections.abc import Iterator
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import Response
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from backend.investigations import (
    CandidateDetail,
    CandidatePage,
    InvestigationSummary,
    ReviewEventCreate,
    Sort,
    add_review_event,
    candidate_detail,
    export_candidates,
    investigation_summary,
    list_candidates,
)

app = FastAPI(
    title="MPLADS Risk Intelligence API",
    version="0.1.0",
)

review_key_header = APIKeyHeader(name="X-MPLADS-Review-Key", auto_error=False)


def require_review_key(key: Annotated[str | None, Depends(review_key_header)]) -> None:
    expected = os.environ.get("MPLADS_REVIEW_API_KEY")
    if not expected or not key or not hmac.compare_digest(key, expected):
        raise HTTPException(
            status_code=401, detail="Valid review service credentials required"
        )


class SourceReportOverview(BaseModel):
    source_file: str
    source_sha256: str
    parser_version: str
    retained_records: int
    detail_records: int
    summary_records: int
    rejected_records: int
    records_with_validation_issues: int


class DataOverview(BaseModel):
    source_batches: int
    retained_records: int
    detail_records: int
    summary_records: int
    rejected_records: int
    records_with_validation_issues: int
    sources: list[SourceReportOverview]


OVERVIEW_SQL = """
SELECT
    b.source_file,
    b.source_sha256,
    b.parser_version,
    count(r.record_number),
    count(*) FILTER (WHERE r.record_kind = 'detail'),
    count(*) FILTER (WHERE r.record_kind = 'summary'),
    count(*) FILTER (WHERE r.record_kind = 'rejected'),
    count(*) FILTER (WHERE jsonb_array_length(r.validation_issues) > 0)
FROM mplads_ingest_batch b
LEFT JOIN mplads_source_record r
    USING (source_sha256, parser_version)
GROUP BY b.source_file, b.source_sha256, b.parser_version
ORDER BY b.source_file
"""


def database_connection() -> Iterator[psycopg.Connection]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=503, detail="Data service is not configured")
    try:
        with psycopg.connect(database_url, connect_timeout=5) as connection:
            yield connection
    except psycopg.Error:
        raise HTTPException(
            status_code=503, detail="Data service is unavailable"
        ) from None


def read_data_overview(connection: psycopg.Connection) -> DataOverview:
    sources = [
        SourceReportOverview(
            source_file=row[0],
            source_sha256=row[1],
            parser_version=row[2],
            retained_records=row[3],
            detail_records=row[4],
            summary_records=row[5],
            rejected_records=row[6],
            records_with_validation_issues=row[7],
        )
        for row in connection.execute(OVERVIEW_SQL).fetchall()
    ]
    return DataOverview(
        source_batches=len(sources),
        retained_records=sum(source.retained_records for source in sources),
        detail_records=sum(source.detail_records for source in sources),
        summary_records=sum(source.summary_records for source in sources),
        rejected_records=sum(source.rejected_records for source in sources),
        records_with_validation_issues=sum(
            source.records_with_validation_issues for source in sources
        ),
        sources=sources,
    )


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "MPLADS Risk Intelligence API",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.get("/data-overview", response_model=DataOverview)
def data_overview(
    connection: Annotated[psycopg.Connection, Depends(database_connection)],
):
    return read_data_overview(connection)


@app.get(
    "/investigation-summary",
    response_model=InvestigationSummary,
    dependencies=[Depends(require_review_key)],
)
def investigation_workload(
    connection: Annotated[psycopg.Connection, Depends(database_connection)],
):
    return investigation_summary(connection)


@app.get(
    "/investigation-candidates",
    response_model=CandidatePage,
    dependencies=[Depends(require_review_key)],
)
def investigation_candidates(
    connection: Annotated[psycopg.Connection, Depends(database_connection)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    query: Annotated[str, Query(max_length=200)] = "",
    state: Annotated[str, Query(max_length=100)] = "",
    status: Annotated[
        str,
        Query(
            pattern="^(NEW|UNDER_REVIEW|VERIFICATION_REQUESTED|RESOLVED|DISMISSED)?$"
        ),
    ] = "",
    sort: Sort = "group_smallest",
):
    return list_candidates(
        connection, page, page_size, query.strip(), state, status, sort
    )


@app.get(
    "/investigation-candidates.csv",
    dependencies=[Depends(require_review_key)],
)
def investigation_export(
    connection: Annotated[psycopg.Connection, Depends(database_connection)],
    query: Annotated[str, Query(max_length=200)] = "",
    state: Annotated[str, Query(max_length=100)] = "",
    status: Annotated[
        str,
        Query(
            pattern="^(NEW|UNDER_REVIEW|VERIFICATION_REQUESTED|RESOLVED|DISMISSED)?$"
        ),
    ] = "",
    sort: Sort = "group_smallest",
):
    return Response(
        export_candidates(connection, query.strip(), state, status, sort),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="investigation-queue.csv"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get(
    "/investigation-candidates/{result_id}",
    response_model=CandidateDetail,
    dependencies=[Depends(require_review_key)],
)
def investigation_candidate(
    result_id: str,
    connection: Annotated[psycopg.Connection, Depends(database_connection)],
):
    return candidate_detail(connection, result_id)


@app.post(
    "/investigation-candidates/{result_id}/events",
    response_model=CandidateDetail,
    dependencies=[Depends(require_review_key)],
)
def create_review_event(
    result_id: str,
    event: ReviewEventCreate,
    connection: Annotated[psycopg.Connection, Depends(database_connection)],
    reviewer: Annotated[
        str, Header(alias="X-MPLADS-Reviewer", min_length=1, max_length=200)
    ],
):
    return add_review_event(connection, result_id, event, reviewer)
