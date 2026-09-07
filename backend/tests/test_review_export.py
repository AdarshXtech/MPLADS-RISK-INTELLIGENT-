"""Synthetic review-export fixtures only; no official MPLADS observations."""

import csv
import io

import pytest

from backend.review_export import FIELDS, build_rows, encode_csv, write_once


def test_review_row_contains_evidence_and_blank_human_fields(tmp_path):
    records = [
        {
            "source_sha256": "synthetic-sanction",
            "parser_version": "test",
            "record_number": number,
            "cleaned": {
                "Work category": "Synthetic category",
                "Hon'ble Members of Parliament": "Synthetic MP",
            },
            "derived": {"work_id": f"WS/MP1/2025-2026/{number}"},
        }
        for number in (1, 2)
    ]
    result = {
        "result_id": "synthetic-candidate",
        "detector_id": "duplicate_work_candidate",
        "evidence": {
            "match_type": "synthetic exact match",
            "matched_values": {
                "Work description": "Synthetic description",
                "work_type": "Synthetic work type",
                "State": "Test State",
                "Constituency": "Test Constituency",
                "IDA": "Test IDA",
                "Sanction Date": "2025-01-02",
                "Sanction Amount ( ₹ )": "100",
            },
        },
        "source_records": [
            {
                "source_sha256": record["source_sha256"],
                "parser_version": record["parser_version"],
                "record_number": record["record_number"],
                "work_id": record["derived"]["work_id"],
            }
            for record in records
        ],
        "verification_step": "Verify synthetic evidence.",
        "limitations": ["Synthetic limitation."],
    }
    recommendation = {
        "source_sha256": "synthetic-recommendation",
        "parser_version": "test",
        "record_number": 10,
        "cleaned": {
            "RECOMMENDED AMOUNT   ( ₹ )": "90",
            "Recommended date": "2025-01-01",
        },
        "derived": {"work_id": "WS/MP1/2025-2026/1"},
    }
    rows = build_rows(
        [result], records, {recommendation["derived"]["work_id"]: recommendation}
    )
    assert len(rows) == 1
    assert list(rows[0]) == FIELDS
    assert rows[0]["group_size"] == 2
    assert rows[0]["recommended_amounts_by_work_id"].endswith(": 90")
    assert rows[0]["review_decision"] == ""

    content = encode_csv(rows)
    assert content.startswith(b"\xef\xbb\xbf")
    parsed = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    assert len(parsed) == 1 and parsed[0]["candidate_group_id"] == "synthetic-candidate"

    rows[0]["reviewer_notes"] = "=unsafe"
    safe = next(csv.DictReader(io.StringIO(encode_csv(rows).decode("utf-8-sig"))))
    assert safe["reviewer_notes"] == "'=unsafe"

    path = tmp_path / "review.csv"
    assert write_once(path, content)
    assert not write_once(path, content)
    with pytest.raises(ValueError, match="refusing overwrite"):
        write_once(path, content + b"changed")
