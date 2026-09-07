"""Audit supplied static XLSX exports against CSV; generate measured documentation.

This is not a general Excel reader. Reject formulas, shared strings and unfamiliar
workbook structures. CSV is the ingestion source; XLSX/PDF remain independent evidence.
"""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from backend.ingest import (
    REPORTS,
    clean_value,
    digest,
    encode,
    ingest,
    inspect_csv,
    is_missing,
    money,
)

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
MEANINGS = {
    "Sr. No.": (
        "Ordinal within this export, not a durable identifier",
        "Provenance only",
        "Must not be used to join different reports",
    ),
    "State": (
        "Reported state or union territory",
        "Peer context",
        "Labels are not standard geographic codes",
    ),
    "Work": (
        "Work type in expenditure; combined work ID and type in sanctioned/completed",
        "Linkage and peer context",
        "Not a unique project description; parse ID separately where embedded",
    ),
    "WORK": (
        "Combined work identifier and type when sanctioned, or NA and work type when not sanctioned",
        "Recommendation-to-sanction linkage where a Work ID exists",
        "NA means no Work ID is reported; it must not be treated as an identifier",
    ),
    "Work ID": (
        "Reported identifier for the work",
        "Cross-report linkage",
        "Tabs/spaces require explicit derived normalisation; repeated payments are not duplicates",
    ),
    "IDA": (
        "District authority label; implementing district authority is an inferred expansion",
        "Administrative context",
        "Not a contractor ID or verified executing agency; district and office are combined",
    ),
    "Hon'ble Members of Parliament": (
        "Reported MP display name",
        "Context, not culpability",
        "Names lack stable IDs and can vary in spelling or title",
    ),
    "Hon'ble Members of Parliaments": (
        "Reported MP display name",
        "Context, not culpability",
        "No stable person ID",
    ),
    "Constituency": (
        "Reported constituency label",
        "Peer context",
        "Not project coordinates or a unique MP key",
    ),
    "Expenditure Date": (
        "Date labelled as expenditure by the export",
        "Payment timing context",
        "Meaning for in-progress payments is unverified; not start/completion date",
    ),
    "Vendor Name": (
        "Reported payment recipient display name",
        "Payment grouping",
        "Not a verified vendor identifier; may include offices and agencies",
    ),
    "Payment Status": (
        "Reported payment processing state",
        "Separate successful and pending amounts",
        "Payment success does not establish physical work completion",
    ),
    "Fund Disbursed Amount ( ₹ )": (
        "Reported per-row disbursal amount in INR",
        "Payment analysis only",
        "Includes in-progress status; sum does not prove actual settled expenditure or full project cost",
    ),
    "Work category": (
        "Administrative work category",
        "Peer/compliance context",
        "Not quantity or engineering scale",
    ),
    "Work Category": (
        "Administrative work category",
        "Peer/compliance context",
        "Not quantity or engineering scale",
    ),
    "Work description": (
        "Free-text description of sanctioned work",
        "Candidate similarity context",
        "Spelling and project scope vary; no verified coordinates or quantities",
    ),
    "Work Description": (
        "Free-text description of completed work",
        "Candidate similarity context",
        "Not independent evidence that an asset exists",
    ),
    "Recommended date": (
        "Reported recommendation date",
        "Administrative sequence",
        "Not the physical work start date",
    ),
    "Sanction Date": (
        "Reported sanction date",
        "Administrative duration context",
        "No expected completion date or extension record",
    ),
    "Sanction Amount ( ₹ )": (
        "Reported sanction amount in INR",
        "Limited peer-cost context",
        "No quantities, revisions or unit costs; footer amount is in Work Status column",
    ),
    "RECOMMENDED AMOUNT   ( ₹ )": (
        "Reported recommended amount in INR",
        "Recommendation amount and later sanction comparison where linked",
        "No quantities, unit rates or revision history; export coverage is unverified",
    ),
    "Work Status": (
        "Reported administrative work state",
        "Workflow context",
        "Not a physical-progress percentage or validated outcome",
    ),
    "Image": (
        "Export marker for image availability",
        "Data-quality context only",
        "Images is not a URL or asset verification; N/A treated as missing",
    ),
    "Completion Date": (
        "Reported work completion date",
        "Observed duration when linked",
        "Not an expected due date; reporting lag unmeasured",
    ),
    "Amount Disbursed ( ₹ )": (
        "Reported disbursal amount for completed work in INR",
        "Completed-work context",
        "Do not add to expenditure report: possible overlapping amounts",
    ),
    "Allocated AMOUNT ( ₹ )": (
        "Reported MP allocation limit in INR",
        "Supplementary context",
        "Not a work-level budget; period unknown",
    ),
    "Calamity Type": (
        "Reported calamity classification",
        "Supplementary context",
        "Not independently verified classification",
    ),
    "Calamity Name": (
        "Reported calamity name",
        "Supplementary context",
        "No stable event ID",
    ),
    "Date of Consent": (
        "Reported consent date",
        "Supplementary timing",
        "Not a payment date",
    ),
    "Consent Amount ( ₹ )": (
        "Reported consented amount in INR",
        "Supplementary context",
        "Consent does not prove disbursal",
    ),
}


def read_static_xlsx(path):
    with ZipFile(path) as archive:
        if sum(e.file_size for e in archive.infolist()) > 150_000_000:
            raise ValueError("Workbook exceeds inspection size limit")
        sheet_names = [
            n
            for n in archive.namelist()
            if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)
        ]
        if sheet_names != ["xl/worksheets/sheet1.xml"]:
            raise ValueError("Expected exactly one exported worksheet")
        content = archive.read(sheet_names[0])
        if b"<!DOCTYPE" in content or b"<!ENTITY" in content:
            raise ValueError("DTD/entities are not supported")
        root = ET.fromstring(content)
        rows = []
        for row in root.findall("s:sheetData/s:row", NS):
            values = {}
            for cell in row.findall("s:c", NS):
                if cell.find("s:f", NS) is not None or cell.get("t") not in (
                    None,
                    "n",
                    "inlineStr",
                ):
                    raise ValueError(
                        "Only static numeric/inline-string exports are supported"
                    )
                letters = re.match(r"[A-Z]+", cell.attrib["r"])[0]
                index = 0
                for letter in letters:
                    index = index * 26 + ord(letter) - 64
                values[index - 1] = (
                    "".join(cell.itertext())
                    if cell.get("t") == "inlineStr"
                    else cell.findtext("s:v", "", NS)
                )
            rows.append(
                (
                    int(row.attrib["r"]),
                    [values.get(i, "") for i in range(max(values, default=-1) + 1)],
                )
            )
    return rows


def xlsx_audit(path, report, records):
    rows = read_static_xlsx(path)
    headers = rows[1][1]
    if headers != report["headers"]:
        raise ValueError("XLSX header does not match CSV")
    width = len(headers)
    details, summaries = [], []
    for number, values in rows[2:]:
        values += [""] * (width - len(values))
        if len(values) != width:
            raise ValueError("Unexpected XLSX width")
        if values[0] == "Grand Total":
            summaries.append(
                {"sheet_row": number, "reported_total_inr": money(values[-1])}
            )
        elif re.fullmatch(r"[1-9]\d*", values[0]):
            details.append((number, values))
        else:
            raise ValueError("Unexpected XLSX data row")
    csv_by_serial = {
        r["original"][0]: r["original"] for r in records if r["kind"] == "detail"
    }
    differences = Counter()
    matched = 0
    for _, values in details:
        other = csv_by_serial.get(values[0])
        if other is None:
            continue
        matched += 1
        for field, left, right in zip(headers, values, other):
            same = (
                money(left) == money(right)
                if "₹" in field and left.strip() and right.strip()
                else left == right
            )
            if not same:
                differences[field] += 1
    profile = []
    for col, field in enumerate(headers):
        vals = [values[col] for _, values in details]
        nonblank = [v for v in vals if not is_missing(field, v)]
        invalid = 0
        for value in nonblank:
            try:
                clean_value(field, value)
            except ValueError:
                invalid += 1
        profile.append(
            {
                "field": field,
                "null_count": len(vals) - len(nonblank),
                "null_percent": round(100 * (len(vals) - len(nonblank)) / len(vals), 6)
                if vals
                else None,
                "unique_non_null_raw": len(set(nonblank)),
                "examples": list(dict.fromkeys(nonblank))[:3],
                "invalid_count": invalid,
            }
        )
    amount_index = next(i for i, h in enumerate(headers) if "₹" in h)
    amount_sum = sum(
        (
            Decimal(money(v[amount_index]))
            for _, v in details
            if v[amount_index].strip()
        ),
        Decimal(0),
    )
    return {
        "file": path.name,
        "sheet": "Sheet1",
        "header_row": rows[1][0],
        "detail_rows": len(details),
        "first_detail_sheet_row": details[0][0] if details else None,
        "last_detail_sheet_row": details[-1][0] if details else None,
        "listed_amount_sum_inr": str(amount_sum),
        "summaries": summaries,
        "overlapping_serials": matched,
        "cell_differences_by_field": dict(differences),
        "profile": profile,
        "comparison_caveat": "Serial alignment within these exports only, not a cross-report join",
    }


def markdown_cell(value):
    return (
        str(value)
        .replace("|", "\\|")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", "\\t")
    )


def run(raw, output, dictionary):
    raw, output, dictionary = raw.resolve(), output.resolve(), dictionary.resolve()
    if output == raw or output.is_relative_to(raw) or dictionary.is_relative_to(raw):
        raise ValueError(
            "Inspection outputs must not be written inside the raw directory"
        )
    if dictionary.suffix != ".md":
        raise ValueError("Dictionary output must be a Markdown file")
    if not any(raw.glob("*.csv")):
        raise ValueError("No CSV reports found; refusing an empty inspection")
    inventory, reports, work_sets = [], [], {}
    missing = []
    for name in REPORTS:
        for extension in ("csv", "xlsx", "pdf"):
            path = raw / f"{name}.{extension}"
            if path.exists():
                inventory.append(
                    {
                        "file": path.name,
                        "sha256": digest(path.read_bytes()),
                        "bytes": path.stat().st_size,
                    }
                )
            else:
                missing.append(path.name)
        csv_path = raw / f"{name}.csv"
        if not csv_path.exists():
            continue
        target = ingest(csv_path, output)
        report, records = inspect_csv(csv_path)
        report["output_directory"] = target.name
        report["xlsx"] = (
            xlsx_audit(raw / f"{name}.xlsx", report, records)
            if (raw / f"{name}.xlsx").exists()
            else None
        )
        work_sets[name] = {
            r["derived"]["work_id"] for r in records if "work_id" in r["derived"]
        }
        reports.append(report)
    joins = [
        {
            "left": a,
            "right": b,
            "shared_normalised_ids": len(work_sets[a] & work_sets[b]),
            "left_only_ids": len(work_sets[a] - work_sets[b]),
            "right_only_ids": len(work_sets[b] - work_sets[a]),
        }
        for a in work_sets
        for b in work_sets
        if a < b and work_sets[a] and work_sets[b]
    ]
    audit = {
        "files": inventory,
        "missing_files": missing,
        "reports": reports,
        "join_coverage": joins,
    }
    (output / "inspection.json").write_bytes(encode(audit))
    lines = [
        "# Measured data dictionary",
        "",
        "Generated by `python -m backend.inspect_exports`. Raw files are not changed.",
        "",
        "CSV is the staging source. XLSX is inspected independently, never appended to CSV. PDF files are retained as reference, not parsed into observations.",
        "",
        "Null means empty/whitespace or N/A in Image. Denominator: detail rows only, excluding title/header/footer and rejected-width rows. Unique counts use exact non-null raw strings, before cleaning. Dates are inferred from dd-MMM-yyyy; money is INR decimal, stored as strings without binary floating-point conversion. Meanings are inferred from actual labels and values, not an official field specification.",
        "",
        "Missing files: " + ", ".join(missing),
        "",
    ]
    for report in reports:
        lines += [
            f"## {report['source_file']}",
            "",
            f"Detail rows: {report['detail_rows']}; rejected: {report['rejected_rows']}; summary rows: {report['summary_rows']}. SHA-256: `{report['sha256']}`.",
            "",
            f"Listed amount sum: INR {report['listed_amount_sum_inr']}; reported totals: {', '.join(str(v) for v in report['reported_totals_inr'])}; reconciles: {report['total_reconciles']}. Coverage remains unverified.",
            "",
            f"Normalised distinct work IDs: {report['distinct_work_ids']}; repeated IDs: {report['repeated_work_ids']}; exact duplicate detail rows ignoring serial: {report['exact_duplicate_detail_rows']}.",
            "",
            "| Field | Inferred meaning | Type | Null % (count) | Unique non-null | Examples | Anomaly usefulness | Quality concerns |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for p in report["profile"]:
            meaning, use, concern = MEANINGS[p["field"]]
            examples = "; ".join(p["examples"][:2])
            lines.append(
                "| "
                + " | ".join(
                    markdown_cell(v)
                    for v in [
                        p["field"],
                        meaning,
                        p["datatype"],
                        f"{p['null_percent']} ({p['null_count']})",
                        p["unique_non_null_raw"],
                        examples,
                        use,
                        concern + f"; invalid typed values: {p['invalid_count']}",
                    ]
                )
                + " |"
            )
        lines += [
            "",
            "Validation counts: "
            + json.dumps(report["issue_counts"], sort_keys=True)
            + ".",
            "",
        ]
        xlsx = report["xlsx"]
        if xlsx:
            lines += [
                f"### Excel counterpart: {xlsx['file']}",
                "",
                f"Sheet1, header row 2; {xlsx['detail_rows']} detail rows. Sum INR {xlsx['listed_amount_sum_inr']}. Overlapping serials: {xlsx['overlapping_serials']}; cell differences: {json.dumps(xlsx['cell_differences_by_field'])}.",
                "",
                "Same field meanings/types/cautions as above; measurements below apply independently to XLSX. Text/numeric cell values are read without evaluating formulas.",
                "",
                "| Field | Null % (count) | Unique non-null | Examples | Invalid typed values |",
                "| --- | --- | --- | --- | --- |",
            ]
            for p in xlsx["profile"]:
                lines.append(
                    "| "
                    + " | ".join(
                        markdown_cell(v)
                        for v in [
                            p["field"],
                            f"{p['null_percent']} ({p['null_count']})",
                            p["unique_non_null_raw"],
                            "; ".join(p["examples"][:2]),
                            p["invalid_count"],
                        ]
                    )
                    + " |"
                )
            lines += [""]
    lines += [
        "## Cross-report linkage coverage",
        "",
        "Counts use parsed, whitespace-normalised Work IDs only. No rows are merged, no names are fuzzy-matched, and missing matches do not imply wrongdoing.",
        "",
        "| Left | Right | Shared IDs | Left only | Right only |",
        "| --- | --- | --- | --- | --- |",
    ]
    for join in joins:
        lines.append(
            f"| {join['left']} | {join['right']} | {join['shared_normalised_ids']} | {join['left_only_ids']} | {join['right_only_ids']} |"
        )
    dictionary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "reports": [
                    {
                        "file": r["source_file"],
                        "rows": r["detail_rows"],
                        "sum": r["listed_amount_sum_inr"],
                        "xlsx_rows": r["xlsx"]["detail_rows"] if r["xlsx"] else None,
                    }
                    for r in reports
                ],
                "joins": joins,
                "missing": missing,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    args = parser.parse_args()
    run(args.raw, args.output, args.dictionary)
