"""Automated tests for idempotent database schema initialisation."""

import os
from unittest.mock import patch
from uuid import uuid4

import pytest

from backend.init_db import init_db, main


def test_init_db_requires_database_url():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0


def test_init_db_creates_all_tables_idempotently():
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL not configured")

    import psycopg
    from psycopg import sql

    schema = "test_init_db_" + uuid4().hex
    with (
        psycopg.connect(os.environ["TEST_DATABASE_URL"], autocommit=True) as connection,
        connection.transaction(force_rollback=True),
    ):
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        connection.execute(
            sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema))
        )

        # Run initialization twice to verify idempotency
        init_db(os.environ["TEST_DATABASE_URL"])
        init_db(os.environ["TEST_DATABASE_URL"])

        # Confirm all required tables exist
        tables = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = current_schema()
            """
        ).fetchall()
        table_names = {t[0] for t in tables}

        expected = {
            "mplads_ingest_batch",
            "mplads_source_record",
            "mplads_detector_run",
            "mplads_detector_result",
            "mplads_review_event",
        }
        assert expected.issubset(table_names)
