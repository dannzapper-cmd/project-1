"""Unit tests for the Phase 5.9 QA-synthesis JSON validation.

Covers ``QAEvaluatorSynthesisPayload`` plus a few sanity checks on the
shared ``extract_json_object`` helper.
"""

from __future__ import annotations

import json
import textwrap

import pytest
from pydantic import ValidationError

from app.schemas.common import HallucinationRisk, Recommendation
from app.schemas.qa_synthesis import QAEvaluatorSynthesisPayload
from app.services.json_utils import extract_json_object


_VALID_JSON = json.dumps(
    {
        "qa_score": 80,
        "personalization": 75,
        "evidence_coverage": 70,
        "cta_quality": 80,
        "tone_match": 85,
        "hallucination_risk": "low",
        "recommendation": "review",
        "strengths": ["clear CTA"],
        "risks": ["thin context"],
        "required_fixes": ["add lead source reference"],
    }
)


def _validate(text: str) -> QAEvaluatorSynthesisPayload:
    return QAEvaluatorSynthesisPayload.model_validate(extract_json_object(text))


# --------------------------------------------------------------------------- #
# 1. Valid JSON                                                               #
# --------------------------------------------------------------------------- #


def test_1_valid_json_validates_into_payload() -> None:
    """1: Valid JSON validates into QAEvaluatorSynthesisPayload."""

    payload = _validate(_VALID_JSON)
    assert isinstance(payload, QAEvaluatorSynthesisPayload)
    assert payload.qa_score == 80
    assert payload.hallucination_risk == HallucinationRisk.LOW
    assert payload.recommendation == Recommendation.REVIEW


# --------------------------------------------------------------------------- #
# 2. JSON inside surrounding text                                             #
# --------------------------------------------------------------------------- #


def test_2a_json_inside_markdown_fence_extracts() -> None:
    """2a: JSON wrapped in a markdown fence extracts."""

    text = textwrap.dedent(
        f"""\
        Sure, here is the evaluation:

        ```json
        {_VALID_JSON}
        ```

        Let me know if you need changes.
        """
    )
    payload = _validate(text)
    assert payload.qa_score == 80


def test_2b_json_inside_loose_prose_extracts() -> None:
    """2b: JSON embedded in prose extracts."""

    text = f"prefix garbage {_VALID_JSON} suffix garbage"
    payload = _validate(text)
    assert payload.recommendation == Recommendation.REVIEW


# --------------------------------------------------------------------------- #
# 3. Invalid JSON                                                             #
# --------------------------------------------------------------------------- #


def test_3_no_json_raises_value_error() -> None:
    """3: A response with no JSON object raises ValueError."""

    with pytest.raises(ValueError) as excinfo:
        extract_json_object("Just plain prose with no braces.")
    assert "No valid JSON object" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# 4. Missing required fields                                                  #
# --------------------------------------------------------------------------- #


def test_4_missing_required_fields_fail() -> None:
    """4: Each required field is enforced by the schema.

    The ``strengths`` / ``risks`` / ``required_fixes`` fields have
    ``default_factory=list`` and so are NOT in the loop — omitting them
    yields an empty list (the default) which the schema accepts.
    """

    base = {
        "qa_score": 80,
        "personalization": 75,
        "evidence_coverage": 70,
        "cta_quality": 80,
        "tone_match": 85,
        "hallucination_risk": "low",
        "recommendation": "review",
    }
    for missing in (
        "qa_score",
        "personalization",
        "evidence_coverage",
        "cta_quality",
        "tone_match",
        "hallucination_risk",
        "recommendation",
    ):
        partial = {k: v for k, v in base.items() if k != missing}
        with pytest.raises(ValidationError):
            QAEvaluatorSynthesisPayload.model_validate(partial)


# --------------------------------------------------------------------------- #
# 5. Score bounds                                                             #
# --------------------------------------------------------------------------- #


def test_5_score_fields_outside_bounds_fail() -> None:
    """5: Score fields below 0 or above 100 fail validation."""

    base = json.loads(_VALID_JSON)
    for score_field in (
        "qa_score",
        "personalization",
        "evidence_coverage",
        "cta_quality",
        "tone_match",
    ):
        # Below 0.
        candidate = dict(base)
        candidate[score_field] = -1
        with pytest.raises(ValidationError):
            QAEvaluatorSynthesisPayload.model_validate(candidate)
        # Above 100.
        candidate = dict(base)
        candidate[score_field] = 101
        with pytest.raises(ValidationError):
            QAEvaluatorSynthesisPayload.model_validate(candidate)


# --------------------------------------------------------------------------- #
# 6. Invalid hallucination_risk                                               #
# --------------------------------------------------------------------------- #


def test_6_invalid_hallucination_risk_fails() -> None:
    """6: An out-of-vocabulary ``hallucination_risk`` is rejected."""

    candidate = json.loads(_VALID_JSON)
    candidate["hallucination_risk"] = "ultracritical"
    with pytest.raises(ValidationError):
        QAEvaluatorSynthesisPayload.model_validate(candidate)


# --------------------------------------------------------------------------- #
# 7. Invalid recommendation                                                   #
# --------------------------------------------------------------------------- #


def test_7_invalid_recommendation_fails() -> None:
    """7: An out-of-vocabulary ``recommendation`` is rejected."""

    candidate = json.loads(_VALID_JSON)
    candidate["recommendation"] = "send-immediately"
    with pytest.raises(ValidationError):
        QAEvaluatorSynthesisPayload.model_validate(candidate)


# --------------------------------------------------------------------------- #
# 8. Lowercase enum strings normalise (FIX 3)                                 #
# --------------------------------------------------------------------------- #


def test_8_lowercase_enum_strings_normalise() -> None:
    """8: Lowercase ``"low|medium|high"`` and
    ``"approve|review|regenerate"`` map to the actual enum values."""

    base = json.loads(_VALID_JSON)
    for risk_raw, expected_risk in (
        ("low", HallucinationRisk.LOW),
        ("medium", HallucinationRisk.MEDIUM),
        ("high", HallucinationRisk.HIGH),
        ("HIGH", HallucinationRisk.HIGH),
        ("Medium", HallucinationRisk.MEDIUM),
    ):
        for rec_raw, expected_rec in (
            ("approve", Recommendation.APPROVE),
            ("approved", Recommendation.APPROVE),
            ("review", Recommendation.REVIEW),
            ("regenerate", Recommendation.REGENERATE),
            ("reject", Recommendation.REGENERATE),
        ):
            candidate = dict(base)
            candidate["hallucination_risk"] = risk_raw
            candidate["recommendation"] = rec_raw
            payload = QAEvaluatorSynthesisPayload.model_validate(candidate)
            assert payload.hallucination_risk == expected_risk
            assert payload.recommendation == expected_rec


# --------------------------------------------------------------------------- #
# 9. Too many strengths/risks/fixes                                           #
# --------------------------------------------------------------------------- #


def test_9_too_many_list_entries_rejected() -> None:
    """9: max_length=8 is enforced on strengths, risks and required_fixes."""

    base = json.loads(_VALID_JSON)
    for list_field in ("strengths", "risks", "required_fixes"):
        candidate = dict(base)
        candidate[list_field] = [f"x{i}" for i in range(9)]
        with pytest.raises(ValidationError):
            QAEvaluatorSynthesisPayload.model_validate(candidate)


# --------------------------------------------------------------------------- #
# 10. No eval / unsafe parsing                                                #
# --------------------------------------------------------------------------- #


def test_10_no_eval_or_unsafe_parsing_imports_present() -> None:
    """10: ``json_utils.py`` must not rely on ``eval`` / ``literal_eval``."""

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
