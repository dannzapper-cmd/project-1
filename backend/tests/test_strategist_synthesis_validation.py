"""Unit tests for the Phase 5.7 Strategist-synthesis JSON validation.

Covers the schema (``StrategistSynthesisPayload``) plus the shared
``extract_json_object`` helper.
"""

from __future__ import annotations

import json
import textwrap

import pytest
from pydantic import ValidationError

from app.schemas.common import Confidence
from app.schemas.strategist_synthesis import StrategistSynthesisPayload
from app.services.json_utils import extract_json_object


_VALID_JSON = json.dumps(
    {
        "pain_hypothesis": "Pipeline quality at scale.",
        "pain_confidence": "high",
        "sales_angle": "Position LeadForge as the qualification layer.",
        "core_message": "For Acme, LeadForge can structure outreach.",
        "likely_objection": "We already have a CRM.",
        "personalization_notes": ["Reference industry", "Reference role"],
    }
)


def _validate(text: str) -> StrategistSynthesisPayload:
    return StrategistSynthesisPayload.model_validate(extract_json_object(text))


# --------------------------------------------------------------------------- #
# 1. Valid JSON validates into payload                                        #
# --------------------------------------------------------------------------- #


def test_1_valid_json_validates_into_payload() -> None:
    """1: Valid JSON validates into StrategistSynthesisPayload."""

    payload = _validate(_VALID_JSON)
    assert isinstance(payload, StrategistSynthesisPayload)
    assert payload.pain_hypothesis == "Pipeline quality at scale."
    assert payload.pain_confidence == Confidence.HIGH
    assert payload.personalization_notes == [
        "Reference industry",
        "Reference role",
    ]


# --------------------------------------------------------------------------- #
# 2. JSON inside surrounding text                                             #
# --------------------------------------------------------------------------- #


def test_2_json_inside_markdown_fence_extracts() -> None:
    """2a: JSON wrapped in a markdown fence extracts."""

    text = textwrap.dedent(
        """\
        Sure, here is the strategy:

        ```json
        {
          "pain_hypothesis": "Fenced pain.",
          "pain_confidence": "medium",
          "sales_angle": "Fenced angle.",
          "core_message": "Fenced message.",
          "likely_objection": "Fenced objection.",
          "personalization_notes": ["Fenced note"]
        }
        ```

        Let me know if you need changes.
        """
    )
    payload = _validate(text)
    assert payload.pain_hypothesis == "Fenced pain."


def test_2b_json_inside_loose_prose_extracts() -> None:
    """2b: JSON embedded in prose extracts."""

    text = (
        "prefix garbage "
        '{"pain_hypothesis": "Loose pain.", "pain_confidence": "low", '
        '"sales_angle": "Loose angle.", "core_message": "Loose msg.", '
        '"likely_objection": "Loose objection.", '
        '"personalization_notes": ["Loose note"]} '
        "suffix garbage"
    )
    payload = _validate(text)
    assert payload.pain_confidence == Confidence.LOW


# --------------------------------------------------------------------------- #
# 3. Invalid JSON                                                             #
# --------------------------------------------------------------------------- #


def test_3_no_json_raises_value_error() -> None:
    """3: A response with no JSON object raises ValueError."""

    with pytest.raises(ValueError) as excinfo:
        extract_json_object("Just plain prose with no braces.")
    assert "No valid JSON object" in str(excinfo.value)


def test_3b_malformed_json_raises_value_error() -> None:
    """3b: A malformed JSON-like string raises ValueError."""

    with pytest.raises(ValueError):
        extract_json_object("{this: 'is not json',}")


# --------------------------------------------------------------------------- #
# 4. Missing required fields fail                                             #
# --------------------------------------------------------------------------- #


def test_4_missing_required_fields_fail() -> None:
    """4: Each required field is enforced by the schema."""

    base = {
        "pain_hypothesis": "p",
        "sales_angle": "a",
        "core_message": "c",
        "likely_objection": "o",
        "personalization_notes": ["n"],
    }
    for missing in (
        "pain_hypothesis",
        "sales_angle",
        "core_message",
        "likely_objection",
    ):
        partial = {k: v for k, v in base.items() if k != missing}
        with pytest.raises(ValidationError):
            StrategistSynthesisPayload.model_validate(partial)


# --------------------------------------------------------------------------- #
# 5. Empty required strings fail                                              #
# --------------------------------------------------------------------------- #


def test_5_empty_required_strings_fail() -> None:
    """5: ``min_length=1`` is enforced on every required string field."""

    base = {
        "pain_hypothesis": "p",
        "sales_angle": "a",
        "core_message": "c",
        "likely_objection": "o",
        "personalization_notes": ["n"],
    }
    for empty_field in (
        "pain_hypothesis",
        "sales_angle",
        "core_message",
        "likely_objection",
    ):
        candidate = dict(base)
        candidate[empty_field] = ""
        with pytest.raises(ValidationError):
            StrategistSynthesisPayload.model_validate(candidate)


# --------------------------------------------------------------------------- #
# 6. personalization_notes bounds (per FIX 4: both ends covered)              #
# --------------------------------------------------------------------------- #


def test_6_too_many_personalization_notes_rejected() -> None:
    """6a: max_length=5 on personalization_notes is enforced."""

    with pytest.raises(ValidationError):
        StrategistSynthesisPayload(
            pain_hypothesis="p",
            sales_angle="a",
            core_message="c",
            likely_objection="o",
            personalization_notes=[f"n{i}" for i in range(6)],
        )


def test_6b_empty_personalization_notes_rejected_per_fix_4() -> None:
    """6b (Phase 5.7 FIX 4): min_length=1 on personalization_notes is
    enforced — an empty list is rejected."""

    with pytest.raises(ValidationError):
        StrategistSynthesisPayload(
            pain_hypothesis="p",
            sales_angle="a",
            core_message="c",
            likely_objection="o",
            personalization_notes=[],
        )


# --------------------------------------------------------------------------- #
# 7. Lowercase confidence normalises (FIX 1)                                  #
# --------------------------------------------------------------------------- #


def test_7_lowercase_confidence_normalises() -> None:
    """7: Lowercase ``"high|medium|low"`` strings normalise to the enum."""

    for raw, expected in (
        ("high", Confidence.HIGH),
        ("medium", Confidence.MEDIUM),
        ("low", Confidence.LOW),
        ("HIGH", Confidence.HIGH),
        ("Medium", Confidence.MEDIUM),
    ):
        payload = StrategistSynthesisPayload(
            pain_hypothesis="p",
            pain_confidence=raw,  # type: ignore[arg-type]
            sales_angle="a",
            core_message="c",
            likely_objection="o",
            personalization_notes=["n"],
        )
        assert payload.pain_confidence == expected


def test_7b_invalid_confidence_still_rejected() -> None:
    """7b: an out-of-vocabulary confidence value still fails validation."""

    with pytest.raises(ValidationError):
        StrategistSynthesisPayload(
            pain_hypothesis="p",
            pain_confidence="supercritical",  # type: ignore[arg-type]
            sales_angle="a",
            core_message="c",
            likely_objection="o",
            personalization_notes=["n"],
        )


# --------------------------------------------------------------------------- #
# 8. No eval / unsafe parsing audit                                           #
# --------------------------------------------------------------------------- #


def test_8_no_eval_or_unsafe_parsing_imports_present() -> None:
    """8: The shared ``json_utils`` module must not rely on ``eval`` or
    ``ast.literal_eval`` (re-asserted here so Phase 5.7's strategist
    path inherits the same audit)."""

    with pytest.raises(ValueError):
        extract_json_object("os.system('rm -rf /') {not json")

    import app.services.json_utils as mod

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
        assert "literal_eval(" not in line
        assert "eval(" not in line
