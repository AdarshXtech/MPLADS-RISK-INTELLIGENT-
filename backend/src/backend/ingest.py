"""Versioned, lossless staging of the supplied MPLADS CSV reports.

No detector execution. Money is a decimal string in JSON, never a float.
"""

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

VERSION = "2"
REPORTS = {
    "Allocated Limit for Honble MPs": [
        "Sr. No.",
        "State",
        "Hon'ble Members of Parliaments",
        "Constituency",
        "Allocated AMOUNT ( ₹ )",
    ],
    "Amount consented for Calamity": [
        "Sr. No.",
        "Calamity Type",
        "Calamity Name",
        "Hon'ble Members of Parliament",
        "Date of Consent",
        "Consent Amount ( ₹ )",
    ],
    "Expenditure on Completed and On-going Works as on Date": [
        "Sr. No.",
        "State",
        "Work",
        "Work ID",
        "IDA",
        "Hon'ble Members of Parliament",
        "Constituency",
        "Expenditure Date",
        "Vendor Name",
        "Payment Status",
        "Fund Disbursed Amount ( ₹ )",
    ],
    "Works Recommended": [
        "Sr. No.",
        "Work category",
        "WORK",
        "State",
        "IDA",
        "Hon'ble Members of Parliament",
        "Constituency",
        "Work description",
        "Recommended date",
        "RECOMMENDED AMOUNT   ( ₹ )",
        "Sanction Date",
    ],
    "Works Sanctioned": [
        "Sr. No.",
        "Work category",
        "Work",
        "State",
        "IDA",
        "Hon'ble Members of Parliament",
        "Constituency",
        "Work description",
        "Recommended date",
        "Sanction Date",
        "Sanction Amount ( ₹ )",
        "Work Status",
    ],
    "Works Completed": [
        "Sr. No.",
        "Work Category",
        "Work",
        "State",
        "IDA",
        "Work Description",
        "Hon'ble Members of Parliament",
        "Constituency",
        "Image",
        "Completion Date",
        "Amount Disbursed ( ₹ )",
    ],
}
DATES = {
    "Date of Consent",
    "Expenditure Date",
    "Recommended date",
    "Sanction Date",
    "Completion Date",
}
MONTHS = dict(
    zip(
        [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
        range(1, 13),
    )
)
WORK_ID = re.compile(r"^(WS/\s*MP\d+/\d{4}-\d{4}/\d+)(?:-(.+))?$")
MONEY = re.compile(
    r"(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d{1,2})?$"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def money(value: str) -> str:
    if not MONEY.fullmatch(value):
        raise ValueError(
            "Expected non-negative INR amount with at most two decimal places"
        )
    return format(Decimal(value.replace(",", "")), "f")


def is_missing(field: str, raw: str) -> bool:
    value = raw.strip()
    return (
        not value
        or (field == "Image" and value == "N/A")
        or (field in DATES and value == "NA")
    )


def clean_value(field: str, raw: str):
    value = raw.strip()
    if is_missing(field, raw):
        return None
    if "₹" in field:
        return money(value)
    if field in DATES:
        match = re.fullmatch(r"(\d{2})-([A-Z][a-z]{2})-(\d{4})", value)
        if not match or match[2] not in MONTHS:
            raise ValueError("Expected dd-MMM-yyyy with English month abbreviation")
        return date(int(match[3]), MONTHS[match[2]], int(match[1])).isoformat()
    if field == "Sr. No.":
        if not re.fullmatch(r"[1-9]\d*", value):
            raise ValueError("Expected positive report serial number")
        return int(value)
    return value


def inspect_csv(path: Path) -> tuple[dict, list[dict]]:
    """Retain all records, including malformed rows and the summary footer."""
    if path.stem not in REPORTS:
        raise ValueError(f"Unsupported report filename: {path.name}")
    content = path.read_bytes()
    source_hash = digest(content)
    reader = csv.reader(
        io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True
    )
    headers = next(reader, [])
    if headers != REPORTS[path.stem]:
        raise ValueError(f"Unexpected columns/order in {path.name}: {headers!r}")
    records, issues, details, footers = [], [], [], []
    previous_line = reader.line_num
    for ordinal, values in enumerate(reader, 1):
        start_line = previous_line + 1
        previous_line = reader.line_num
        kind = "summary" if values and values[0].strip() == "Grand Total" else "detail"
        record = {
            "record_number": ordinal,
            "line_start": start_line,
            "line_end": reader.line_num,
            "kind": kind,
            "original": values,
            "cleaned": {},
            "derived": {},
            "issues": [],
        }

        def issue(code, field=None, message=None, record=record, ordinal=ordinal):
            item = {"code": code, "field": field, "message": message}
            record["issues"].append(item)
            issues.append({"record_number": ordinal, **item})

        if len(values) != len(headers):
            issue(
                "row_width",
                message=f"Expected {len(headers)} cells, found {len(values)}",
            )
            record["kind"] = "rejected"
        elif kind == "summary":
            # Sanctioned export places its total under Work Status, not the amount header.
            try:
                record["derived"]["reported_total_inr"] = money(values[-1].strip())
            except ValueError as error:
                issue("invalid_summary", message=str(error))
            footers.append(record)
        else:
            for field, raw in zip(headers, values):
                try:
                    cleaned = clean_value(field, raw)
                except ValueError as error:
                    cleaned = None
                    issue("invalid_value", field, str(error))
                record["cleaned"][field] = cleaned
                if cleaned is None:
                    issue("missing_value", field, "No usable value; not imputed")
                if raw != raw.strip():
                    issue(
                        "trimmed_whitespace",
                        field,
                        "Outer whitespace removed in cleaned value only",
                    )
            if "Work" in headers or "WORK" in headers:
                combined = "Work ID" not in headers
                field = (
                    "WORK" if "WORK" in headers else "Work" if combined else "Work ID"
                )
                work_value = record["cleaned"].get(field) or ""
                if field == "WORK" and work_value.startswith("NA-"):
                    record["derived"]["work_type"] = work_value[3:].strip()
                else:
                    match = WORK_ID.fullmatch(work_value)
                    if (
                        not match
                        or (combined and not match[2])
                        or (not combined and match[2])
                    ):
                        issue(
                            "invalid_work_id",
                            field,
                            "Unrecognised report work identifier structure",
                        )
                    else:
                        record["derived"]["work_id"] = re.sub(r"\s+", "", match[1])
                        if match[2]:
                            record["derived"]["work_type"] = match[2]
                        if re.search(r"\s", match[1]):
                            issue(
                                "work_id_whitespace",
                                field,
                                "Whitespace removed from derived ID only",
                            )
            status = record["cleaned"].get("Payment Status")
            if status is not None and status not in {
                "Payment Success",
                "Payment In-Progress",
            }:
                issue(
                    "unknown_payment_status",
                    "Payment Status",
                    "Not recognised by this parser version",
                )
            recommended = record["cleaned"].get("Recommended date")
            sanctioned = record["cleaned"].get("Sanction Date")
            if recommended and sanctioned and sanctioned < recommended:
                issue(
                    "date_order",
                    "Sanction Date",
                    "Sanction predates recommendation; verify source",
                )
            details.append(record)
        records.append(record)
    profile = []
    for index, field in enumerate(headers):
        raw_values = [r["original"][index] for r in details]
        nonblank = [v for v in raw_values if not is_missing(field, v)]
        profile.append(
            {
                "field": field,
                "datatype": "decimal INR"
                if "₹" in field
                else "date"
                if field in DATES
                else "integer"
                if field == "Sr. No."
                else "text",
                "null_count": len(details) - len(nonblank),
                "null_percent": round(
                    100 * (len(details) - len(nonblank)) / len(details), 6
                )
                if details
                else None,
                "unique_non_null_raw": len(set(nonblank)),
                "examples": list(dict.fromkeys(nonblank))[:3],
                "invalid_count": sum(
                    i["code"] == "invalid_value" and i["field"] == field for i in issues
                ),
            }
        )
    amount_field = next(h for h in headers if "₹" in h)
    amounts = [
        Decimal(r["cleaned"][amount_field])
        for r in details
        if r["cleaned"][amount_field] is not None
    ]
    total = sum(amounts, Decimal(0))
    totals = [r["derived"].get("reported_total_inr") for r in footers]
    reconciled = (
        len(totals) == 1 and totals[0] is not None and Decimal(totals[0]) == total
    )
    serials = Counter(r["cleaned"].get("Sr. No.") for r in details)
    ids = Counter(r["derived"]["work_id"] for r in details if "work_id" in r["derived"])
    status_totals = {}
    for r in details:
        status = r["cleaned"].get("Payment Status")
        amount = r["cleaned"].get(amount_field)
        if status and amount is not None:
            status_totals[status] = status_totals.get(status, Decimal(0)) + Decimal(
                amount
            )
    report = {
        "version": VERSION,
        "source_file": path.name,
        "sha256": source_hash,
        "encoding": "utf-8-sig",
        "headers": headers,
        "detail_rows": len(details),
        "rejected_rows": sum(r["kind"] == "rejected" for r in records),
        "summary_rows": len(footers),
        "profile": profile,
        "issues": issues,
        "issue_counts": dict(Counter(i["code"] for i in issues)),
        "listed_amount_sum_inr": str(total),
        "reported_totals_inr": totals,
        "total_reconciles": reconciled,
        "coverage": "unverified even when totals reconcile",
        "distinct_work_ids": len(ids),
        "repeated_work_ids": sum(n > 1 for n in ids.values()),
        "duplicate_serials": [s for s, n in serials.items() if n > 1],
        "exact_duplicate_detail_rows": len(details)
        - len({tuple(r["original"][1:]) for r in details}),
        "amount_by_payment_status_inr": {s: str(v) for s, v in status_totals.items()},
    }
    return report, records


def ingest(path: Path, output: Path) -> Path:
    path, output = path.resolve(), output.resolve()
    if output == path.parent or output.is_relative_to(path.parent):
        raise ValueError("Output must be separate from the raw source directory")
    report, records = inspect_csv(path)
    # Source hash + parser version form an immutable, reproducible processing identity.
    target = output / f"{path.stem}-{report['sha256']}-v{VERSION}"
    data = {
        "report.json": encode(report),
        "records.jsonl": b"".join(
            json.dumps(r, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
            for r in records
        ),
    }
    if target.exists():
        if not all(
            (target / name).is_file() and (target / name).read_bytes() == body
            for name, body in data.items()
        ):
            raise ValueError(
                "Existing output differs or is incomplete; refusing overwrite"
            )
        return target
    target.mkdir(parents=True)
    for name, body in data.items():
        with (target / name).open("xb") as stream:
            stream.write(body)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        target = ingest(args.source, args.output)
        report = json.loads((target / "report.json").read_text(encoding="utf-8"))
        print(
            json.dumps(
                {
                    "output": str(target),
                    "rows": report["detail_rows"],
                    "total_reconciles": report["total_reconciles"],
                    "issue_counts": report["issue_counts"],
                }
            )
        )
        # Exit 2 means staged for review, not clean/approved for analytics.
        return (
            2
            if report["issues"]
            or report["rejected_rows"]
            or not report["total_reconciles"]
            or report["duplicate_serials"]
            or report["exact_duplicate_detail_rows"]
            else 0
        )
    except (ValueError, OSError, csv.Error) as error:
        print(f"Ingestion failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
