"""Idempotent PostgreSQL schema initialisation for all MPLADS tables."""

import argparse
import os
import sys

import psycopg

from backend.detectors import DDL as DETECTORS_DDL
from backend.investigations import DDL as INVESTIGATIONS_DDL
from backend.staging import DDL as STAGING_DDL

ALL_DDL: list[tuple[str, str]] = [
    ("staging", STAGING_DDL),
    ("detectors", DETECTORS_DDL),
    ("investigations", INVESTIGATIONS_DDL),
]


def init_db(database_url: str) -> None:
    """Execute all schema DDLs idempotently within an atomic transaction."""
    with (
        psycopg.connect(database_url, connect_timeout=10) as connection,
        connection.transaction(),
    ):
        for _, ddl in ALL_DDL:
            connection.execute(ddl)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialise MPLADS PostgreSQL database schema tables."
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="Target database connection URL. Defaults to DATABASE_URL environment variable.",
    )
    args = parser.parse_args()

    if not args.database_url:
        parser.error(
            "Database URL required. Supply --database-url or set DATABASE_URL in the environment."
        )

    try:
        init_db(args.database_url)
        print("MPLADS database tables initialised successfully.")
    except psycopg.Error:
        # Never output driver messages that might contain connection credentials
        sys.stderr.write(
            "Database initialisation failed. Verify connection and privileges.\n"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
