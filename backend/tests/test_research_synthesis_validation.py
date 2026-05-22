"""Unit tests for the Phase 5.5C structured-research JSON validation.

Covers ``extract_json_object``, ``validate_research_synthesis_payload``,
and the ``ResearchSynthesisPayload`` schema constraints.
"""

from __future__ import annotations

import json
import textwrap

import pytest
from pydantic import ValidationError

from app.agents.research_agent import (
    extract_json_object,
    validate_research_synthesis_payload,
)
from app.schemas.common import Confidence
from app.schemas.research_synthesis import (
    ResearchSynthesisEvidence,
    ResearchSynthesisPayload,
)


_VALID_JSON = json.dumps(
    {
        "company_summary": "Acme Co is a growth-stage B2B SaaS company.",
        "opportunity_signals": ["Hiring SDRs", "Series B raised"],
        "pain_hypotheses": ["Pipeline quality at scale"],
        "evidence_cards": [
            {
                "headline": "Hiring evidence",
                "description": "Three SDR roles posted simultaneously.",
                "confidence": "high",
            }
        ],
        "information_risks": ["Budget authority unverified."],
        "confidence": "high",
    }
)


# --------------------------------------------------------------------------- #
# 1. Valid JSON validates into the payload                                    #
# --------------------------------------------------------------------------- #


def test_1_valid_json_validates_into_payload() -> None:
    """1: Valid JSON validates into ResearchSynthesisPayload."""

    payload = validate_research_synthesis_payload(_VALID_JSON)
    assert isinstance(payload, ResearchSynthesisPayload)
    assert payload.company_summary.startswith("Acme")
    assert payload.opportunity_signals == ["Hiring SDRs", "Series B raised"]
    assert payload.confidence == Confidence.HIGH
    assert len(payload.evidence_cards) == 1
    assert isinstance(payload.evidence_cards[0], ResearchSynthesisEvidence)
    assert payload.evidence_cards[0].confidence == Confidence.HIGH


# --------------------------------------------------------------------------- #
# 2. JSON inside surrounding text can be extracted                            #
# --------------------------------------------------------------------------- #


def test_2_json_inside_markdown_fence_extracts() -> None:
    """2a: JSON wrapped in a markdown code fence (with `json` tag) extracts."""

    text = textwrap.dedent(
        """\
        Sure! Here is the structured synthesis:

        ```json
        {
          "company_summary": "Fence-wrapped summary.",
          "opportunity_signals": [],
          "pain_hypotheses": [],
          "evidence_cards": [],
          "information_risks": [],
          "confidence": "medium"
        }
        ```

        Let me know if you need adjustments.
        """
    )
    payload = validate_research_synthesis_payload(text)
    assert payload.company_summary == "Fence-wrapped summary."


def test_2b_json_inside_loose_prose_extracts() -> None:
    """2b: JSON embedded in prose without code fences extracts via the
    first-`{` to last-`}` strategy."""

    text = (
        "prefix garbage "
        '{"company_summary": "Loose-prose summary.", '
        '"opportunity_signals": [], '
        '"pain_hypotheses": [], '
        '"evidence_cards": [], '
        '"information_risks": [], '
        '"confidence": "low"} '
        "suffix garbage"
    )
    payload = validate_research_synthesis_payload(text)
    assert payload.company_summary == "Loose-prose summary."
    assert payload.confidence == Confidence.LOW


def test_2c_extract_only_returns_dict_for_plain_json() -> None:
    """2c: extract_json_object returns the parsed dict for a bare JSON object."""

    data = extract_json_object('{"a": 1, "b": [2, 3]}')
    assert data == {"a": 1, "b": [2, 3]}


# --------------------------------------------------------------------------- #
# 3. Invalid JSON raises ValueError                                           #
# --------------------------------------------------------------------------- #


def test_3_no_json_raises_value_error() -> None:
    """3a: A response with no JSON object raises ValueError."""

    with pytest.raises(ValueError) as excinfo:
        extract_json_object("Just plain prose, no braces at all.")
    assert "No valid JSON object" in str(excinfo.value)


def test_3b_malformed_braces_raises_value_error() -> None:
    """3b: A response with broken JSON raises ValueError."""

    with pytest.raises(ValueError):
        extract_json_object("{this: 'is not json',}")


def test_3c_validate_invalid_json_raises_value_error() -> None:
    """3c: validate_research_synthesis_payload raises ValueError on
    non-JSON input."""

    with pytest.raises(ValueError):
        validate_research_synthesis_payload("nope")


# --------------------------------------------------------------------------- #
# 4. Missing company_summary fails validation                                 #
# --------------------------------------------------------------------------- #


def test_4_missing_company_summary_raises_value_error() -> None:
    """4: A payload missing the required company_summary fails validation.

    ``validate_research_synthesis_payload`` re-raises Pydantic
    ValidationError as ValueError so the agent layer sees a uniform
    failure type.
    """

    bad = json.dumps(
        {
            "opportunity_signals": [],
            "pain_hypotheses": [],
            "evidence_cards": [],
            "information_risks": [],
            "confidence": "medium",
        }
    )
    with pytest.raises(ValueError):
        validate_research_synthesis_payload(bad)


def test_4b_empty_company_summary_rejected_by_schema() -> None:
    """4b: An explicitly empty company_summary is rejected by min_length=1."""

    with pytest.raises(ValidationError):
        ResearchSynthesisPayload(company_summary="")


# --------------------------------------------------------------------------- #
# 5. Too-many lists fail the schema max_length caps                           #
# --------------------------------------------------------------------------- #


def test_5_too_many_opportunity_signals_rejected() -> None:
    """5a: max_length=5 on opportunity_signals is enforced."""

    with pytest.raises(ValidationError):
        ResearchSynthesisPayload(
            company_summary="ok",
            opportunity_signals=["s%d" % i for i in range(6)],
        )


def test_5b_too_many_evidence_cards_rejected() -> None:
    """5b: max_length=5 on evidence_cards is enforced."""

    cards = [
        ResearchSynthesisEvidence(headline=f"h{i}", description=f"d{i}")
        for i in range(6)
    ]
    with pytest.raises(ValidationError):
        ResearchSynthesisPayload(company_summary="ok", evidence_cards=cards)


def test_5c_too_many_information_risks_rejected() -> None:
    """5c: max_length=10 on information_risks is enforced."""

    with pytest.raises(ValidationError):
        ResearchSynthesisPayload(
            company_summary="ok",
            information_risks=[f"r{i}" for i in range(11)],
        )


# --------------------------------------------------------------------------- #
# 6. No unsafe parsing path exists                                            #
# --------------------------------------------------------------------------- #


def test_6_no_eval_or_unsafe_parsing_imports_present() -> None:
    """6: ``extract_json_object`` must not rely on ``eval`` or
    ``ast.literal_eval``.

    A `os.system`-style payload disguised as JSON-like text must NOT
    execute. We assert the helper raises a plain ValueError instead.
    """

    payload = "os.system('rm -rf /') {not json"
    with pytest.raises(ValueError):
        extract_json_object(payload)

    # And the source file must not import or call the dangerous
    # helpers. We assert specifically against import statements and
    # call sites (not against any occurrence of the strings — the
    # module's docstring mentions them by name to document the rule).
    import app.agents.research_agent as mod

    source_lines = open(mod.__file__).read().splitlines()
    code_lines = [
        line for line in source_lines
        if not line.lstrip().startswith(("#", '"', "'"))
    ]
    for line in code_lines:
        stripped = line.strip()
        assert not stripped.startswith("import ast"), (
            f"ast import detected: {line!r}"
        )
        assert not stripped.startswith("from ast"), (
            f"ast import detected: {line!r}"
        )
        assert "literal_eval(" not in line, (
            f"literal_eval call detected: {line!r}"
        )
        # Bare `eval(` is a call site — `ValueError`/`ValidationError`
        # contain the substring `eval` but never `eval(`.
        assert "eval(" not in line, f"eval() call detected: {line!r}"
