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
    from psycopg.conninfo import make_conninfo

    schema = "test_init_db_" + uuid4().hex
    database_url = os.environ["TEST_DATABASE_URL"]
    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))

    schema_url = make_conninfo(database_url, options=f"-csearch_path={schema}")
    try:
        init_db(schema_url)
        init_db(schema_url)

        with psycopg.connect(schema_url) as connection:
            tables = connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                """
            ).fetchall()
            table_names = {table[0] for table in tables}

        expected = {
            "mplads_ingest_batch",
            "mplads_source_record",
            "mplads_detector_run",
            "mplads_detector_result",
            "mplads_review_event",
        }
        assert expected.issubset(table_names)
    finally:
        with psycopg.connect(database_url, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema))
            )
