"""Explicit PostgreSQL staging, with no risk tables or destructive statements."""

import argparse
import os
from pathlib import Path

from backend.ingest import inspect_csv

DDL = """
CREATE TABLE IF NOT EXISTS mplads_ingest_batch (
    source_sha256 text NOT NULL,
    parser_version text NOT NULL,
    source_file text NOT NULL,
    report jsonb NOT NULL,
    PRIMARY KEY (source_sha256, parser_version)
);
CREATE TABLE IF NOT EXISTS mplads_source_record (
    source_sha256 text NOT NULL,
    parser_version text NOT NULL,
    record_number integer NOT NULL CHECK (record_number > 0),
    record_kind text NOT NULL CHECK (record_kind IN ('detail', 'summary', 'rejected')),
    original_values jsonb NOT NULL,
    cleaned_values jsonb NOT NULL,
    derived_values jsonb NOT NULL,
    validation_issues jsonb NOT NULL,
    line_start integer NOT NULL,
    line_end integer NOT NULL,
    PRIMARY KEY (source_sha256, parser_version, record_number),
    FOREIGN KEY (source_sha256, parser_version)
        REFERENCES mplads_ingest_batch (source_sha256, parser_version)
);
"""


def stage(connection, report, records):
    from psycopg.types.json import Jsonb

    identity = (report["sha256"], report["version"])
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO mplads_ingest_batch VALUES (%s, %s, %s, %s) "
            "ON CONFLICT DO NOTHING RETURNING source_sha256",
            (*identity, report["source_file"], Jsonb(report)),
        )
        if cursor.fetchone() is None:
            cursor.execute(
                "SELECT report FROM mplads_ingest_batch WHERE source_sha256=%s AND parser_version=%s",
                identity,
            )
            if cursor.fetchone()[0] != report:
                raise ValueError("Existing batch metadata differs; refusing overwrite")
            cursor.execute(
                "SELECT count(*) FROM mplads_source_record WHERE source_sha256=%s AND parser_version=%s",
                identity,
            )
            if cursor.fetchone()[0] != len(records):
                raise ValueError("Existing batch has an inconsistent record count")
            return False
        cursor.executemany(
            "INSERT INTO mplads_source_record VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                (
                    *identity,
                    r["record_number"],
                    r["kind"],
                    Jsonb(r["original"]),
                    Jsonb(r["cleaned"]),
                    Jsonb(r["derived"]),
                    Jsonb(r["issues"]),
                    r["line_start"],
                    r["line_end"],
                )
                for r in records
            ],
        )
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--create-tables", action="store_true")
    args = parser.parse_args()
    if not os.environ.get("DATABASE_URL"):
        parser.error(
            "Set DATABASE_URL in the process environment; never put credentials in arguments"
        )
    report, records = inspect_csv(args.source)
    import psycopg

    try:
        with psycopg.connect(
            os.environ["DATABASE_URL"], connect_timeout=5
        ) as connection:
            if args.create_tables:
                connection.execute(DDL)
            changed = stage(connection, report, records)
        print("Staged for review" if changed else "Identical batch already staged")
    except psycopg.Error:
        # Driver messages can contain connection details; do not print secrets.
        parser.exit(
            1,
            "PostgreSQL staging failed; transaction rolled back. Check connection, permissions and schema locally.\n",
        )


if __name__ == "__main__":
    main()
