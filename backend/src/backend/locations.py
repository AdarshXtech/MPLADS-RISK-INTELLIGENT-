"""Append-only import and lookup of verified MPLADS work-location snapshots.

This module never geocodes addresses.  It accepts only reviewed administrative
locations or coordinates supplied through the documented import contract.
"""

import argparse
import csv
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

LOCATION_STATUSES = {
    "VERIFIED_COORDINATES",
    "ADMINISTRATIVE_ONLY",
    "ADDRESS_UNVERIFIED",
    "LOCATION_UNAVAILABLE",
}
IMPORT_FIELDS = [
    "source_sha256",
    "parser_version",
    "record_number",
    "state",
    "district",
    "constituency",
    "block_tehsil",
    "ward_village",
    "verified_address_text",
    "latitude",
    "longitude",
    "location_source",
    "location_status",
    "last_verified_at",
]

DDL = """
CREATE TABLE IF NOT EXISTS mplads_work_location (
    location_id text PRIMARY KEY,
    source_sha256 text NOT NULL,
    parser_version text NOT NULL,
    record_number integer NOT NULL CHECK (record_number > 0),
    work_id text NOT NULL,
    state text,
    district text,
    constituency text,
    block_tehsil text,
    ward_village text,
    verified_address_text text,
    latitude numeric(9,6),
    longitude numeric(9,6),
    location_source text NOT NULL,
    location_status text NOT NULL CHECK (location_status IN
        ('VERIFIED_COORDINATES','ADMINISTRATIVE_ONLY','ADDRESS_UNVERIFIED','LOCATION_UNAVAILABLE')),
    last_verified_at timestamptz,
    original_values jsonb NOT NULL,
    cleaned_values jsonb NOT NULL,
    derived_values jsonb NOT NULL,
    imported_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_sha256, parser_version, record_number)
        REFERENCES mplads_source_record (source_sha256, parser_version, record_number),
    CHECK ((latitude IS NULL) = (longitude IS NULL)),
    CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    CHECK (location_status <> 'VERIFIED_COORDINATES' OR latitude IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS mplads_work_location_source_idx
    ON mplads_work_location (source_sha256, parser_version, record_number, last_verified_at DESC);
"""


def _canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _identifier(value) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _timestamp(value: str | None) -> datetime | None:
    value = _text(value)
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("last_verified_at must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError("last_verified_at must include a timezone offset")
    return parsed


def clean_import_row(raw: dict[str, str]) -> dict:
    """Validate one reviewed import row without changing its source values."""
    missing_headers = set(IMPORT_FIELDS) - set(raw)
    if missing_headers:
        raise ValueError(
            f"Location import is missing columns: {sorted(missing_headers)}"
        )
    cleaned = {field: _text(raw.get(field)) for field in IMPORT_FIELDS}
    try:
        cleaned["record_number"] = int(cleaned["record_number"] or "")
    except ValueError as error:
        raise ValueError("record_number must be a positive integer") from error
    if cleaned["record_number"] <= 0:
        raise ValueError("record_number must be a positive integer")
    if not cleaned["source_sha256"] or not cleaned["parser_version"]:
        raise ValueError("source_sha256 and parser_version are required")
    if not cleaned["location_source"]:
        raise ValueError("location_source is required")
    if cleaned["location_status"] not in LOCATION_STATUSES:
        raise ValueError("location_status is not supported")
    try:
        latitude = float(cleaned["latitude"]) if cleaned["latitude"] else None
        longitude = float(cleaned["longitude"]) if cleaned["longitude"] else None
    except ValueError as error:
        raise ValueError("latitude and longitude must be decimal values") from error
    if (latitude is None) != (longitude is None):
        raise ValueError("latitude and longitude must be supplied together")
    if latitude is not None and not (
        -90 <= latitude <= 90 and -180 <= longitude <= 180
    ):
        raise ValueError("latitude or longitude is outside the permitted range")
    if cleaned["location_status"] == "VERIFIED_COORDINATES":
        if latitude is None or _timestamp(cleaned["last_verified_at"]) is None:
            raise ValueError(
                "VERIFIED_COORDINATES requires coordinates and a verified timestamp"
            )
    elif latitude is not None:
        raise ValueError("coordinates require VERIFIED_COORDINATES status")
    if (
        cleaned["location_status"] == "ADDRESS_UNVERIFIED"
        and not cleaned["verified_address_text"]
    ):
        raise ValueError("ADDRESS_UNVERIFIED requires an address text")
    cleaned["latitude"] = latitude
    cleaned["longitude"] = longitude
    cleaned["last_verified_at"] = _timestamp(cleaned["last_verified_at"])
    return cleaned


def read_import(path: Path) -> list[tuple[dict[str, str], dict]]:
    """Read the explicit CSV contract used for reviewed location snapshots."""
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != IMPORT_FIELDS:
            raise ValueError(
                "Location import columns must exactly match the documented order"
            )
        return [(row, clean_import_row(row)) for row in reader]


def stage_locations(connection, rows: list[tuple[dict[str, str], dict]]) -> bool:
    """Insert immutable location snapshots after checking their source provenance."""
    from psycopg.types.json import Jsonb

    staged = []
    for original, cleaned in rows:
        source = connection.execute(
            "SELECT derived_values FROM mplads_source_record WHERE source_sha256=%s "
            "AND parser_version=%s AND record_number=%s",
            (
                cleaned["source_sha256"],
                cleaned["parser_version"],
                cleaned["record_number"],
            ),
        ).fetchone()
        if source is None:
            raise ValueError("Location import references an unstaged source record")
        work_id = source[0].get("work_id")
        if not work_id:
            raise ValueError("Location import source record has no derived work ID")
        snapshot = {
            "source_sha256": cleaned["source_sha256"],
            "parser_version": cleaned["parser_version"],
            "record_number": cleaned["record_number"],
            "work_id": work_id,
            "cleaned": {
                key: value.isoformat() if isinstance(value, datetime) else value
                for key, value in cleaned.items()
                if key not in {"source_sha256", "parser_version", "record_number"}
            },
        }
        location_id = _identifier(snapshot)
        staged.append((location_id, original, cleaned, work_id, snapshot))
    changed = False
    for location_id, original, cleaned, work_id, snapshot in staged:
        values = (
            location_id,
            cleaned["source_sha256"],
            cleaned["parser_version"],
            cleaned["record_number"],
            work_id,
            cleaned["state"],
            cleaned["district"],
            cleaned["constituency"],
            cleaned["block_tehsil"],
            cleaned["ward_village"],
            cleaned["verified_address_text"],
            cleaned["latitude"],
            cleaned["longitude"],
            cleaned["location_source"],
            cleaned["location_status"],
            cleaned["last_verified_at"],
            Jsonb(original),
            Jsonb(snapshot["cleaned"]),
            Jsonb({"work_id": work_id}),
        )
        inserted = connection.execute(
            "INSERT INTO mplads_work_location (location_id,source_sha256,parser_version,"
            "record_number,work_id,state,district,constituency,block_tehsil,ward_village,"
            "verified_address_text,latitude,longitude,location_source,location_status,"
            "last_verified_at,original_values,cleaned_values,derived_values) VALUES "
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT DO NOTHING RETURNING location_id",
            values,
        ).fetchone()
        if inserted is None:
            stored = connection.execute(
                "SELECT cleaned_values, derived_values FROM mplads_work_location WHERE location_id=%s",
                (location_id,),
            ).fetchone()
            if stored != (snapshot["cleaned"], {"work_id": work_id}):
                raise ValueError(
                    "Existing location snapshot differs; refusing overwrite"
                )
        else:
            changed = True
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?")
    parser.add_argument("--create-tables", action="store_true")
    args = parser.parse_args()
    if not args.create_tables and args.source is None:
        parser.error("Provide an import CSV or use --create-tables")
    if not os.environ.get("DATABASE_URL"):
        parser.error("Set DATABASE_URL in the process environment")
    import psycopg

    rows = read_import(args.source) if args.source else []
    try:
        with psycopg.connect(
            os.environ["DATABASE_URL"], connect_timeout=5
        ) as connection:
            if args.create_tables:
                connection.execute(DDL)
            changed = stage_locations(connection, rows) if rows else False
        print("Location snapshots staged" if changed else "No new location snapshots")
    except (psycopg.Error, ValueError):
        parser.exit(
            1,
            "Location import failed; transaction rolled back. Check source provenance and reviewed values locally.\n",
        )


if __name__ == "__main__":
    main()
