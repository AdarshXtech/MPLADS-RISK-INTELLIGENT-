"""Synthetic fixtures only; not official MPLADS observations."""

import csv
import json

import pytest

from backend.ingest import REPORTS, clean_value, ingest, inspect_csv, money


def source(tmp_path, rows, name="Works Sanctioned"):
    raw = tmp_path / "raw"
    raw.mkdir(exist_ok=True)
    path = raw / f"{name}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(REPORTS[name])
        writer.writerows(rows)
    return path


def work(serial="1", amount="10.25"):
    return [
        serial,
        "Normal/Others",
        "WS/\t MP1/2024-2025/123-Road",
        "Test State",
        "Test IDA",
        "Synthetic MP",
        "Test Constituency",
        "Synthetic description\nsecond line",
        "01-Jan-2025",
        "02-Jan-2025",
        amount,
        "Sanction",
    ]


def footer(amount="10.25"):
    return ["Grand Total"] + ["\u00a0"] * 10 + [amount]


def test_lossless_reproducible_and_footer(tmp_path):
    path = source(tmp_path, [work(), footer()])
    original = path.read_bytes()
    first = ingest(path, tmp_path / "processed")
    before = {f.name: f.read_bytes() for f in first.iterdir()}
    assert ingest(path, tmp_path / "processed") == first
    assert before == {f.name: f.read_bytes() for f in first.iterdir()}
    assert path.read_bytes() == original
    report, records = inspect_csv(path)
    assert report["detail_rows"] == 1 and report["total_reconciles"]
    assert records[0]["original"] == work()
    assert records[0]["derived"]["work_id"] == "WS/MP1/2024-2025/123"
    assert records[0]["line_start"] == 2 and records[0]["line_end"] == 3
    assert records[1]["kind"] == "summary" and not records[1]["cleaned"]


@pytest.mark.parametrize(
    "value", ["NaN", "Infinity", "-1", "1e4", "1,2,3", "1.001", "", "₹100"]
)
def test_invalid_money(value):
    with pytest.raises(ValueError):
        money(value)


@pytest.mark.parametrize(
    "value,expected",
    [("1,23,456.78", "123456.78"), ("123,456.78", "123456.78"), ("0", "0")],
)
def test_exact_money(value, expected):
    assert money(value) == expected


def test_invalid_and_missing_values_retained(tmp_path):
    invalid = work(amount="NaN")
    invalid[8] = "31-Feb-2025"
    invalid[3] = " "
    report, records = inspect_csv(source(tmp_path, [invalid, ["short"], footer()]))
    assert records[0]["original"] == invalid
    assert records[0]["cleaned"]["Sanction Amount ( ₹ )"] is None
    assert records[0]["cleaned"]["State"] is None
    assert report["rejected_rows"] == 1
    assert report["issue_counts"]["invalid_value"] == 2
    assert not report["total_reconciles"]


def test_no_false_zero_or_automatic_deduplication(tmp_path):
    report, records = inspect_csv(source(tmp_path, [work(), work(), footer("20.50")]))
    assert report["detail_rows"] == 2
    assert report["duplicate_serials"] == [1]
    assert report["repeated_work_ids"] == 1
    assert len(records) == 3


def test_schema_and_output_protection(tmp_path):
    path = source(tmp_path, [work()])
    with pytest.raises(ValueError, match="separate"):
        ingest(path, path.parent)
    target = ingest(path, tmp_path / "processed")
    (target / "report.json").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="refusing overwrite"):
        ingest(path, tmp_path / "processed")
    path.write_text("wrong,header\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unexpected columns"):
        inspect_csv(path)


def test_dates_and_image_marker():
    assert clean_value("Completion Date", "29-Feb-2024") == "2024-02-29"
    assert clean_value("Sanction Date", "NA") is None
    assert clean_value("Image", "N/A") is None
    assert clean_value("Image", "Images") == "Images"
    with pytest.raises(ValueError):
        clean_value("Completion Date", "02/03/2025")


def test_invalid_id_and_date_order(tmp_path):
    row = work()
    row[2] = "Unrecognised work"
    row[9] = "01-Jan-2024"
    report, records = inspect_csv(source(tmp_path, [row]))
    assert report["issue_counts"]["invalid_work_id"] == 1
    assert report["issue_counts"]["date_order"] == 1
    assert not records[0]["derived"]


def test_multiple_totals_and_invalid_summary(tmp_path):
    report, records = inspect_csv(source(tmp_path, [work(), footer(), footer("bad")]))
    assert not report["total_reconciles"]
    assert report["summary_rows"] == 2
    assert report["issue_counts"]["invalid_summary"] == 1
    assert len(records) == 3


def test_cli_review_exit_code(tmp_path, monkeypatch):
    from backend.ingest import main

    path = source(tmp_path, [work()])
    monkeypatch.setattr(
        "sys.argv", ["ingest", str(path), "--output", str(tmp_path / "processed")]
    )
    assert main() == 2


def test_unknown_status_and_no_payment_conflation(tmp_path):
    name = "Expenditure on Completed and On-going Works as on Date"
    rows = [
        [
            "1",
            "Test",
            "Road",
            "WS/MP1/2024-2025/123",
            "Test IDA",
            "Synthetic MP",
            "Test",
            "01-Jan-2025",
            "Synthetic Vendor",
            "Payment In-Progress",
            "10",
        ],
        [
            "2",
            "Test",
            "Road",
            "WS/MP1/2024-2025/123",
            "Test IDA",
            "Synthetic MP",
            "Test",
            "02-Jan-2025",
            "Synthetic Vendor",
            "Unexpected",
            "20",
        ],
    ]
    report, _ = inspect_csv(source(tmp_path, rows, name))
    assert report["amount_by_payment_status_inr"] == {
        "Payment In-Progress": "10",
        "Unexpected": "20",
    }
    assert report["issue_counts"]["unknown_payment_status"] == 1
    assert not report["total_reconciles"]


def test_json_output_preserves_decimal_string(tmp_path):
    path = source(tmp_path, [work(amount="9999999999999999.99")])
    output = ingest(path, tmp_path / "processed")
    record = json.loads((output / "records.jsonl").read_text(encoding="utf-8"))
    assert record["cleaned"]["Sanction Amount ( ₹ )"] == "9999999999999999.99"


def test_allocation_report_preserves_missing_amount(tmp_path):
    name = "Allocated Limit for Honble MPs"
    row = ["1", "Test State", "Synthetic MP", "Test Constituency", ""]
    report, records = inspect_csv(source(tmp_path, [row], name))
    assert report["detail_rows"] == 1
    assert report["issue_counts"] == {"missing_value": 1}
    assert records[0]["cleaned"]["Allocated AMOUNT ( ₹ )"] is None


def test_calamity_report_parses_consent_without_work_link(tmp_path):
    name = "Amount consented for Calamity"
    row = [
        "1",
        "Synthetic Type",
        "Synthetic Event",
        "Synthetic MP",
        "07-Dec-2025",
        "10.25",
    ]
    report, records = inspect_csv(source(tmp_path, [row], name))
    assert report["issue_counts"] == {}
    assert records[0]["cleaned"]["Date of Consent"] == "2025-12-07"
    assert records[0]["cleaned"]["Consent Amount ( ₹ )"] == "10.25"
    assert records[0]["derived"] == {}


def test_recommended_report_retains_unsanctioned_and_linked_rows(tmp_path):
    name = "Works Recommended"
    unsanctioned = [
        "1",
        "Normal/Others",
        "NA-Synthetic work type",
        "Test State",
        "Test IDA",
        "Synthetic MP",
        "Test Constituency",
        "Synthetic description",
        "01-Jan-2025",
        "100",
        "NA",
    ]
    linked = unsanctioned.copy()
    linked[0] = "2"
    linked[2] = "WS/ MP1/2024-2025/123-Synthetic work type"
    linked[9] = "200"
    linked[10] = "02-Jan-2025"
    summary = ["Grand Total"] + ["\u00a0"] * 9 + ["300"]
    report, records = inspect_csv(
        source(tmp_path, [unsanctioned, linked, summary], name)
    )
    assert report["total_reconciles"]
    assert records[0]["cleaned"]["Sanction Date"] is None
    assert records[0]["derived"] == {"work_type": "Synthetic work type"}
    assert records[1]["derived"] == {
        "work_id": "WS/MP1/2024-2025/123",
        "work_type": "Synthetic work type",
    }
