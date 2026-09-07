"""Investigation workflow tests use synthetic detector records only."""

import csv
import io
import json
import os
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.detectors import DDL as DETECTOR_DDL
from backend.detectors import DETECTOR_CONFIGURATION, build_run, stage_run
from backend.investigations import (
    DDL,
    ReviewEventCreate,
    add_review_event,
    candidate_detail,
    export_candidates,
    investigation_summary,
    list_candidates,
)


def record(number):
    amount_field = DETECTOR_CONFIGURATION["duplicate_work_candidate"]["fields"][-1]
    return {
        "source_sha256": "synthetic-source",
        "parser_version": "test",
        "record_number": number,
        "cleaned": {
            "Work description": "Synthetic community hall",
            "Work category": "Synthetic category",
            "State": "Test State",
            "Constituency": "Test Constituency",
            "IDA": "Test Agency",
            "Sanction Date": "2025-01-02",
            amount_field: "100",
        },
        "derived": {
            "work_id": f"SYNTHETIC/{number}",
            "work_type": "Synthetic work type",
        },
    }


@pytest.fixture
def investigation_connection():
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL not configured")
    import psycopg
    from psycopg import sql
    from psycopg.types.json import Jsonb

    schema = "test_investigation_" + uuid4().hex
    with (
        psycopg.connect(os.environ["TEST_DATABASE_URL"], autocommit=True) as connection,
        connection.transaction(force_rollback=True),
    ):
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        connection.execute(
            sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema))
        )
        connection.execute(DETECTOR_DDL)
        records = [record(1), record(2)]
        run, results = build_run(
            [
                {
                    "source_file": "Synthetic.csv",
                    "source_sha256": "synthetic-source",
                    "parser_version": "test",
                }
            ],
            records,
        )
        stage_run(connection, run, results)
        connection.execute(
            "CREATE TABLE mplads_source_record (source_sha256 text, parser_version text, "
            "record_number integer, cleaned_values jsonb, derived_values jsonb, "
            "validation_issues jsonb, PRIMARY KEY(source_sha256,parser_version,record_number))"
        )
        for item in records:
            connection.execute(
                "INSERT INTO mplads_source_record VALUES (%s,%s,%s,%s,%s,%s)",
                (
                    item["source_sha256"],
                    item["parser_version"],
                    item["record_number"],
                    Jsonb(item["cleaned"]),
                    Jsonb(item["derived"]),
                    Jsonb([]),
                ),
            )
        connection.execute(DDL)
        yield connection, results[0]["result_id"]


def test_queue_lists_real_detector_evidence(investigation_connection):
    connection, result_id = investigation_connection
    page = list_candidates(connection, 1, 20, "community hall", "Test State", "NEW")
    assert page.total == 1
    assert page.items[0].result_id == result_id
    assert page.items[0].group_size == 2
    assert page.items[0].status == "NEW"
    assert len(candidate_detail(connection, result_id).source_records) == 2


def test_summary_is_derived_from_latest_append_only_status(investigation_connection):
    connection, result_id = investigation_connection
    initial = investigation_summary(connection)
    assert initial.model_dump() == {
        "total_candidates": 1,
        "new": 1,
        "under_review": 0,
        "verification_requested": 0,
        "resolved": 0,
        "dismissed": 0,
    }
    add_review_event(
        connection,
        result_id,
        ReviewEventCreate(expected_status="NEW", target_status="UNDER_REVIEW"),
        "synthetic-reviewer",
    )
    reviewed = investigation_summary(connection)
    assert reviewed.total_candidates == 1
    assert reviewed.new == 0
    assert reviewed.under_review == 1


def test_review_history_is_append_only(investigation_connection):
    connection, result_id = investigation_connection
    started = add_review_event(
        connection,
        result_id,
        ReviewEventCreate(expected_status="NEW", target_status="UNDER_REVIEW"),
        "synthetic-reviewer",
    )
    assert started.status == "UNDER_REVIEW"
    resolved = add_review_event(
        connection,
        result_id,
        ReviewEventCreate(
            expected_status="UNDER_REVIEW",
            target_status="RESOLVED",
            decision="SEPARATE_WORKS",
            notes="Synthetic evidence reviewed",
        ),
        "synthetic-reviewer",
    )
    assert resolved.status == "RESOLVED"
    assert len(resolved.history) == 2
    assert resolved.history[0].decision == "SEPARATE_WORKS"


def test_dismissal_requires_decision_and_reason(investigation_connection):
    connection, result_id = investigation_connection
    add_review_event(
        connection,
        result_id,
        ReviewEventCreate(expected_status="NEW", target_status="UNDER_REVIEW"),
        "synthetic-reviewer",
    )
    with pytest.raises(HTTPException, match="dismissal reason"):
        add_review_event(
            connection,
            result_id,
            ReviewEventCreate(
                expected_status="UNDER_REVIEW",
                target_status="DISMISSED",
                decision="SEPARATE_WORKS",
            ),
            "synthetic-reviewer",
        )


def test_disallowed_transition_is_rejected(investigation_connection):
    connection, result_id = investigation_connection
    with pytest.raises(HTTPException, match="not permitted"):
        add_review_event(
            connection,
            result_id,
            ReviewEventCreate(
                expected_status="NEW",
                target_status="RESOLVED",
                decision="SEPARATE_WORKS",
            ),
            "synthetic-reviewer",
        )


def test_export_matches_filters_preserves_provenance_and_latest_review(
    investigation_connection,
):
    connection, result_id = investigation_connection
    add_review_event(
        connection,
        result_id,
        ReviewEventCreate(
            expected_status="NEW",
            target_status="UNDER_REVIEW",
            notes="  =1+1",
            documents_checked="Synthetic document, with comma\nand new line",
        ),
        "synthetic-reviewer",
    )
    content = export_candidates(
        connection, "community hall", "Test State", "UNDER_REVIEW"
    )
    assert content.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    assert len(rows) == 1
    row = rows[0]
    assert row["result_id"] == result_id
    assert row["status"] == "UNDER_REVIEW"
    assert row["notes"] == "'  =1+1"
    assert row["documents_checked"] == "Synthetic document, with comma\nand new line"
    assert row["detector_version"] == "1"
    assert row["run_id"]
    assert len(json.loads(row["source_records"])) == 2
    assert "not probability" in row["confidence_meaning"]
    empty = export_candidates(connection, "", "", "NEW")
    assert list(csv.DictReader(io.StringIO(empty.decode("utf-8-sig")))) == []
    assert (
        connection.execute("SELECT count(*) FROM mplads_review_event").fetchone()[0]
        == 1
    )


def test_export_includes_all_pages_and_search_is_literal(investigation_connection):
    connection, result_id = investigation_connection
    connection.execute(
        "INSERT INTO mplads_detector_result SELECT run_id, result_id || i::text, "
        "detector_id, detector_name, severity, confidence, explanation, verification_step, "
        "fields_used, evidence, source_records, limitations FROM mplads_detector_result, "
        "generate_series(1,24) i WHERE result_id=%s",
        (result_id,),
    )
    assert len(list_candidates(connection, 1, 20, "", "", "").items) == 20
    exported = export_candidates(connection, "", "", "")
    assert len(list(csv.DictReader(io.StringIO(exported.decode("utf-8-sig"))))) == 25
    for query in ["%", "__no_such_literal__", "' OR 1=1 --"]:
        assert list_candidates(connection, 1, 20, query, "", "").total == 0
        assert (
            list(
                csv.DictReader(
                    io.StringIO(
                        export_candidates(connection, query, "", "").decode("utf-8-sig")
                    )
                )
            )
            == []
        )


def test_export_refuses_truncation(investigation_connection, monkeypatch):
    from backend import investigations

    connection, _ = investigation_connection
    monkeypatch.setattr(investigations, "EXPORT_LIMIT", 0)
    with pytest.raises(HTTPException, match="Narrow the filters"):
        export_candidates(connection, "", "", "")


def test_queue_and_export_use_selected_stable_sort(investigation_connection):
    connection, result_id = investigation_connection
    large_id = result_id + "-large"
    connection.execute(
        "INSERT INTO mplads_detector_result "
        "SELECT run_id, %s, detector_id, detector_name, severity, confidence, "
        "explanation, verification_step, fields_used, "
        "jsonb_set(evidence, '{matched_record_count}', '4'::jsonb), "
        "source_records || source_records, limitations "
        "FROM mplads_detector_result WHERE result_id=%s",
        (large_id, result_id),
    )

    smallest = list_candidates(connection, 1, 20, "", "", "", "group_smallest")
    largest = list_candidates(connection, 1, 20, "", "", "", "group_largest")
    assert smallest.items[0].result_id == result_id
    assert largest.items[0].result_id == large_id
    assert largest.items[0].group_size == 4

    exported = list(
        csv.DictReader(
            io.StringIO(
                export_candidates(connection, "", "", "", "group_largest").decode(
                    "utf-8-sig"
                )
            )
        )
    )
    assert exported[0]["result_id"] == large_id

    add_review_event(
        connection,
        result_id,
        ReviewEventCreate(expected_status="NEW", target_status="UNDER_REVIEW"),
        "synthetic-reviewer",
    )
    recent = list_candidates(connection, 1, 20, "", "", "", "recently_reviewed")
    assert recent.items[0].result_id == result_id
