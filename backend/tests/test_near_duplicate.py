"""Synthetic examples for read-only near-match screening."""

from backend.near_duplicate import near_duplicate_pairs


def record(number, description, *, amount="100", work_id=None, ida="Test agency"):
    return {
        "record_number": number,
        "cleaned": {
            "Work category": "Test category",
            "Work description": description,
            "State": "Test State",
            "Constituency": "Test Constituency",
            "IDA": ida,
            "Sanction Date": "2025-01-02",
            "Sanction Amount ( ₹ )": amount,
        },
        "derived": {
            "work_id": work_id or f"WS/MP1/2024-2025/{number}",
            "work_type": "Test road work",
        },
    }


def test_near_match_is_explainable_and_deterministic():
    rows = [
        record(1, "Construction of community hall at Test Village"),
        record(2, "Construction of comunity hall at Test Village"),
    ]
    first = near_duplicate_pairs(rows)
    assert near_duplicate_pairs(reversed(rows)) == first
    assert len(first) == 1
    assert 90 <= first[0]["description_similarity"] < 100
    assert "Sanction Amount ( ₹ )" in first[0]["exact_fields"]
    assert "fraud" not in first[0]["interpretation"].lower()


def test_exact_description_is_left_to_existing_detector():
    assert near_duplicate_pairs([record(1, "Same work"), record(2, "Same work")]) == []


def test_missing_or_conflicting_context_is_not_scored():
    base = record(1, "Construction of community hall at Test Village")
    assert (
        near_duplicate_pairs(
            [
                base,
                record(
                    2, "Construction of comunity hall at Test Village", amount="200"
                ),
            ]
        )
        == []
    )
    assert (
        near_duplicate_pairs(
            [
                base,
                record(
                    2,
                    "Construction of comunity hall at Test Village",
                    ida="Other agency",
                ),
            ]
        )
        == []
    )
    assert (
        near_duplicate_pairs(
            [
                base,
                record(
                    2,
                    "Construction of comunity hall at Test Village",
                    work_id=base["derived"]["work_id"],
                ),
            ]
        )
        == []
    )
    assert near_duplicate_pairs([base, record(2, "", amount="100")]) == []


def test_different_phases_and_quantities_are_not_near_matches():
    assert (
        near_duplicate_pairs(
            [record(1, "Repair of hall part-I"), record(2, "Repair of hall part-II")]
        )
        == []
    )
    assert (
        near_duplicate_pairs(
            [
                record(1, "Install 2 solar lights at Village"),
                record(2, "Install 4 solar lights at Village"),
            ]
        )
        == []
    )
