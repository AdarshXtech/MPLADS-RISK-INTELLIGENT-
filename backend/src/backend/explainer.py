"""Grounded administrative synthesis for existing detector results."""

import json
import logging
import os
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

NUMBER_PATTERN = re.compile(r"(?<![A-Za-z0-9])\d[\d,]*(?:\.\d+)?")
CURRENCY_PATTERN = re.compile(
    r"(?:₹|\bINR\b|\bRs\.?)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE
)
PERCENTAGE_PATTERN = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*(?:%|per\s+cent\b)", re.IGNORECASE
)
IDENTIFIER_PATTERN = re.compile(
    r"\b(?=[A-Za-z0-9./_-]*[A-Za-z])"
    r"(?:[A-Za-z0-9]+(?:[./_-][A-Za-z0-9]+)+|[A-Za-z]{2,}\d{2,})\b"
)
LABELLED_WORK_ID_PATTERN = re.compile(
    r"\bwork\s+ids?\s*(?::|is\b|are\b)\s*([A-Za-z0-9./_-]+)", re.IGNORECASE
)
EMOJI_PATTERN = re.compile(
    "[\U0001f300-\U0001faff\U00002700-\U000027bf\U00002600-\U000026ff]"
)
PROHIBITED_TERMS = ("fraud", "corruption", "theft", "guilty")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class GroundedSourceFact(StrictModel):
    record_number: int
    work_id: str
    sanction_amount: str | None = None
    sanction_date: str | None = None
    state: str | None = None
    district: str | None = None
    constituency: str | None = None
    block_tehsil: str | None = None
    ward_village: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class GroundedExplanationContext(StrictModel):
    detector_id: str
    detector_name: str
    explanation: str
    fields_used: list[str]
    work_ids: list[str]
    evidence: dict[str, Any]
    verification_step: str
    limitations: list[str]
    source_records: list[GroundedSourceFact]


class GeneratedSynthesis(StrictModel):
    summary_brief: str = Field(min_length=1, max_length=1600)
    primary_concerns: list[str] = Field(min_length=1, max_length=8)
    verification_checklist: list[str] = Field(min_length=1, max_length=10)
    data_limitations: list[str] = Field(min_length=1, max_length=10)


class CandidateSynthesis(GeneratedSynthesis):
    generation_mode: Literal["validated_llm", "deterministic_fallback"]


class GroundingError(ValueError):
    """Raised when generated content is not supported by supplied facts."""


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    model_name: str
    base_url: str
    timeout_seconds: float


Generator = Callable[[GroundedExplanationContext], GeneratedSynthesis | dict]


def _as_dict(value: Any) -> dict:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    raise TypeError("Detector result must be a mapping or Pydantic model")


def _value_for_prefix(values: dict, prefix: str) -> str | None:
    for key, value in values.items():
        if key.casefold().startswith(prefix.casefold()) and value not in (None, ""):
            return str(value)
    return None


def build_grounded_context(
    detector_result: dict | BaseModel,
) -> GroundedExplanationContext:
    """Extract only authoritative detector and source facts for synthesis."""
    result = _as_dict(detector_result)
    evidence = result.get("evidence") or {}
    work_ids = {
        str(work_id)
        for work_id in evidence.get("different_work_ids", [])
        if work_id not in (None, "")
    }
    source_facts = []
    for raw_source in result.get("source_records") or []:
        source = _as_dict(raw_source)
        cleaned = source.get("cleaned_values") or {}
        location = source.get("location") or {}
        work_id = str(source.get("work_id") or "").strip()
        if work_id:
            work_ids.add(work_id)
        source_facts.append(
            GroundedSourceFact(
                record_number=source["record_number"],
                work_id=work_id,
                sanction_amount=_value_for_prefix(cleaned, "Sanction Amount"),
                sanction_date=_value_for_prefix(cleaned, "Sanction Date"),
                state=location.get("state") or cleaned.get("State"),
                district=location.get("district"),
                constituency=location.get("constituency")
                or cleaned.get("Constituency"),
                block_tehsil=location.get("block_tehsil"),
                ward_village=location.get("ward_village"),
                latitude=location.get("latitude"),
                longitude=location.get("longitude"),
            )
        )
    return GroundedExplanationContext(
        detector_id=str(result["detector_id"]),
        detector_name=str(result["detector_name"]),
        explanation=str(result["explanation"]),
        fields_used=[str(field) for field in result.get("fields_used") or []],
        work_ids=sorted(work_ids),
        evidence=evidence,
        verification_step=str(result["verification_step"]),
        limitations=[str(item) for item in result.get("limitations") or []],
        source_records=source_facts,
    )


def _fallback_concerns(context: GroundedExplanationContext) -> list[str]:
    concerns = []
    if context.work_ids:
        concerns.append(
            "The detector linked separate Work IDs: "
            + ", ".join(context.work_ids)
            + "."
        )
    matched_values = context.evidence.get("matched_values") or {}
    if matched_values:
        concerns.append(
            "The configured rule matched these evidence fields: "
            + ", ".join(str(field) for field in matched_values)
            + "."
        )
    locality = context.evidence.get("locality_evidence") or {}
    if locality.get("label"):
        concerns.append(f"Locality evidence used: {locality['label']}.")
    supporting = context.evidence.get("supporting_signals") or []
    labels = [str(item.get("label")) for item in supporting if item.get("label")]
    if labels:
        concerns.append("Supporting detector signals: " + ", ".join(labels) + ".")
    if not concerns:
        concerns.append(context.explanation)
    return concerns


def deterministic_fallback(
    detector_result: dict | BaseModel,
) -> CandidateSynthesis:
    context = build_grounded_context(detector_result)
    limitations = context.limitations or [
        "The brief is limited to the evidence supplied by the detector."
    ]
    return CandidateSynthesis(
        summary_brief=context.explanation,
        primary_concerns=_fallback_concerns(context),
        verification_checklist=[context.verification_step],
        data_limitations=limitations,
        generation_mode="deterministic_fallback",
    )


def _walk_numbers(value: Any) -> Iterable[Decimal]:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float, Decimal)):
        yield Decimal(str(value))
        return
    if isinstance(value, str):
        for match in NUMBER_PATTERN.finditer(value):
            try:
                yield Decimal(match.group().replace(",", ""))
            except InvalidOperation:
                continue
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from _walk_numbers(item)


def _numbers_for_keys(value: Any, key_terms: tuple[str, ...]) -> set[Decimal]:
    found: set[Decimal] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).casefold() for term in key_terms):
                found.update(_walk_numbers(item))
            found.update(_numbers_for_keys(item, key_terms))
    elif isinstance(value, list):
        for item in value:
            found.update(_numbers_for_keys(item, key_terms))
    return found


def _supported(number: Decimal, allowed: Iterable[Decimal]) -> bool:
    for expected in allowed:
        tolerance = max(abs(expected) * Decimal("0.01"), Decimal("0.005"))
        if abs(number - expected) <= tolerance:
            return True
    return False


def _all_text(content: GeneratedSynthesis) -> str:
    return "\n".join(
        [
            content.summary_brief,
            *content.primary_concerns,
            *content.verification_checklist,
            *content.data_limitations,
        ]
    )


def validate_grounding(
    content: GeneratedSynthesis, context: GroundedExplanationContext
) -> None:
    """Reject identifiers, figures or language absent from authoritative facts."""
    text = _all_text(content)
    lowered = text.casefold()
    if "—" in text or EMOJI_PATTERN.search(text):
        raise GroundingError("Generated synthesis does not meet the writing policy")
    if any(re.search(rf"\b{re.escape(term)}\b", lowered) for term in PROHIBITED_TERMS):
        raise GroundingError("Generated synthesis contains prohibited language")

    allowed_ids = {work_id.casefold() for work_id in context.work_ids}
    mentioned_ids = {
        match.group().casefold() for match in IDENTIFIER_PATTERN.finditer(text)
    }
    mentioned_ids.update(
        match.group(1).casefold() for match in LABELLED_WORK_ID_PATTERN.finditer(text)
    )
    unknown_ids = mentioned_ids - allowed_ids
    if unknown_ids:
        raise GroundingError("Generated synthesis contains an unsupported identifier")

    context_data = context.model_dump(mode="json")
    allowed_numbers = set(_walk_numbers(context_data))
    amount_numbers = _numbers_for_keys(context_data, ("amount", "median"))
    percentage_numbers = _numbers_for_keys(
        context_data, ("percentage", "percent", "similarity")
    )
    percentage_numbers.update(
        number * Decimal(100)
        for number in tuple(percentage_numbers)
        if Decimal(0) <= number <= Decimal(1)
    )

    numeric_text = text
    for work_id in sorted(context.work_ids, key=len, reverse=True):
        numeric_text = re.sub(re.escape(work_id), "", numeric_text, flags=re.IGNORECASE)
    for match in CURRENCY_PATTERN.finditer(numeric_text):
        value = Decimal(match.group(1).replace(",", ""))
        if not _supported(value, amount_numbers):
            raise GroundingError("Generated synthesis contains an unsupported amount")
    for match in PERCENTAGE_PATTERN.finditer(numeric_text):
        value = Decimal(match.group(1).replace(",", ""))
        if not _supported(value, percentage_numbers):
            raise GroundingError(
                "Generated synthesis contains an unsupported percentage"
            )
    for number in _walk_numbers(numeric_text):
        if not _supported(number, allowed_numbers | percentage_numbers):
            raise GroundingError("Generated synthesis contains an unsupported figure")


def _settings_from_environment() -> LLMSettings | None:
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    model_name = os.environ.get("LLM_MODEL_NAME", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "").strip().rstrip("/")
    if not api_key or not model_name or not base_url:
        return None
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        logger.warning("LLM synthesis disabled because LLM_BASE_URL is invalid")
        return None
    try:
        timeout = float(os.environ.get("LLM_TIMEOUT_SECONDS", "8"))
    except ValueError:
        timeout = 8.0
    return LLMSettings(
        api_key=api_key,
        model_name=model_name,
        base_url=base_url,
        timeout_seconds=min(max(timeout, 1.0), 30.0),
    )


def _chat_completions_url(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    return base_url + "/chat/completions"


def _provider_content(payload: dict) -> str:
    content = payload["choices"][0]["message"]["content"]
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(item.get("text", "")) for item in content if isinstance(item, dict)
        )
    raise ValueError("LLM response content is unavailable")


def _generate_with_configured_llm(
    context: GroundedExplanationContext, settings: LLMSettings
) -> GeneratedSynthesis:
    schema = GeneratedSynthesis.model_json_schema()
    request_body = {
        "model": settings.model_name,
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "mplads_grounded_synthesis",
                "strict": True,
                "schema": schema,
            },
        },
        "messages": [
            {
                "role": "system",
                "content": (
                    "Prepare a neutral Indian English administrative brief using only the "
                    "supplied facts. Do not infer missing facts, introduce identifiers or "
                    "numbers, assign risk, change severity, or make an accusation. Return only "
                    "JSON matching the supplied schema."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    context.model_dump(mode="json"), ensure_ascii=False, sort_keys=True
                ),
            },
        ],
    }
    request = Request(
        _chat_completions_url(settings.base_url),
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=settings.timeout_seconds) as response:
        response_body = json.loads(response.read().decode("utf-8"))
    return GeneratedSynthesis.model_validate_json(_provider_content(response_body))


def synthesise_candidate(
    detector_result: dict | BaseModel, generator: Generator | None = None
) -> CandidateSynthesis:
    """Return validated synthesis or a deterministic detector-derived fallback."""
    fallback = deterministic_fallback(detector_result)
    context = build_grounded_context(detector_result)
    if generator is None:
        settings = _settings_from_environment()
        if settings is None:
            return fallback
        generator = lambda grounded: _generate_with_configured_llm(grounded, settings)
    try:
        generated = GeneratedSynthesis.model_validate(generator(context))
        validate_grounding(generated, context)
        return CandidateSynthesis(
            **generated.model_dump(), generation_mode="validated_llm"
        )
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        TimeoutError,
        OSError,
    ) as error:
        logger.warning(
            "Generated candidate synthesis rejected; deterministic fallback used (%s)",
            type(error).__name__,
        )
        return fallback
