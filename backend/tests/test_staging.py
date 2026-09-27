"""Synthetic staging contract tests plus opt-in rollback-only PostgreSQL check."""

import os
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from backend.staging import DDL, stage


def batch():
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
            "issues": [],
            "line_start": 2,
            "line_end": 2,
        }
    ]
    return report, records


def test_parameterised_staging_and_idempotency():
    report, records = batch()
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (report["sha256"],)
    assert stage(conn, report, records)
    sql, parameters = cursor.executemany.call_args.args
    assert "%s" in sql and report["sha256"] not in sql
    assert parameters[0][0] == report["sha256"]
    cursor.reset_mock()
    cursor.fetchone.side_effect = [None, (report,), (1,)]
    assert not stage(conn, report, records)
    cursor.executemany.assert_not_called()


def test_staging_writes_records_in_bounded_chunks():
    report, records = batch()
    records = [
        {
            **records[0],
            "record_number": number,
            "line_start": number + 1,
            "line_end": number + 1,
        }
        for number in range(1, 6)
    ]
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (report["sha256"],)

    assert stage(conn, report, records, chunk_size=2)

    calls = cursor.executemany.call_args_list
    assert [len(call.args[1]) for call in calls] == [2, 2, 1]
    assert [row[2] for call in calls for row in call.args[1]] == [1, 2, 3, 4, 5]


def test_staging_rejects_invalid_chunk_size():
    report, records = batch()
    with pytest.raises(ValueError, match="positive integer"):
        stage(MagicMock(), report, records, chunk_size=0)


def test_existing_batch_conflict_is_not_overwritten():
    report, records = batch()
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = [None, ({"different": True},)]
    with pytest.raises(ValueError, match="differs"):
        stage(conn, report, records)
    cursor.executemany.assert_not_called()


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not configured"
)
def test_postgres_round_trip_idempotency_and_rollback():
    import psycopg

    report, records = batch()
    records = [
        {
            **records[0],
            "record_number": number,
            "line_start": number + 1,
            "line_end": number + 1,
        }
        for number in range(1, 6)
    ]
    schema = "test_ingest_" + uuid4().hex
    from psycopg import sql

    with psycopg.connect(
        os.environ["TEST_DATABASE_URL"], autocommit=True, connect_timeout=5
    ) as conn:
        with conn.transaction(force_rollback=True):
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            conn.execute(
                sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema))
            )
            conn.execute(DDL)
            assert stage(conn, report, records, chunk_size=2)
            assert not stage(conn, report, records, chunk_size=2)
            actual = conn.execute(
                "SELECT record_number, original_values, cleaned_values "
                "FROM mplads_source_record ORDER BY record_number"
            ).fetchall()
            assert actual == [
                (number, ["10.25"], {"amount": "10.25"}) for number in range(1, 6)
            ]
            failed_report, _ = batch()
            with pytest.raises(psycopg.errors.UniqueViolation), conn.transaction():
                stage(conn, failed_report, records + records)
            assert (
                conn.execute("SELECT count(*) FROM mplads_ingest_batch").fetchone()[0]
                == 1
            )
        assert (
            conn.execute(
                "SELECT count(*) FROM pg_namespace WHERE nspname=%s", (schema,)
            ).fetchone()[0]
            == 0
        )
