"""Deterministic, explainable screening over immutable staged MPLADS records."""

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from decimal import Decimal
from statistics import median

ENGINE_VERSION = "2"
SANCTIONED_REPORT = "Works Sanctioned.csv"
PEER_MINIMUM = 20
PEER_MEDIAN_MULTIPLIER = Decimal(2)

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


def detect(records):
    results = duplicate_work_candidates(records)
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
    return batches, records


def build_run(source_batches, records):
    results = detect(records)
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
            batches, records = load_inputs(connection)
            if not records:
                parser.exit(1, "No staged Works Sanctioned detail records found.\n")
            run, results = build_run(batches, records)
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
