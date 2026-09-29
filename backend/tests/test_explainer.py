"""Grounded synthesis tests use synthetic detector evidence only."""

from backend.explainer import GeneratedSynthesis, synthesise_candidate


def detector_result():
    return {
        "detector_id": "duplicate_work_candidate",
        "detector_name": "Potential duplicate work candidate",
        "explanation": "Two sanctioned records match the configured fields and require verification.",
        "fields_used": ["Work description", "Sanction Amount"],
        "evidence": {
            "matched_record_count": 2,
            "different_work_ids": ["SYNTHETIC/1", "SYNTHETIC/2"],
            "matched_values": {
                "Work description": "Synthetic community hall",
                "Sanction Amount": "100000",
                "Sanction Date": "2025-01-02",
            },
        },
        "verification_step": "Compare the sanction orders and physical asset records.",
        "limitations": ["Precise coordinates are not supplied."],
        "source_records": [
            {
                "record_number": number,
                "work_id": f"SYNTHETIC/{number}",
                "cleaned_values": {
                    "Sanction Amount ( INR )": "100000",
                    "Sanction Date": "2025-01-02",
                    "State": "Test State",
                    "Constituency": "Test Constituency",
                },
                "location": {
                    "state": "Test State",
                    "district": "Test District",
                    "constituency": "Test Constituency",
                    "block_tehsil": None,
                    "ward_village": None,
                    "latitude": None,
                    "longitude": None,
                },
            }
            for number in (1, 2)
        ],
    }


def grounded_response(**changes):
    values = {
        "summary_brief": "SYNTHETIC/1 and SYNTHETIC/2 share the configured sanction evidence of INR 100000 dated 2025-01-02.",
        "primary_concerns": [
            "Separate Work IDs share the configured description and sanction date."
        ],
        "verification_checklist": [
            "Compare both sanction orders and inspect the physical asset records."
        ],
        "data_limitations": ["Precise coordinates are not supplied."],
    }
    values.update(changes)
    return GeneratedSynthesis(**values)


def test_unconfigured_service_uses_deterministic_fallback(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = synthesise_candidate(detector_result())

    assert result.generation_mode == "deterministic_fallback"
    assert result.summary_brief == detector_result()["explanation"]
    assert result.verification_checklist == [detector_result()["verification_step"]]
    assert result.data_limitations == detector_result()["limitations"]


def test_grounded_structured_generation_is_accepted():
    result = synthesise_candidate(
        detector_result(), lambda context: grounded_response()
    )

    assert result.generation_mode == "validated_llm"
    assert "SYNTHETIC/1" in result.summary_brief


def test_unknown_work_id_is_rejected_and_falls_back():
    generated = grounded_response(
        summary_brief="SYNTHETIC/99 shares the configured sanction evidence."
    )

    result = synthesise_candidate(detector_result(), lambda context: generated)

    assert result.generation_mode == "deterministic_fallback"
    assert "SYNTHETIC/99" not in result.summary_brief


def test_unlisted_amount_is_rejected_and_falls_back():
    generated = grounded_response(
        summary_brief="Both records refer to a sanction amount of INR 250000."
    )

    result = synthesise_candidate(detector_result(), lambda context: generated)

    assert result.generation_mode == "deterministic_fallback"
    assert "250000" not in result.summary_brief


def test_unlisted_percentage_is_rejected_and_falls_back():
    generated = grounded_response(
        primary_concerns=["The records indicate a 75 per cent match."]
    )

    result = synthesise_candidate(detector_result(), lambda context: generated)

    assert result.generation_mode == "deterministic_fallback"


def test_provider_failure_uses_fallback():
    def unavailable(context):
        raise TimeoutError("Synthetic provider timeout")

    result = synthesise_candidate(detector_result(), unavailable)

    assert result.generation_mode == "deterministic_fallback"
