"""Deterministic, explainable screening over immutable staged MPLADS records."""

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from decimal import Decimal
from itertools import combinations
from math import asin, cos, radians, sin, sqrt
from statistics import median

ENGINE_VERSION = "3"
SANCTIONED_REPORT = "Works Sanctioned.csv"
PEER_MINIMUM = 20
PEER_MEDIAN_MULTIPLIER = Decimal(2)
LOCALITY_SPATIAL_RADIUS_METRES = Decimal(500)
DESCRIPTION_SIMILARITY_THRESHOLD = Decimal("0.60")
DESCRIPTION_MIN_SHARED_TOKENS = 3
MAX_DESCRIPTION_TOKEN_BUCKET = 250

DETECTOR_CONFIGURATION = {
    "duplicate_work_candidate": {
        "version": "1",
        "match": "exact normalised values across all configured fields with different work IDs",
        "fields": [
            "Work description",
            "work_type",
            "State",
            "Constituency",
            "IDA",
            "Sanction Date",
            "Sanction Amount ( ₹ )",
        ],
    },
    "locality_duplicate_candidate": {
        "version": "1",
        "match": "same work type, locality evidence, meaningful description similarity and an additional supporting signal",
        "locality_order": [
            "ward_village",
            "block_tehsil",
            "district",
            "state",
            "spatial_radius",
        ],
        "spatial_radius_metres": str(LOCALITY_SPATIAL_RADIUS_METRES),
        "spatial_radius_status": "prototype configuration requiring policy validation",
        "description_similarity_threshold": str(DESCRIPTION_SIMILARITY_THRESHOLD),
        "description_minimum_shared_tokens": DESCRIPTION_MIN_SHARED_TOKENS,
        "maximum_description_token_bucket": MAX_DESCRIPTION_TOKEN_BUCKET,
        "national_comparison": "not performed by this detector; version 1 exact-context screening remains the only national comparison",
    },
    "peer_sanction_cost": {
        "version": "1",
        "enabled": False,
        "disabled_reason": "Measured calibration produced too many candidates and available fields do not establish comparable engineering scope.",
        "peer_fields": ["Work category", "work_type"],
        "minimum_peer_count": PEER_MINIMUM,
        "median_multiplier": str(PEER_MEDIAN_MULTIPLIER),
    },
}

UNAVAILABLE_DETECTORS = [
    {
        "detector_id": "expenditure_progress_mismatch",
        "missing_fields": [
            "physical progress percentage",
            "dated milestones",
            "expected payment schedule",
        ],
    },
    {
        "detector_id": "expected_duration_delay",
        "missing_fields": [
            "expected completion date",
            "actual start date",
            "approved extensions",
        ],
    },
    {
        "detector_id": "mplads_compliance",
        "missing_fields": [
            "verified applicable guideline clause",
            "rule-specific eligibility and approval evidence",
        ],
    },
    {
        "detector_id": "predictive_early_warning",
        "missing_fields": [
            "historical as-of snapshots",
            "verified outcomes",
            "contractual deadlines",
        ],
    },
]

DDL = """
CREATE TABLE IF NOT EXISTS mplads_detector_run (
    run_id text PRIMARY KEY,
    engine_version text NOT NULL,
    configuration jsonb NOT NULL,
    source_batches jsonb NOT NULL,
    unavailable_detectors jsonb NOT NULL,
    result_count integer NOT NULL CHECK (result_count >= 0),
    results_sha256 text NOT NULL
);
ALTER TABLE mplads_detector_run
    ADD COLUMN IF NOT EXISTS run_status text NOT NULL DEFAULT 'calibration'
    CHECK (run_status IN ('calibration', 'reviewable'));
CREATE TABLE IF NOT EXISTS mplads_detector_result (
    run_id text NOT NULL REFERENCES mplads_detector_run (run_id),
    result_id text NOT NULL,
    detector_id text NOT NULL,
    detector_name text NOT NULL,
    severity text NOT NULL CHECK (severity = 'review'),
    confidence numeric NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    explanation text NOT NULL,
    verification_step text NOT NULL,
    fields_used jsonb NOT NULL,
    evidence jsonb NOT NULL,
    source_records jsonb NOT NULL,
    limitations jsonb NOT NULL,
    PRIMARY KEY (run_id, result_id)
);
"""


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def identifier(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def normalise_text(value):
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(re.findall(r"[^\W_]+", value.casefold()))


def _record_key(record):
    return (
        record["source_sha256"],
        record["parser_version"],
        record["record_number"],
    )


def _location_context(record, locations):
    """Return a non-mutating view of reviewed or source administrative location."""
    stored = (locations or {}).get(_record_key(record))
    cleaned = record["cleaned"]
    administrative = {
        "state": (stored or {}).get("state") or cleaned.get("State"),
        "district": (stored or {}).get("district"),
        "constituency": (stored or {}).get("constituency")
        or cleaned.get("Constituency"),
        "block_tehsil": (stored or {}).get("block_tehsil"),
        "ward_village": (stored or {}).get("ward_village"),
    }
    if stored:
        status = stored["location_status"]
    elif administrative["state"] or administrative["constituency"]:
        status = "ADMINISTRATIVE_ONLY"
    else:
        status = "LOCATION_UNAVAILABLE"
    return {
        **administrative,
        "location_status": status,
        "location_source": (stored or {}).get("location_source"),
        "verified_address_text": (stored or {}).get("verified_address_text"),
        "latitude": (stored or {}).get("latitude"),
        "longitude": (stored or {}).get("longitude"),
        "last_verified_at": (stored or {}).get("last_verified_at"),
    }


def _tokens(value):
    return set((normalise_text(value) or "").split())


def _description_similarity(left, right):
    left_tokens, right_tokens = _tokens(left), _tokens(right)
    shared = left_tokens & right_tokens
    union = left_tokens | right_tokens
    similarity = Decimal(len(shared)) / Decimal(len(union)) if union else Decimal(0)
    return similarity, sorted(shared)


def _distance_metres(left, right):
    if None in {
        left["latitude"],
        left["longitude"],
        right["latitude"],
        right["longitude"],
    }:
        return None
    lat1, lon1, lat2, lon2 = map(
        radians,
        (
            float(left["latitude"]),
            float(left["longitude"]),
            float(right["latitude"]),
            float(right["longitude"]),
        ),
    )
    latitude_delta, longitude_delta = lat2 - lat1, lon2 - lon1
    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(longitude_delta / 2) ** 2
    )
    return Decimal(str(2 * 6_371_000 * asin(sqrt(haversine)))).quantize(Decimal("0.01"))


def _locality_evidence(left, right):
    labels = {
        "ward_village": "Ward/village",
        "block_tehsil": "Block/tehsil",
        "district": "District",
        "state": "State",
    }
    matched = {}
    for field in ("ward_village", "block_tehsil", "district", "state"):
        left_value, right_value = left.get(field), right.get(field)
        if (
            left_value
            and right_value
            and normalise_text(left_value) == normalise_text(right_value)
        ):
            matched[field] = left_value
            return {"level": field, "label": labels[field], "matched_fields": matched}
    distance = _distance_metres(left, right)
    if distance is not None and distance <= LOCALITY_SPATIAL_RADIUS_METRES:
        return {
            "level": "spatial_radius",
            "label": "Verified-coordinate radius",
            "matched_fields": matched,
            "distance_metres": str(distance),
        }
    return None


def _supporting_signals(left_record, right_record, left_location, right_location):
    left, right = left_record["cleaned"], right_record["cleaned"]
    signals = []
    if normalise_text(left.get("IDA")) and normalise_text(
        left.get("IDA")
    ) == normalise_text(right.get("IDA")):
        signals.append(
            {
                "signal": "same_authority",
                "label": "Same authority",
                "value": left["IDA"],
            }
        )
    if normalise_text(left_location.get("constituency")) and normalise_text(
        left_location.get("constituency")
    ) == normalise_text(right_location.get("constituency")):
        signals.append(
            {
                "signal": "same_constituency",
                "label": "Same constituency",
                "value": left_location["constituency"],
            }
        )
    if left.get("Sanction Date") and left.get("Sanction Date") == right.get(
        "Sanction Date"
    ):
        signals.append(
            {
                "signal": "same_sanction_date",
                "label": "Same sanction date",
                "value": left["Sanction Date"],
            }
        )
    if left.get("Sanction Amount ( ₹ )") and left.get(
        "Sanction Amount ( ₹ )"
    ) == right.get("Sanction Amount ( ₹ )"):
        signals.append(
            {
                "signal": "same_sanction_amount",
                "label": "Same sanction amount",
                "value": left["Sanction Amount ( ₹ )"],
            }
        )
    return signals


def source_reference(record):
    return {
        "source_sha256": record["source_sha256"],
        "parser_version": record["parser_version"],
        "record_number": record["record_number"],
        "work_id": record["derived"].get("work_id"),
    }


def result(
    detector_id,
    detector_name,
    explanation,
    verification_step,
    fields,
    evidence,
    records,
    limitations,
):
    references = sorted(
        (source_reference(record) for record in records),
        key=lambda item: (
            item["source_sha256"],
            item["parser_version"],
            item["record_number"],
        ),
    )
    result_id = identifier(
        {
            "detector_id": detector_id,
            "version": DETECTOR_CONFIGURATION[detector_id]["version"],
            "source_records": references,
        }
    )
    return {
        "result_id": result_id,
        "detector_id": detector_id,
        "detector_name": detector_name,
        "severity": "review",
        "confidence": "1",
        "explanation": explanation,
        "verification_step": verification_step,
        "fields_used": fields,
        "evidence": evidence,
        "source_records": references,
        "limitations": limitations,
    }


def duplicate_work_candidates(records):
    fields = DETECTOR_CONFIGURATION["duplicate_work_candidate"]["fields"]
    groups = defaultdict(list)
    for record in records:
        cleaned, derived = record["cleaned"], record["derived"]
        raw_values = {
            "Work description": cleaned.get("Work description"),
            "work_type": derived.get("work_type"),
            "State": cleaned.get("State"),
            "Constituency": cleaned.get("Constituency"),
            "IDA": cleaned.get("IDA"),
            "Sanction Date": cleaned.get("Sanction Date"),
            "Sanction Amount ( ₹ )": cleaned.get("Sanction Amount ( ₹ )"),
        }
        key = tuple(normalise_text(raw_values[field]) for field in fields)
        if derived.get("work_id") and all(key):
            groups[key].append(record)

    candidates = []
    for matched in groups.values():
        work_ids = sorted({record["derived"]["work_id"] for record in matched})
        if len(work_ids) < 2:
            continue
        cleaned = matched[0]["cleaned"]
        evidence = {
            "match_type": "exact after case, punctuation and whitespace normalisation",
            "matched_record_count": len(matched),
            "different_work_ids": work_ids,
            "matched_values": {
                "Work description": cleaned["Work description"],
                "work_type": matched[0]["derived"]["work_type"],
                "State": cleaned["State"],
                "Constituency": cleaned["Constituency"],
                "IDA": cleaned["IDA"],
                "Sanction Date": cleaned["Sanction Date"],
                "Sanction Amount ( ₹ )": cleaned["Sanction Amount ( ₹ )"],
            },
        }
        candidates.append(
            result(
                "duplicate_work_candidate",
                "Potential duplicate work candidate",
                f"{len(matched)} sanctioned records have different Work IDs but the configured descriptive, administrative, date and amount fields match exactly after normalisation.",
                "Verify the underlying recommendations, locations, asset identities and sanction records before treating these as separate or duplicate works.",
                fields,
                evidence,
                matched,
                [
                    "No asset ID, precise location, coordinates or quantities are available.",
                    "Repeated template descriptions can create legitimate matches.",
                    "This result is a candidate for verification, not proof of duplication or misuse.",
                    "Confidence represents certainty that the configured fields match, not probability of misuse.",
                ],
            )
        )
    return sorted(candidates, key=lambda item: item["result_id"])


def locality_duplicate_candidates(records, locations=None):
    """Screen conservatively within the nearest available locality context.

    The configured radius only narrows comparison. It cannot independently
    create a potential duplicate candidate.
    """
    candidates = []
    # Compare within locality buckets first, then only pairs sharing enough
    # non-generic description tokens. This avoids an all-records pairwise scan.
    locality_buckets = defaultdict(list)
    contexts = {
        _record_key(record): _location_context(record, locations) for record in records
    }
    for record in records:
        work_type = normalise_text(record["derived"].get("work_type"))
        if not work_type:
            continue
        context = contexts[_record_key(record)]
        for field in ("ward_village", "block_tehsil", "district", "state"):
            value = normalise_text(context.get(field))
            if value:
                locality_buckets[(work_type, field, value)].append(record)
    candidate_tokens = defaultdict(set)
    for bucket in locality_buckets.values():
        token_groups = defaultdict(list)
        for record in bucket:
            for token in _tokens(record["cleaned"].get("Work description")):
                token_groups[token].append(record)
        for grouped in token_groups.values():
            if len(grouped) > MAX_DESCRIPTION_TOKEN_BUCKET:
                continue
            for left_record, right_record in combinations(grouped, 2):
                left_key, right_key = sorted(
                    (_record_key(left_record), _record_key(right_record))
                )
                candidate_tokens[(left_key, right_key)].add(
                    normalise_text(left_record["cleaned"].get("Work description"))
                )
    record_by_key = {_record_key(record): record for record in records}
    # A small grid limits verified-coordinate comparisons to nearby cells.
    # Exact Haversine distance is still required before a spatial pair is used.
    spatial_grid = defaultdict(list)
    for record in records:
        key = _record_key(record)
        context = contexts[key]
        if context["latitude"] is None or context["longitude"] is None:
            continue
        cell = (
            int(float(context["latitude"]) / 0.005),
            int(float(context["longitude"]) / 0.005),
        )
        for latitude_offset in range(-2, 3):
            for longitude_offset in range(-2, 3):
                for other_key in spatial_grid[
                    (cell[0] + latitude_offset, cell[1] + longitude_offset)
                ]:
                    other = record_by_key[other_key]
                    if (
                        normalise_text(record["derived"].get("work_type"))
                        == normalise_text(other["derived"].get("work_type"))
                        and _distance_metres(context, contexts[other_key])
                        <= LOCALITY_SPATIAL_RADIUS_METRES
                    ):
                        candidate_tokens[tuple(sorted((key, other_key)))].add("spatial")
        spatial_grid[cell].append(key)
    for left_key, right_key in candidate_tokens:
        left_record, right_record = record_by_key[left_key], record_by_key[right_key]
        left_id, right_id = (
            left_record["derived"].get("work_id"),
            right_record["derived"].get("work_id"),
        )
        if not left_id or not right_id or left_id == right_id:
            continue
        left_type, right_type = (
            normalise_text(left_record["derived"].get("work_type")),
            normalise_text(right_record["derived"].get("work_type")),
        )
        if not left_type or left_type != right_type:
            continue
        left_location = contexts[left_key]
        right_location = contexts[right_key]
        locality = _locality_evidence(left_location, right_location)
        if locality is None:
            continue
        similarity, shared_tokens = _description_similarity(
            left_record["cleaned"].get("Work description"),
            right_record["cleaned"].get("Work description"),
        )
        if (
            similarity < DESCRIPTION_SIMILARITY_THRESHOLD
            or len(shared_tokens) < DESCRIPTION_MIN_SHARED_TOKENS
        ):
            continue
        supporting_signals = _supporting_signals(
            left_record, right_record, left_location, right_location
        )
        if not supporting_signals:
            continue
        distance = _distance_metres(left_location, right_location)
        statuses = sorted(
            {left_location["location_status"], right_location["location_status"]}
        )
        coordinate_available = distance is not None
        evidence = {
            "match_type": "locality-first potential-duplicate screening",
            "matched_record_count": 2,
            "different_work_ids": sorted([left_id, right_id]),
            "matched_values": {
                "Work description": left_record["cleaned"].get("Work description"),
                "work_type": left_record["derived"].get("work_type"),
                "State": locality["matched_fields"].get("state")
                or left_location.get("state"),
                "Constituency": left_location.get("constituency"),
                "IDA": left_record["cleaned"].get("IDA"),
            },
            "locality_evidence": locality,
            "location_summary": {
                "statuses": statuses,
                "coordinate_availability": "available"
                if coordinate_available
                else "unavailable",
            },
            "spatial_evidence": {
                "distance_metres": str(distance) if distance is not None else None,
                "distance_kilometres": str(
                    (distance / Decimal(1000)).quantize(Decimal("0.001"))
                )
                if distance is not None
                else None,
                "within_configured_radius": distance is not None
                and distance <= LOCALITY_SPATIAL_RADIUS_METRES,
                "configured_radius_metres": str(LOCALITY_SPATIAL_RADIUS_METRES),
                "configuration_status": "prototype configuration requiring policy validation",
            },
            "matched_administrative_fields": locality["matched_fields"],
            "matched_descriptive_fields": {
                "work_type": left_record["derived"].get("work_type"),
                "description_similarity": str(similarity.quantize(Decimal("0.0001"))),
                "shared_description_tokens": shared_tokens,
            },
            "supporting_signals": supporting_signals,
        }
        limitations = [
            "This is a potential duplicate candidate requiring verification, not proof of duplication or misuse.",
            "The spatial radius is a prototype configuration requiring policy validation; it is not an official MPLADS limit.",
            "Physical duplicate confirmation requires official review of asset identity, exact location, quantities, scope, phases, documents and inspection evidence.",
            "Confidence represents certainty that the configured rule matched, not probability of misuse.",
        ]
        if not coordinate_available:
            limitations.append(
                "Location is not sufficiently verified for spatial comparison. This record was compared only using available administrative fields."
            )
        candidates.append(
            result(
                "locality_duplicate_candidate",
                "Locality-aware potential duplicate candidate",
                "Two different Work IDs have the same work type, meaningful description similarity, "
                f"{locality['label'].lower()} locality evidence and {len(supporting_signals)} additional supporting signal(s).",
                "Verify asset identity, exact location, quantities, scope, phases, source documents and inspection evidence before deciding whether the works are separate or potential duplicates.",
                [
                    "work_type",
                    "Work description",
                    "location administrative fields",
                    "latitude/longitude when verified",
                    "IDA",
                    "Constituency",
                    "Sanction Date",
                    "Sanction Amount ( ₹ )",
                ],
                evidence,
                [left_record, right_record],
                limitations,
            )
        )
    return sorted(candidates, key=lambda item: item["result_id"])


def peer_cost_candidates(records):
    groups = defaultdict(list)
    for record in records:
        cleaned, derived = record["cleaned"], record["derived"]
        amount = cleaned.get("Sanction Amount ( ₹ )")
        key = (
            normalise_text(cleaned.get("Work category")),
            normalise_text(derived.get("work_type")),
        )
        if amount is not None and all(key):
            groups[key].append((record, Decimal(amount)))

    candidates = []
    for peers in groups.values():
        if len(peers) < PEER_MINIMUM:
            continue
        peer_median = median(amount for _, amount in peers)
        if peer_median <= 0:
            continue
        for record, amount in peers:
            if amount < peer_median * PEER_MEDIAN_MULTIPLIER:
                continue
            ratio = amount / peer_median
            candidates.append(
                result(
                    "peer_sanction_cost",
                    "Peer sanction-cost candidate",
                    f"The sanctioned amount is {ratio.quantize(Decimal('0.0001'))} times the median of {len(peers)} records in the same work-category and work-type group.",
                    "Verify engineering scope, quantities, rates, revisions and whether the selected records are genuinely comparable.",
                    ["Sanction Amount ( ₹ )", "Work category", "work_type"],
                    {
                        "sanction_amount_inr": str(amount),
                        "peer_median_inr": str(peer_median),
                        "amount_to_median_ratio": str(
                            ratio.quantize(Decimal("0.0001"))
                        ),
                        "peer_count": len(peers),
                        "threshold_multiplier": str(PEER_MEDIAN_MULTIPLIER),
                    },
                    [record],
                    [
                        "Peer groups do not control for quantities, dimensions, unit rates or revisions.",
                        "The threshold is an exploratory screening rule, not an official MPLADS limit.",
                        "This result is not proof of a cost overrun or misuse.",
                        "Confidence represents certainty that the threshold matched, not probability of misuse.",
                    ],
                )
            )
    return sorted(candidates, key=lambda item: item["result_id"])


def detect(records, locations=None):
    results = duplicate_work_candidates(records)
    results.extend(locality_duplicate_candidates(records, locations))
    return sorted(results, key=lambda item: (item["detector_id"], item["result_id"]))


def load_inputs(connection):
    batches = [
        {
            "source_file": row[0],
            "source_sha256": row[1],
            "parser_version": row[2],
        }
        for row in connection.execute(
            "SELECT source_file, source_sha256, parser_version "
            "FROM mplads_ingest_batch ORDER BY source_file, source_sha256, parser_version"
        ).fetchall()
    ]
    records = [
        {
            "source_sha256": row[0],
            "parser_version": row[1],
            "record_number": row[2],
            "cleaned": row[3],
            "derived": row[4],
        }
        for row in connection.execute(
            "SELECT r.source_sha256, r.parser_version, r.record_number, "
            "r.cleaned_values, r.derived_values "
            "FROM mplads_ingest_batch b JOIN mplads_source_record r "
            "USING (source_sha256, parser_version) "
            "WHERE b.source_file=%s AND r.record_kind='detail' "
            "ORDER BY r.source_sha256, r.parser_version, r.record_number",
            (SANCTIONED_REPORT,),
        ).fetchall()
    ]
    locations = {
        (row[0], row[1], row[2]): {
            "state": row[3],
            "district": row[4],
            "constituency": row[5],
            "block_tehsil": row[6],
            "ward_village": row[7],
            "verified_address_text": row[8],
            "latitude": row[9],
            "longitude": row[10],
            "location_source": row[11],
            "location_status": row[12],
            "last_verified_at": row[13].isoformat() if row[13] else None,
        }
        for row in connection.execute(
            "SELECT DISTINCT ON (source_sha256, parser_version, record_number) "
            "source_sha256, parser_version, record_number, state, district, constituency, "
            "block_tehsil, ward_village, verified_address_text, latitude, longitude, "
            "location_source, location_status, last_verified_at FROM mplads_work_location "
            "ORDER BY source_sha256, parser_version, record_number, last_verified_at DESC NULLS LAST, location_id DESC"
        ).fetchall()
    }
    return batches, records, locations


def build_run(source_batches, records, locations=None):
    results = detect(records, locations)
    results_sha256 = identifier(results)
    run = {
        "run_id": identifier(
            {
                "engine_version": ENGINE_VERSION,
                "configuration": DETECTOR_CONFIGURATION,
                "source_batches": source_batches,
            }
        ),
        "engine_version": ENGINE_VERSION,
        "configuration": DETECTOR_CONFIGURATION,
        "source_batches": source_batches,
        "unavailable_detectors": UNAVAILABLE_DETECTORS,
        "run_status": "reviewable",
        "result_count": len(results),
        "results_sha256": results_sha256,
    }
    return run, results


def stage_run(connection, run, results):
    from psycopg.types.json import Jsonb

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO mplads_detector_run "
            "(run_id, engine_version, configuration, source_batches, "
            "unavailable_detectors, result_count, results_sha256, run_status) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT DO NOTHING RETURNING run_id",
            (
                run["run_id"],
                run["engine_version"],
                Jsonb(run["configuration"]),
                Jsonb(run["source_batches"]),
                Jsonb(run["unavailable_detectors"]),
                run["result_count"],
                run["results_sha256"],
                run["run_status"],
            ),
        )
        if cursor.fetchone() is None:
            stored = cursor.execute(
                "SELECT engine_version, configuration, source_batches, "
                "unavailable_detectors, result_count, results_sha256, run_status "
                "FROM mplads_detector_run WHERE run_id=%s",
                (run["run_id"],),
            ).fetchone()
            expected = (
                run["engine_version"],
                run["configuration"],
                run["source_batches"],
                run["unavailable_detectors"],
                run["result_count"],
                run["results_sha256"],
                run["run_status"],
            )
            if stored != expected:
                raise ValueError("Existing detector run differs; refusing overwrite")
            count = cursor.execute(
                "SELECT count(*) FROM mplads_detector_result WHERE run_id=%s",
                (run["run_id"],),
            ).fetchone()[0]
            if count != len(results):
                raise ValueError(
                    "Existing detector run has an inconsistent result count"
                )
            return False
        cursor.executemany(
            "INSERT INTO mplads_detector_result VALUES "
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                (
                    run["run_id"],
                    item["result_id"],
                    item["detector_id"],
                    item["detector_name"],
                    item["severity"],
                    Decimal(item["confidence"]),
                    item["explanation"],
                    item["verification_step"],
                    Jsonb(item["fields_used"]),
                    Jsonb(item["evidence"]),
                    Jsonb(item["source_records"]),
                    Jsonb(item["limitations"]),
                )
                for item in results
            ],
        )
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-tables", action="store_true")
    args = parser.parse_args()
    if not os.environ.get("DATABASE_URL"):
        parser.error("Set DATABASE_URL in the process environment")
    import psycopg

    try:
        with psycopg.connect(
            os.environ["DATABASE_URL"], connect_timeout=5
        ) as connection:
            if args.create_tables:
                connection.execute(DDL)
            batches, records, locations = load_inputs(connection)
            if not records:
                parser.exit(1, "No staged Works Sanctioned detail records found.\n")
            run, results = build_run(batches, records, locations)
            changed = stage_run(connection, run, results)
        counts = {
            detector_id: sum(item["detector_id"] == detector_id for item in results)
            for detector_id, configuration in DETECTOR_CONFIGURATION.items()
            if configuration.get("enabled", True)
        }
        print(
            json.dumps(
                {
                    "run_id": run["run_id"],
                    "stored": changed,
                    "result_count": len(results),
                    "by_detector": counts,
                    "unavailable_detectors": len(UNAVAILABLE_DETECTORS),
                },
                sort_keys=True,
            )
        )
    except (psycopg.Error, ValueError):
        parser.exit(
            1,
            "Detector run failed; transaction rolled back. Check database permissions and stored run integrity locally.\n",
        )


if __name__ == "__main__":
    main()
