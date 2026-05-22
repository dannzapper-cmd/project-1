"""Unit tests for the Phase 5.6B Qualifier-synthesis JSON validation.

Covers the schema (``QualifierSynthesisPayload``) plus the shared
``extract_json_object`` helper (re-imported through the agent module so
the existing import path keeps working).
"""

from __future__ import annotations

import json
import textwrap

import pytest
from pydantic import ValidationError

from app.schemas.common import Confidence, Priority
from app.schemas.qualifier_synthesis import QualifierSynthesisPayload
from app.services.json_utils import extract_json_object

_VALID_JSON = json.dumps(
    {
        "fit_score": 80,
        "priority": "high",
        "fit_reasons": ["B2B SaaS Tier 1", "Hiring SDRs"],
        "fit_risks": ["Budget authority unverified"],
        "confidence": "high",
    }
)


def _validate(text: str) -> QualifierSynthesisPayload:
    """Helper that mirrors the agent path: extract + model_validate."""

    return QualifierSynthesisPayload.model_validate(extract_json_object(text))


# --------------------------------------------------------------------------- #
# 1. Valid JSON validates into payload                                        #
# --------------------------------------------------------------------------- #


def test_1_valid_json_validates_into_payload() -> None:
    """1: Valid JSON validates into QualifierSynthesisPayload."""

    payload = _validate(_VALID_JSON)
    assert isinstance(payload, QualifierSynthesisPayload)
    assert payload.fit_score == 80
    assert payload.priority == Priority.HIGH
    assert payload.confidence == Confidence.HIGH
    assert payload.fit_reasons == ["B2B SaaS Tier 1", "Hiring SDRs"]
    assert payload.fit_risks == ["Budget authority unverified"]


# --------------------------------------------------------------------------- #
# 2. JSON inside surrounding text can be extracted                            #
# --------------------------------------------------------------------------- #


def test_2_json_inside_markdown_fence_extracts() -> None:
    """2a: JSON wrapped in a markdown code fence extracts."""

    text = textwrap.dedent(
        """\
        Sure! Here is the qualification:

        ```json
        {
          "fit_score": 65,
          "priority": "medium",
          "fit_reasons": ["Mexico Tier 2"],
          "fit_risks": [],
          "confidence": "medium"
        }
        ```

        Let me know if you need adjustments.
        """
    )
    payload = _validate(text)
    assert payload.fit_score == 65
    assert payload.priority == Priority.MEDIUM


def test_2b_json_inside_loose_prose_extracts() -> None:
    """2b: JSON embedded in prose extracts via the first-`{` to last-`}`
    strategy."""

    text = (
        "prefix garbage "
        '{"fit_score": 10, "priority": "low", "fit_reasons": [], '
        '"fit_risks": ["small"], "confidence": "low"} '
        "suffix garbage"
    )
    payload = _validate(text)
    assert payload.priority == Priority.LOW


# --------------------------------------------------------------------------- #
# 3. Invalid JSON raises ValueError                                           #
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
# 4. fit_score bounded 0..100                                                 #
# --------------------------------------------------------------------------- #


def test_4_fit_score_below_zero_rejected() -> None:
    """4a: fit_score < 0 is rejected."""

    with pytest.raises(ValidationError):
        QualifierSynthesisPayload(
            fit_score=-1, priority=Priority.LOW, confidence=Confidence.LOW
        )


def test_4b_fit_score_above_hundred_rejected() -> None:
    """4b: fit_score > 100 is rejected."""

    with pytest.raises(ValidationError):
        QualifierSynthesisPayload(
            fit_score=101, priority=Priority.HIGH, confidence=Confidence.HIGH
        )


def test_4c_fit_score_boundaries_accepted() -> None:
    """4c: 0 and 100 boundary values are accepted."""

    QualifierSynthesisPayload(
        fit_score=0, priority=Priority.LOW, confidence=Confidence.LOW
    )
    QualifierSynthesisPayload(
        fit_score=100, priority=Priority.HIGH, confidence=Confidence.HIGH
    )


# --------------------------------------------------------------------------- #
# 5. Invalid priority fails                                                   #
# --------------------------------------------------------------------------- #


def test_5_invalid_priority_fails_validation() -> None:
    """5: An out-of-vocabulary priority value is rejected."""

    bad = json.dumps(
        {
            "fit_score": 50,
            "priority": "supercritical",
            "fit_reasons": [],
            "fit_risks": [],
            "confidence": "high",
        }
    )
    with pytest.raises(ValidationError):
        QualifierSynthesisPayload.model_validate(extract_json_object(bad))


def test_5b_invalid_confidence_fails_validation() -> None:
    """5b: An out-of-vocabulary confidence value is rejected."""

    bad = json.dumps(
        {
            "fit_score": 50,
            "priority": "low",
            "fit_reasons": [],
            "fit_risks": [],
            "confidence": "ultra",
        }
    )
    with pytest.raises(ValidationError):
        QualifierSynthesisPayload.model_validate(extract_json_object(bad))


# --------------------------------------------------------------------------- #
# 6. Too many fit_reasons / fit_risks                                         #
# --------------------------------------------------------------------------- #


def test_6_too_many_fit_reasons_rejected() -> None:
    """6a: max_length=8 on fit_reasons is enforced."""

    with pytest.raises(ValidationError):
        QualifierSynthesisPayload(
            fit_score=50,
            priority=Priority.MEDIUM,
            fit_reasons=[f"r{i}" for i in range(9)],
            fit_risks=[],
            confidence=Confidence.MEDIUM,
        )


def test_6b_too_many_fit_risks_rejected() -> None:
    """6b: max_length=8 on fit_risks is enforced."""

    with pytest.raises(ValidationError):
        QualifierSynthesisPayload(
            fit_score=50,
            priority=Priority.MEDIUM,
            fit_reasons=[],
            fit_risks=[f"k{i}" for i in range(9)],
            confidence=Confidence.MEDIUM,
        )


# --------------------------------------------------------------------------- #
# 7. Lowercase priority / confidence normalise (FIX 2 validator)              #
# --------------------------------------------------------------------------- #


def test_7_lowercase_priority_and_confidence_normalise() -> None:
    """7: Lowercase ``"high|medium|low"`` strings normalise to the enum."""

    for prio_in, prio_out in (
        ("high", Priority.HIGH),
        ("medium", Priority.MEDIUM),
        ("low", Priority.LOW),
        ("HIGH", Priority.HIGH),
        ("Medium", Priority.MEDIUM),
    ):
        for conf_in, conf_out in (
            ("high", Confidence.HIGH),
            ("medium", Confidence.MEDIUM),
            ("low", Confidence.LOW),
        ):
            payload = QualifierSynthesisPayload(
                fit_score=50,
                priority=prio_in,  # type: ignore[arg-type]
                confidence=conf_in,  # type: ignore[arg-type]
            )
            assert payload.priority == prio_out
            assert payload.confidence == conf_out


# --------------------------------------------------------------------------- #
# 8. No eval / unsafe parsing in the helper module                            #
# --------------------------------------------------------------------------- #


def test_8_no_eval_or_unsafe_parsing_imports_present() -> None:
    """8: The shared ``json_utils`` module must not rely on ``eval`` or
    ``ast.literal_eval``.

    Asserted against actual import statements / call sites, not against
    docstring text (the docstring intentionally mentions those names by
    name to document the rule).
    """

    payload = "os.system('rm -rf /') {not json"
    with pytest.raises(ValueError):
        extract_json_object(payload)

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
        assert "literal_eval(" not in line, (
            f"literal_eval call detected: {line!r}"
        )
        assert "eval(" not in line, f"eval() call detected: {line!r}"
