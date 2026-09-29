"""API summary tests using synthetic rows and the dedicated PostgreSQL database."""

import importlib
import os
from contextlib import contextmanager
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.main import (
    app,
    database_connection,
    read_data_overview,
    require_review_key,
)
from backend.staging import DDL, stage

main_module = importlib.import_module("backend.main")


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


def test_candidate_detail_api_exposes_grounded_synthesis():
    operation = app.openapi()["paths"]["/investigation-candidates/{result_id}"]["get"]
    response_schema = operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    assert response_schema["$ref"].endswith("/CandidateDetail")
    detail_schema = app.openapi()["components"]["schemas"]["CandidateDetail"]
    assert "synthesis" in detail_schema["required"]


def test_database_dependency_reuses_configured_pool(monkeypatch):
    class FakePool:
        @contextmanager
        def connection(self):
            yield "pooled-connection"

    monkeypatch.setattr(main_module, "connection_pool", FakePool())

    dependency = database_connection()

    assert next(dependency) == "pooled-connection"
    with pytest.raises(StopIteration):
        next(dependency)


def test_database_dependency_reports_missing_configuration(monkeypatch):
    monkeypatch.setattr(main_module, "connection_pool", None)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(HTTPException) as error:
        next(database_connection())

    assert error.value.status_code == 503


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
