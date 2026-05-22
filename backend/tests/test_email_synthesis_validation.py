"""Unit tests for the Phase 5.8 Email-draft synthesis JSON validation.

Covers ``EmailDraftSynthesisPayload`` plus a few sanity checks on the
shared ``extract_json_object`` helper from Phase 5.5C / 5.6B / 5.7.
"""

from __future__ import annotations

import json
import textwrap

import pytest
from pydantic import ValidationError

from app.schemas.common import Confidence
from app.schemas.email_synthesis import EmailDraftSynthesisPayload
from app.services.json_utils import extract_json_object


_BODY_OK = (
    "Hi Sarah, I'm reaching out because the team at Acme might be facing "
    "research and qualification bottlenecks as you scale. LeadForge can "
    "help structure that work into a reviewable, prioritized pipeline. "
    "Would it be worth a quick look?"
)


_VALID_JSON = json.dumps(
    {
        "email_subject": "Idea for Acme",
        "email_body": _BODY_OK,
        "personalization_notes": ["Reference Acme", "Reference Series B"],
        "confidence": "high",
    }
)


def _validate(text: str) -> EmailDraftSynthesisPayload:
    return EmailDraftSynthesisPayload.model_validate(extract_json_object(text))


# --------------------------------------------------------------------------- #
# 1. Valid JSON                                                               #
# --------------------------------------------------------------------------- #


def test_1_valid_json_validates_into_payload() -> None:
    """1: Valid JSON validates into EmailDraftSynthesisPayload."""

    payload = _validate(_VALID_JSON)
    assert isinstance(payload, EmailDraftSynthesisPayload)
    assert payload.email_subject == "Idea for Acme"
    assert payload.confidence == Confidence.HIGH


# --------------------------------------------------------------------------- #
# 2. JSON inside surrounding text                                             #
# --------------------------------------------------------------------------- #


def test_2a_json_inside_markdown_fence_extracts() -> None:
    """2a: JSON wrapped in a markdown fence extracts."""

    text = textwrap.dedent(
        f"""\
        Sure, here is the email draft:

        ```json
        {_VALID_JSON}
        ```

        Let me know if you need changes.
        """
    )
    payload = _validate(text)
    assert payload.email_subject == "Idea for Acme"


def test_2b_json_inside_loose_prose_extracts() -> None:
    """2b: JSON embedded in prose extracts via first-`{` to last-`}`."""

    text = f"prefix garbage {_VALID_JSON} suffix garbage"
    payload = _validate(text)
    assert payload.confidence == Confidence.HIGH


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

    ``personalization_notes`` is intentionally NOT in this loop because
    the schema gives it ``default_factory=list``; an omitted field
    materialises as ``[]`` from the default and Pydantic v2 does not
    re-apply ``min_length=1`` to defaults. Test 9 covers the
    explicit-empty-list rejection instead.
    """

    base = {
        "email_subject": "Idea for Acme",
        "email_body": _BODY_OK,
        "personalization_notes": ["n"],
    }
    for missing in ("email_subject", "email_body"):
        partial = {k: v for k, v in base.items() if k != missing}
        with pytest.raises(ValidationError):
            EmailDraftSynthesisPayload.model_validate(partial)


# --------------------------------------------------------------------------- #
# 5. Empty required strings                                                   #
# --------------------------------------------------------------------------- #


def test_5_empty_required_strings_fail() -> None:
    """5: ``min_length=1`` is enforced on ``email_subject``;
    ``min_length=50`` on ``email_body``."""

    with pytest.raises(ValidationError):
        EmailDraftSynthesisPayload(
            email_subject="",
            email_body=_BODY_OK,
            personalization_notes=["n"],
        )
    with pytest.raises(ValidationError):
        EmailDraftSynthesisPayload(
            email_subject="Idea for Acme",
            email_body="",
            personalization_notes=["n"],
        )


# --------------------------------------------------------------------------- #
# 6. email_subject too long                                                   #
# --------------------------------------------------------------------------- #


def test_6_email_subject_over_120_chars_fails() -> None:
    """6: ``email_subject`` over 120 chars fails validation."""

    long_subject = "x" * 121
    with pytest.raises(ValidationError):
        EmailDraftSynthesisPayload(
            email_subject=long_subject,
            email_body=_BODY_OK,
            personalization_notes=["n"],
        )


# --------------------------------------------------------------------------- #
# 7. email_body too short                                                     #
# --------------------------------------------------------------------------- #


def test_7_email_body_under_50_chars_fails() -> None:
    """7: ``email_body`` under 50 chars fails validation."""

    with pytest.raises(ValidationError):
        EmailDraftSynthesisPayload(
            email_subject="Idea for Acme",
            email_body="too short.",
            personalization_notes=["n"],
        )


# --------------------------------------------------------------------------- #
# 8. email_body too long                                                      #
# --------------------------------------------------------------------------- #


def test_8_email_body_over_1800_chars_fails() -> None:
    """8: ``email_body`` over 1800 chars fails validation."""

    body = "x" * 1801
    with pytest.raises(ValidationError):
        EmailDraftSynthesisPayload(
            email_subject="Idea for Acme",
            email_body=body,
            personalization_notes=["n"],
        )


# --------------------------------------------------------------------------- #
# 9. personalization_notes empty                                              #
# --------------------------------------------------------------------------- #


def test_9_personalization_notes_empty_fails() -> None:
    """9: empty personalization_notes fails (min_length=1)."""

    with pytest.raises(ValidationError):
        EmailDraftSynthesisPayload(
            email_subject="Idea for Acme",
            email_body=_BODY_OK,
            personalization_notes=[],
        )


# --------------------------------------------------------------------------- #
# 10. personalization_notes too long                                          #
# --------------------------------------------------------------------------- #


def test_10_personalization_notes_over_five_fails() -> None:
    """10: more than 5 personalization_notes fails (max_length=5)."""

    with pytest.raises(ValidationError):
        EmailDraftSynthesisPayload(
            email_subject="Idea for Acme",
            email_body=_BODY_OK,
            personalization_notes=[f"n{i}" for i in range(6)],
        )


# --------------------------------------------------------------------------- #
# 11. Lowercase confidence normalises                                         #
# --------------------------------------------------------------------------- #


def test_11_lowercase_confidence_normalises() -> None:
    """11: Lowercase confidence string normalises to the enum."""

    for raw, expected in (
        ("high", Confidence.HIGH),
        ("medium", Confidence.MEDIUM),
        ("low", Confidence.LOW),
        ("HIGH", Confidence.HIGH),
        ("Medium", Confidence.MEDIUM),
    ):
        payload = EmailDraftSynthesisPayload(
            email_subject="Idea for Acme",
            email_body=_BODY_OK,
            personalization_notes=["n"],
            confidence=raw,  # type: ignore[arg-type]
        )
        assert payload.confidence == expected


def test_11b_invalid_confidence_still_rejected() -> None:
    """11b: an out-of-vocabulary confidence value still fails."""

    with pytest.raises(ValidationError):
        EmailDraftSynthesisPayload(
            email_subject="Idea for Acme",
            email_body=_BODY_OK,
            personalization_notes=["n"],
            confidence="supercritical",  # type: ignore[arg-type]
        )


# --------------------------------------------------------------------------- #
# 12. No eval / unsafe parsing                                                #
# --------------------------------------------------------------------------- #


def test_12_no_eval_or_unsafe_parsing_imports_present() -> None:
    """12: ``json_utils.py`` must not rely on ``eval`` / ``literal_eval``."""

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
