"""Read-only near-match screening for sanctioned works; not a fraud model."""

import argparse
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

from backend.detectors import normalise_text
from backend.ingest import inspect_csv

MODEL_VERSION = "exploratory-1"
MIN_DESCRIPTION_SIMILARITY = 0.90
BLOCK_FIELDS = (
    "Work category",
    "State",
    "Constituency",
    "IDA",
    "Sanction Date",
    "Sanction Amount ( ₹ )",
)


def _block(record):
    cleaned, derived = record["cleaned"], record["derived"]
    work_id = derived.get("work_id")
    description = normalise_text(cleaned.get("Work description"))
    key = tuple(normalise_text(cleaned.get(field)) for field in BLOCK_FIELDS) + (
        normalise_text(derived.get("work_type")),
    )
    if not work_id or not description or not all(key):
        return None
    return key, description


def near_duplicate_pairs(records):
    """Return high text-similarity pairs with exact administrative/financial context."""
    blocks = defaultdict(list)
    for record in records:
        prepared = _block(record)
        if prepared:
            key, description = prepared
            blocks[key].append((record, description))

    pairs = []
    for entries in blocks.values():
        for (left, left_text), (right, right_text) in combinations(entries, 2):
            left_id, right_id = left["derived"]["work_id"], right["derived"]["work_id"]
            if left_id == right_id or left_text == right_text:
                continue  # Exact-description groups belong to the existing detector.
            if sorted(re.findall(r"\d+", left_text)) != sorted(
                re.findall(r"\d+", right_text)
            ):
                continue  # Quantities or location numbers may identify distinct works.
            phase = r"\b(?:part|phase|stage|bit)\s+(?:\d+|[ivx]+)\b"
            if re.findall(phase, left_text) != re.findall(phase, right_text):
                continue  # Differently named phases are not near-duplicate evidence.
            similarity = SequenceMatcher(
                None, left_text, right_text, autojunk=False
            ).ratio()
            if similarity < MIN_DESCRIPTION_SIMILARITY:
                continue
            ordered = sorted(
                (left, right), key=lambda record: record["derived"]["work_id"]
            )
            pairs.append(
                {
                    "description_similarity": round(similarity * 100, 1),
                    "work_ids": [record["derived"]["work_id"] for record in ordered],
                    "work_descriptions": [
                        record["cleaned"]["Work description"] for record in ordered
                    ],
                    "source_record_numbers": sorted(
                        (left["record_number"], right["record_number"])
                    ),
                    "exact_fields": [
                        *BLOCK_FIELDS,
                        "work_type",
                        "description numbers",
                        "phase markers",
                    ],
                    "model_version": MODEL_VERSION,
                    "interpretation": "Text resemblance only; verify distinct assets and source documents.",
                }
            )
    return sorted(
        pairs,
        key=lambda pair: (
            -pair["description_similarity"],
            pair["source_record_numbers"],
            pair["work_ids"],
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Path to Works Sanctioned.csv")
    parser.add_argument(
        "--show", type=int, default=10, help="Number of top pairs to print"
    )
    args = parser.parse_args()
    if args.show < 0 or args.show > 100:
        parser.error("--show must be between 0 and 100")
    report, records = inspect_csv(args.csv)
    pairs = near_duplicate_pairs(
        record for record in records if record["kind"] == "detail"
    )
    print(
        json.dumps(
            {
                "model_version": MODEL_VERSION,
                "source_sha256": report["sha256"],
                "description_similarity_threshold": MIN_DESCRIPTION_SIMILARITY,
                "candidate_pair_count": len(pairs),
                "top_pairs": pairs[: args.show],
                "fraud_rating": "unavailable: no verified misuse outcomes or sufficient project evidence",
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
