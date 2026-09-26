"""Synthetic detector fixtures only; no official MPLADS observations."""

import os
from uuid import uuid4

import pytest

from backend.detectors import (
    DDL,
    build_run,
    detect,
    duplicate_work_candidates,
    locality_duplicate_candidates,
    peer_cost_candidates,
    stage_run,
)


def record(number, *, work_id=None, amount="100", description="Synthetic road"):
    return {
        "source_sha256": "synthetic-source",
        "parser_version": "test",
        "record_number": number,
        "cleaned": {
            "Work description": description,
            "Work category": "Synthetic category",
            "State": "Test State",
            "Constituency": "Test Constituency",
            "IDA": "Test IDA",
            "Sanction Date": "2025-01-02",
            "Sanction Amount ( ₹ )": amount,
        },
        "derived": {
            "work_id": work_id or f"WS/MP1/2024-2025/{number}",
            "work_type": "Synthetic work type",
        },
    }


def test_exact_duplicate_candidate_is_explainable_and_deterministic():
    records = [record(1), record(2)]
    first = duplicate_work_candidates(records)
    assert duplicate_work_candidates(list(reversed(records))) == first
    assert len(first) == 1
    candidate = first[0]
    assert candidate["detector_id"] == "duplicate_work_candidate"
    assert candidate["severity"] == "review"
    assert candidate["confidence"] == "1"
    assert len(candidate["source_records"]) == 2
    assert any("not proof" in limitation for limitation in candidate["limitations"])


def test_duplicate_rule_requires_every_field_and_different_ids():
    missing = record(2)
    missing["cleaned"]["IDA"] = None
    same_id = record(3, work_id="WS/MP1/2024-2025/1")
    assert duplicate_work_candidates([record(1), missing]) == []
    assert duplicate_work_candidates([record(1), same_id]) == []


def locality(number, **overrides):
    return {
        "state": "Test State",
        "district": "Test District",
        "constituency": "Test Constituency",
        "block_tehsil": "Test Block",
        "ward_village": "Test Ward",
        "location_status": "ADMINISTRATIVE_ONLY",
        "location_source": "Synthetic reviewed fixture",
        "verified_address_text": None,
        "latitude": None,
        "longitude": None,
        "last_verified_at": None,
        **overrides,
    }


def locations_for(*records, overrides=None):
    return {
        (
            item["source_sha256"],
            item["parser_version"],
            item["record_number"],
        ): locality(
            item["record_number"], **(overrides or {}).get(item["record_number"], {})
        )
        for item in records
    }


def test_same_locality_with_matching_evidence_creates_candidate():
    left = record(1, description="Synthetic pathway upgrade at ward four")
    right = record(2, description="Synthetic pathway upgrade near ward four")
    candidates = locality_duplicate_candidates(
        [left, right], locations_for(left, right)
    )
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["detector_id"] == "locality_duplicate_candidate"
    assert candidate["evidence"]["locality_evidence"]["level"] == "ward_village"
    signals = candidate["evidence"]["supporting_signals"]
    assert signals
    assert any(signal["signal"] == "same_sanction_amount" for signal in signals)


def test_nearby_records_need_description_and_supporting_evidence():
    left = record(1, description="Synthetic culvert construction")
    right = record(2, description="Synthetic library renovation")
    locations = locations_for(
        left,
        right,
        overrides={
            1: {
                "location_status": "VERIFIED_COORDINATES",
                "latitude": 20.0000,
                "longitude": 78.0000,
            },
            2: {
                "location_status": "VERIFIED_COORDINATES",
                "latitude": 20.0001,
                "longitude": 78.0001,
            },
        },
    )
    assert locality_duplicate_candidates([left, right], locations) == []


def test_administrative_fallback_is_explicit_when_coordinates_absent():
    left = record(1, description="Synthetic pathway upgrade at ward four")
    right = record(2, description="Synthetic pathway upgrade near ward four")
    candidate = locality_duplicate_candidates(
        [left, right], locations_for(left, right)
    )[0]
    assert candidate["evidence"]["spatial_evidence"]["distance_metres"] is None
    assert any("not sufficiently verified" in item for item in candidate["limitations"])


def test_locality_detector_excludes_unrelated_work_types():
    left = record(1, description="Synthetic pathway upgrade at ward four")
    right = record(2, description="Synthetic pathway upgrade near ward four")
    right["derived"]["work_type"] = "Different synthetic work type"
    assert (
        locality_duplicate_candidates([left, right], locations_for(left, right)) == []
    )


def test_locality_detector_version_does_not_change_exact_v1_results():
    records = [record(1), record(2)]
    exact = duplicate_work_candidates(records)
    _, results = build_run([], records)
    assert exact[0]["detector_id"] == "duplicate_work_candidate"
    assert exact[0]["result_id"] in {item["result_id"] for item in results}
    assert len(detect(records)) >= len(exact)


def test_peer_cost_threshold_and_minimum_group():
    peers = [
        record(number, description=f"Synthetic work {number}")
        for number in range(1, 20)
    ]
    peers.append(record(20, amount="200", description="Different synthetic work"))
    candidates = peer_cost_candidates(peers)
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["detector_id"] == "peer_sanction_cost"
    assert candidate["evidence"] == {
        "sanction_amount_inr": "200",
        "peer_median_inr": "100",
        "amount_to_median_ratio": "2.0000",
        "peer_count": 20,
        "threshold_multiplier": "2",
    }
    assert peer_cost_candidates(peers[:-1]) == []


def test_peer_cost_rule_is_not_enabled_for_reviewable_runs():
    peers = [
        record(number, description=f"Synthetic work {number}")
        for number in range(1, 20)
    ]
    peers.append(record(20, amount="200", description="Different synthetic work"))
    assert detect(peers) == []


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not configured"
)
def test_postgres_detector_run_is_immutable_and_idempotent():
    import psycopg
    from psycopg import sql

    schema = "test_detector_" + uuid4().hex
    batches = [
        {
            "source_file": "Synthetic.csv",
            "source_sha256": "synthetic-source",
            "parser_version": "test",
        }
    ]
    run, results = build_run(batches, [record(1), record(2)])
    with psycopg.connect(
        os.environ["TEST_DATABASE_URL"], autocommit=True, connect_timeout=5
    ) as connection:
        with connection.transaction(force_rollback=True):
            connection.execute(
                sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema))
            )
            connection.execute(
                sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema))
            )
            connection.execute(DDL)
            assert stage_run(connection, run, results)
            assert not stage_run(connection, run, results)
            assert connection.execute(
                "SELECT count(*) FROM mplads_detector_result"
            ).fetchone()[0] == len(results)
        assert (
            connection.execute(
                "SELECT count(*) FROM pg_namespace WHERE nspname=%s", (schema,)
            ).fetchone()[0]
            == 0
        )
