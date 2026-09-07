"""API summary tests using synthetic rows and the dedicated PostgreSQL database."""

import os
from uuid import uuid4

import pytest

from backend.main import app, read_data_overview, require_review_key
from backend.staging import DDL, stage


def synthetic_batch():
    report = {
        "sha256": "synthetic-" + uuid4().hex,
        "version": "test",
        "source_file": "synthetic.csv",
    }
    records = [
        {
            "record_number": 1,
            "kind": "detail",
            "original": ["10.25"],
            "cleaned": {"amount": "10.25"},
            "derived": {},
            "issues": [{"code": "synthetic_check"}],
            "line_start": 2,
            "line_end": 2,
        }
    ]
    return report, records


def test_investigation_api_key_is_required(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setenv("MPLADS_REVIEW_API_KEY", "synthetic-test-key")
    require_review_key("synthetic-test-key")
    with pytest.raises(HTTPException) as missing:
        require_review_key(None)
    assert missing.value.status_code == 401
    with pytest.raises(HTTPException) as incorrect:
        require_review_key("incorrect")
    assert incorrect.value.status_code == 401


def test_investigation_sort_is_a_closed_api_enum():
    operation = app.openapi()["paths"]["/investigation-candidates"]["get"]
    sort_parameter = next(
        parameter
        for parameter in operation["parameters"]
        if parameter["name"] == "sort"
    )
    assert sort_parameter["schema"]["enum"] == [
        "group_smallest",
        "group_largest",
        "state",
        "recently_reviewed",
    ]


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not configured"
)
def test_data_overview_uses_staged_postgres_records():
    import psycopg
    from psycopg import sql

    schema = "test_overview_" + uuid4().hex
    with (
        psycopg.connect(
            os.environ["TEST_DATABASE_URL"], autocommit=True, connect_timeout=5
        ) as connection,
        connection.transaction(force_rollback=True),
    ):
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        connection.execute(
            sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema))
        )
        connection.execute(DDL)
        report, records = synthetic_batch()
        assert stage(connection, report, records)

        overview = read_data_overview(connection)

        assert overview.source_batches == 1
        assert overview.retained_records == 1
        assert overview.detail_records == 1
        assert overview.records_with_validation_issues == 1
        assert overview.sources[0].source_sha256 == report["sha256"]
