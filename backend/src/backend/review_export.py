"""Export reviewable duplicate-work candidates as an Excel-friendly CSV."""

import argparse
import csv
import io
import os
from pathlib import Path

from backend.detectors import SANCTIONED_REPORT, load_inputs

DECISION_OPTIONS = (
    "SEPARATE_WORKS | POTENTIAL_DUPLICATE | INSUFFICIENT_EVIDENCE | DATA_ERROR"
)
REASON_OPTIONS = (
    "DIFFERENT_LOCATION | DIFFERENT_ASSET | DIFFERENT_PHASE_OR_QUANTITY | "
    "SAME_ASSET_AND_SCOPE | SOURCE_RECORD_ERROR | DOCUMENTS_UNAVAILABLE | OTHER"
)
FIELDS = [
    "review_order",
    "candidate_group_id",
    "group_size",
    "work_ids",
    "work_description",
    "work_type",
    "work_categories",
    "state",
    "constituency",
    "ida",
    "mp_names",
    "sanction_date",
    "sanction_amount_inr",
    "recommended_amounts_by_work_id",
    "recommended_dates_by_work_id",
    "sanction_source_records",
    "recommendation_source_records",
    "match_basis",
    "verification_step",
    "limitations",
    "review_decision_options",
    "review_reason_options",
    "review_decision",
    "review_reason_code",
    "documents_checked",
    "evidence_references",
    "reviewer_name",
    "review_date_yyyy_mm_dd",
    "district_verification_required_yes_no",
    "reviewer_notes",
]


def source_label(source_file, record):
    return (
        f"{source_file}|sha256={record['source_sha256']}|"
        f"parser=v{record['parser_version']}|record={record['record_number']}"
    )


def load_reviewable_results(connection, run_id=None):
    if run_id is None:
        selected = connection.execute(
            "SELECT run_id FROM mplads_detector_run "
            "WHERE run_status='reviewable' "
            "ORDER BY jsonb_array_length(source_batches) DESC, run_id DESC LIMIT 1"
        ).fetchone()
        if selected is None:
            raise ValueError("No reviewable detector run exists")
        run_id = selected[0]
    run = connection.execute(
        "SELECT run_id, result_count FROM mplads_detector_run "
        "WHERE run_id=%s AND run_status='reviewable'",
        (run_id,),
    ).fetchone()
    if run is None:
        raise ValueError("Requested detector run is not reviewable")
    results = [
        {
            "result_id": row[0],
            "detector_id": row[1],
            "evidence": row[2],
            "source_records": row[3],
            "verification_step": row[4],
            "limitations": row[5],
        }
        for row in connection.execute(
            "SELECT result_id, detector_id, evidence, source_records, "
            "verification_step, limitations FROM mplads_detector_result "
            "WHERE run_id=%s ORDER BY detector_id, result_id",
            (run_id,),
        ).fetchall()
    ]
    if len(results) != run[1]:
        raise ValueError("Detector run result count is inconsistent")
    return run_id, results


def load_recommendations(connection, work_ids):
    if not work_ids:
        return {}
    rows = connection.execute(
        "SELECT r.source_sha256, r.parser_version, r.record_number, "
        "r.cleaned_values, r.derived_values "
        "FROM mplads_ingest_batch b JOIN mplads_source_record r "
        "USING (source_sha256, parser_version) "
        "WHERE b.source_file='Works Recommended.csv' "
        "AND r.record_kind='detail' "
        "AND r.derived_values->>'work_id'=ANY(%s) "
        "ORDER BY r.source_sha256, r.parser_version, r.record_number",
        (sorted(work_ids),),
    ).fetchall()
    return {
        row[4]["work_id"]: {
            "source_sha256": row[0],
            "parser_version": row[1],
            "record_number": row[2],
            "cleaned": row[3],
            "derived": row[4],
        }
        for row in rows
    }


def joined(values):
    return "\n".join(str(value) for value in values if value is not None)


def build_rows(results, sanctioned_records, recommendations):
    sanctioned = {
        (
            record["source_sha256"],
            record["parser_version"],
            record["record_number"],
        ): record
        for record in sanctioned_records
    }
    rows = []
    ordered = sorted(
        results,
        key=lambda item: (len(item["source_records"]), item["result_id"]),
    )
    for order, item in enumerate(ordered, 1):
        if item["detector_id"] != "duplicate_work_candidate":
            continue
        records = []
        for reference in item["source_records"]:
            key = (
                reference["source_sha256"],
                reference["parser_version"],
                reference["record_number"],
            )
            if key not in sanctioned:
                raise ValueError("Candidate source record is unavailable")
            records.append(sanctioned[key])
        work_ids = sorted({record["derived"]["work_id"] for record in records})
        recommended = [
            recommendations[work_id]
            for work_id in work_ids
            if work_id in recommendations
        ]
        matched = item["evidence"]["matched_values"]
        rows.append(
            {
                "review_order": order,
                "candidate_group_id": item["result_id"],
                "group_size": len(records),
                "work_ids": joined(work_ids),
                "work_description": matched["Work description"],
                "work_type": matched["work_type"],
                "work_categories": joined(
                    sorted(
                        {record["cleaned"].get("Work category") for record in records}
                    )
                ),
                "state": matched["State"],
                "constituency": matched["Constituency"],
                "ida": matched["IDA"],
                "mp_names": joined(
                    sorted(
                        {
                            record["cleaned"].get("Hon'ble Members of Parliament")
                            for record in records
                        }
                    )
                ),
                "sanction_date": matched["Sanction Date"],
                "sanction_amount_inr": matched["Sanction Amount ( ₹ )"],
                "recommended_amounts_by_work_id": joined(
                    f"{record['derived']['work_id']}: {record['cleaned'].get('RECOMMENDED AMOUNT   ( ₹ )', '')}"
                    for record in recommended
                ),
                "recommended_dates_by_work_id": joined(
                    f"{record['derived']['work_id']}: {record['cleaned'].get('Recommended date', '')}"
                    for record in recommended
                ),
                "sanction_source_records": joined(
                    source_label(SANCTIONED_REPORT, record) for record in records
                ),
                "recommendation_source_records": joined(
                    source_label("Works Recommended.csv", record)
                    for record in recommended
                ),
                "match_basis": item["evidence"]["match_type"],
                "verification_step": item["verification_step"],
                "limitations": joined(item["limitations"]),
                "review_decision_options": DECISION_OPTIONS,
                "review_reason_options": REASON_OPTIONS,
                "review_decision": "",
                "review_reason_code": "",
                "documents_checked": "",
                "evidence_references": "",
                "reviewer_name": "",
                "review_date_yyyy_mm_dd": "",
                "district_verification_required_yes_no": "",
                "reviewer_notes": "",
            }
        )
    return rows


def encode_csv(rows, fields=FIELDS):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(
        {
            field: "'" + str(value)
            if str(value).lstrip().startswith(("=", "+", "-", "@"))
            else value
            for field, value in row.items()
        }
        for row in rows
    )
    return stream.getvalue().encode("utf-8-sig")


def write_once(path, content):
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError("Existing review CSV differs; refusing overwrite")
        return False
    with path.open("xb") as stream:
        stream.write(content)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    if not os.environ.get("DATABASE_URL"):
        parser.error("Set DATABASE_URL in the process environment")
    import psycopg

    try:
        with psycopg.connect(
            os.environ["DATABASE_URL"], connect_timeout=5
        ) as connection:
            run_id, results = load_reviewable_results(connection, args.run_id)
            _, sanctioned = load_inputs(connection)
            work_ids = {
                reference["work_id"]
                for item in results
                for reference in item["source_records"]
                if reference.get("work_id")
            }
            recommendations = load_recommendations(connection, work_ids)
        rows = build_rows(results, sanctioned, recommendations)
        changed = write_once(args.output, encode_csv(rows))
        print(
            f"{'Created' if changed else 'Verified'} {args.output.resolve()} "
            f"with {len(rows)} candidate groups from run {run_id}."
        )
    except (psycopg.Error, OSError, ValueError):
        parser.exit(
            1,
            "Review export failed. Check database access, run identity and output path locally.\n",
        )


if __name__ == "__main__":
    main()
