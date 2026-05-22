"""Unit tests for the Phase 5.8 Email Drafter Agent service.

Test IDs map 1:1 to the Phase 5.8 spec (S-01 .. S-22).
"""

from __future__ import annotations

import importlib
import inspect
import json

from app.agents.email_drafter_agent import EmailDrafterAgentService
from app.schemas.agents import (
    EmailDrafterAgentInput,
    EmailDrafterAgentOutput,
)
from app.schemas.common import Confidence, RunMode
from app.schemas.lead import LeadIn
from app.schemas.model import (
    ModelCostEstimate,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)
from app.services.model_service import BaseModelService, MockModelService


# --------------------------------------------------------------------------- #
# Fixture factories                                                           #
# --------------------------------------------------------------------------- #


def _lead(**overrides) -> LeadIn:
    base = dict(
        lead_id="lead_email_001",
        company_name="Acme Corp",
        industry="B2B SaaS",
        country="United States",
        employee_count=140,
        contact_name="Sarah Whitmore",
        contact_role="VP Revenue Operations",
        website="acme.io",
        notes="Recently closed Series B; hiring three SDRs.",
    )
    base.update(overrides)
    return LeadIn(**base)


def _input_for(
    lead: LeadIn | None = None,
    *,
    company_summary: str | None = None,
    pain_hypothesis: str = "Pipeline quality at scale.",
    sales_angle: str = "Position LeadForge as the qualification layer.",
    core_message: str = "For Acme Corp, LeadForge structures outreach.",
    personalization_notes: list[str] | None = None,
) -> EmailDrafterAgentInput:
    return EmailDrafterAgentInput(
        lead=lead if lead is not None else _lead(),
        company_summary=(
            company_summary
            if company_summary is not None
            else "Acme is a growth-stage B2B SaaS company."
        ),
        pain_hypothesis=pain_hypothesis,
        sales_angle=sales_angle,
        core_message=core_message,
        personalization_notes=(
            personalization_notes
            if personalization_notes is not None
            else [
                "Reference company name: Acme Corp.",
                "Anchor to the B2B SaaS context.",
            ]
        ),
        run_id="test_run_001",
    )


def _valid_email_json(
    *,
    email_subject: str = "Idea for Acme Corp",
    email_body: str | None = None,
    personalization_notes: list[str] | None = None,
    confidence: str = "high",
) -> str:
    if email_body is None:
        email_body = (
            "Hi Sarah, I'm reaching out because of how teams at Acme Corp "
            "often spend disproportionate time on lead research and "
            "qualification before outreach. LeadForge can help structure "
            "that work into a reviewable, prioritized pipeline. Would it "
            "be worth a quick look? Happy to share a short example."
        )
    if personalization_notes is None:
        personalization_notes = ["LLM note 1", "LLM note 2"]
    return json.dumps(
        {
            "email_subject": email_subject,
            "email_body": email_body,
            "personalization_notes": personalization_notes,
            "confidence": confidence,
        }
    )


class _FakeGroqLikeModelService(BaseModelService):
    """Non-simulated test double."""

    def __init__(self, content: str) -> None:
        self.content = content

    def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            request_id=request.request_id,
            provider=ModelProvider.GROQ,
            model_name="llama-3.1-8b-instant",
            content=self.content,
            usage=ModelUsage(input_tokens=50, output_tokens=25, total_tokens=75),
            cost=ModelCostEstimate(
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0,
                display_cost="$0.0000",
            ),
            latency="123ms",
            finish_reason="stop",
            simulated=False,
        )


# --------------------------------------------------------------------------- #
# S-01 .. S-06 — deterministic defaults                                       #
# --------------------------------------------------------------------------- #


def test_s01_default_returns_email_drafter_output() -> None:
    """S-01: Default deterministic behavior returns EmailDrafterAgentOutput."""

    output = EmailDrafterAgentService().run(_input_for())
    assert isinstance(output, EmailDrafterAgentOutput)
    assert output.lead_id == "lead_email_001"


def test_s02_result_success_is_true() -> None:
    """S-02: result.success is True."""

    output = EmailDrafterAgentService().run(_input_for())
    assert output.result.success is True
    assert output.result.error is None


def test_s03_metadata_agent_name_is_email_drafter_agent() -> None:
    """S-03: metadata.agent_name == "email_drafter_agent"."""

    output = EmailDrafterAgentService().run(_input_for())
    assert output.result.metadata.agent_name == "email_drafter_agent"


def test_s04_metadata_run_mode_is_simulation() -> None:
    """S-04: metadata.run_mode == RunMode.SIMULATION."""

    output = EmailDrafterAgentService().run(_input_for())
    assert output.result.metadata.run_mode == RunMode.SIMULATION


def test_s05_metadata_simulated_is_true_by_default() -> None:
    """S-05: metadata.simulated is True by default."""

    output = EmailDrafterAgentService().run(_input_for())
    assert output.result.metadata.simulated is True


def test_s06_metadata_tokens_zero_and_cost_zero_dollars() -> None:
    """S-06: metadata.tokens == 0 and metadata.cost == "$0.00" by default."""

    output = EmailDrafterAgentService().run(_input_for())
    assert output.result.metadata.tokens == 0
    assert output.result.metadata.cost == "$0.00"
    assert output.result.metadata.model == "none"
    assert (
        output.result.metadata.prompt_version
        == "email_drafter_agent_deterministic_v1"
    )


# --------------------------------------------------------------------------- #
# S-07 .. S-11 — deterministic content semantics                              #
# --------------------------------------------------------------------------- #


def test_s07_deterministic_draft_has_non_empty_subject_and_body() -> None:
    """S-07: Deterministic draft has non-empty subject and body."""

    output = EmailDrafterAgentService().run(_input_for())
    assert output.email_subject.strip() != ""
    assert output.email_body.strip() != ""


def test_s08_draft_mentions_company_name_or_your_team() -> None:
    """S-08: Draft includes company_name or "your team"."""

    output = EmailDrafterAgentService().run(_input_for())
    blob = (output.email_subject + " " + output.email_body).lower()
    assert "acme corp" in blob or "your team" in blob


def test_s09_draft_includes_a_soft_cta() -> None:
    """S-09: Draft includes a soft CTA."""

    output = EmailDrafterAgentService().run(_input_for())
    lowered = output.email_body.lower()
    assert (
        "would it be worth" in lowered
        or "open to seeing" in lowered
        or "happy to share" in lowered
    )


def test_s10_draft_does_not_claim_live_web_research() -> None:
    """S-10: Draft does not claim live web research or public sources."""

    output = EmailDrafterAgentService().run(_input_for())
    blob = " ".join(
        [output.email_subject, output.email_body, *output.personalization_notes]
    ).lower()
    for forbidden in (
        "live web research",
        "we found on your website",
        "according to your website",
        "we saw online",
        "we noticed online",
        "according to news",
        "recent news about",
        "your recent funding",
        "we read that you",
    ):
        assert forbidden not in blob, f"forbidden phrase present: {forbidden!r}"


def test_s11_draft_does_not_say_it_was_sent() -> None:
    """S-11: Draft does not say it was sent."""

    output = EmailDrafterAgentService().run(_input_for())
    body_lower = output.email_body.lower()
    for marker in (
        "this email was sent",
        "sent on behalf of",
        "delivered via",
        "unsubscribe",
        "message-id:",
    ):
        assert marker not in body_lower, f"sent / delivery marker present: {marker!r}"


# --------------------------------------------------------------------------- #
# S-12 .. S-15 — synthesis flag behaviour                                     #
# --------------------------------------------------------------------------- #


def test_s12_flag_false_with_fake_groq_does_not_consume_content() -> None:
    """S-12: use_model_synthesis=False ignores model content."""

    fake = _FakeGroqLikeModelService(
        content=_valid_email_json(email_subject="LLM-only subject")
    )
    output = EmailDrafterAgentService(
        model_service=fake, use_model_synthesis=False
    ).run(_input_for())
    assert output.email_subject != "LLM-only subject"
    assert (
        output.result.metadata.prompt_version
        == "email_drafter_agent_deterministic_v1"
    )


def test_s13_flag_true_with_simulated_response_returns_deterministic() -> None:
    """S-13: use_model_synthesis=True with simulated response returns
    deterministic output (mock content is NOT consumed)."""

    output = EmailDrafterAgentService(
        model_service=MockModelService(), use_model_synthesis=True
    ).run(_input_for())
    blob = (output.email_subject + " " + output.email_body).lower()
    assert "[mock model response" not in blob
    assert (
        output.result.metadata.prompt_version
        == "email_drafter_agent_deterministic_v1"
    )
    assert output.result.metadata.simulated is True


def test_s14_flag_true_with_valid_json_consumes_payload() -> None:
    """S-14: use_model_synthesis=True with a valid JSON Groq response
    consumes the payload."""

    fake = _FakeGroqLikeModelService(
        content=_valid_email_json(
            email_subject="LLM refined subject",
            personalization_notes=["LLM note A", "LLM note B"],
        )
    )
    output = EmailDrafterAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert output.email_subject == "LLM refined subject"
    assert "LLM note A" in output.personalization_notes
    assert "LLM note B" in output.personalization_notes


def test_s15_valid_path_metadata_is_groq_json_v1_and_not_simulated() -> None:
    """S-15: Valid LLM path → prompt_version is
    ``email_drafter_agent_groq_json_v1`` and ``simulated`` is False."""

    fake = _FakeGroqLikeModelService(content=_valid_email_json())
    output = EmailDrafterAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "email_drafter_agent_groq_json_v1"
    )
    assert output.result.metadata.simulated is False
    assert output.result.metadata.model == "llama-3.1-8b-instant"


# --------------------------------------------------------------------------- #
# S-16 .. S-19 — fallback / guardrail behaviour                               #
# --------------------------------------------------------------------------- #


def test_s16_invalid_json_triggers_fallback_with_note() -> None:
    """S-16: Invalid JSON triggers deterministic fallback + fallback
    note and ``simulated=True``."""

    fake = _FakeGroqLikeModelService(content="garbage no json")
    output = EmailDrafterAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "email_drafter_agent_groq_json_v1_fallback"
    )
    assert output.result.metadata.simulated is True
    assert any(
        "LLM email draft failed" in note for note in output.personalization_notes
    )


def test_s17_forbidden_live_research_phrase_triggers_fallback() -> None:
    """S-17: A forbidden live-research phrase in the body triggers the
    deterministic fallback."""

    body = (
        "Hi Sarah, we found on your website that you raised your recent "
        "funding. LeadForge can help structure your outreach. Would it "
        "be worth a quick look?"
    )
    fake = _FakeGroqLikeModelService(content=_valid_email_json(email_body=body))
    output = EmailDrafterAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "email_drafter_agent_groq_json_v1_fallback"
    )
    assert output.result.metadata.simulated is True


def test_s18_manipulative_urgency_triggers_fallback() -> None:
    """S-18: Manipulative urgency phrasing in the body triggers fallback."""

    body = (
        "Hi Sarah, why wait — act now before this opportunity is gone. "
        "LeadForge can help structure your outreach. Would it be worth a "
        "quick look?"
    )
    fake = _FakeGroqLikeModelService(content=_valid_email_json(email_body=body))
    output = EmailDrafterAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "email_drafter_agent_groq_json_v1_fallback"
    )


def test_s19_guaranteed_outcome_triggers_fallback() -> None:
    """S-19: Guaranteed-outcome phrasing in the body triggers fallback."""

    body = (
        "Hi Sarah, LeadForge is guaranteed to increase your pipeline "
        "quality — you will see results in week one. Would it be worth "
        "a quick look?"
    )
    fake = _FakeGroqLikeModelService(content=_valid_email_json(email_body=body))
    output = EmailDrafterAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "email_drafter_agent_groq_json_v1_fallback"
    )


# --------------------------------------------------------------------------- #
# S-20 .. S-21 — failure safety                                               #
# --------------------------------------------------------------------------- #


def test_s20_unexpected_model_failure_returns_safe_success_false() -> None:
    """S-20: Unexpected model failure returns ``success=False`` with a
    safe fallback output."""

    class _Explode(BaseModelService):
        def complete(self, request):  # noqa: D401
            raise RuntimeError("synthesis exploded")

    output = EmailDrafterAgentService(
        model_service=_Explode(), use_model_synthesis=True
    ).run(_input_for())
    assert output.result.success is False
    assert output.result.error is not None
    assert output.result.error.code == "email_drafter_agent_error"
    assert output.email_subject == "Manual review required"
    assert (
        "Insufficient safe context" in output.email_body
    )
    assert output.personalization_notes == []  # FIX 3
    assert output.confidence == Confidence.LOW


def test_s21_no_raw_model_response_leaked() -> None:
    """S-21: Raw model response is not leaked through error messages or
    fallback notes."""

    secret_marker = "MODEL_RAW_DUMP_THAT_SHOULD_NEVER_LEAK"

    # Invalid-JSON fallback path.
    fake = _FakeGroqLikeModelService(content=f"prefix {secret_marker} suffix")
    output = EmailDrafterAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    blob = " ".join(
        [output.email_subject, output.email_body, *output.personalization_notes]
    )
    assert secret_marker not in blob

    # Unexpected-failure path.
    class _LeakyFailure(BaseModelService):
        def complete(self, request):  # noqa: D401
            raise RuntimeError(
                "benign agent failure"
            )

    output2 = EmailDrafterAgentService(
        model_service=_LeakyFailure(), use_model_synthesis=True
    ).run(_input_for())
    assert output2.result.error is not None
    assert secret_marker not in output2.result.error.message


# --------------------------------------------------------------------------- #
# S-22 — the service never sends email                                        #
# --------------------------------------------------------------------------- #


def test_s22_service_never_imports_smtp_or_defines_send() -> None:
    """S-22: The agent module never imports SMTP / email transport
    libraries and does not define any callable named ``send``,
    ``deliver``, or similar — the agent only drafts."""

    mod = importlib.import_module("app.agents.email_drafter_agent")
    source = inspect.getsource(mod)

    code_lines = [
        line for line in source.splitlines()
        if not line.lstrip().startswith(("#", '"', "'"))
    ]
    for line in code_lines:
        stripped = line.strip()
        for forbidden_import in (
            "import smtplib",
            "from smtplib",
            "import email.mime",
            "from email.mime",
            "import aiosmtplib",
            "from aiosmtplib",
        ):
            assert forbidden_import not in stripped, (
                f"forbidden import detected: {line!r}"
            )

    # No callable named ``send`` / ``deliver`` exists at module level.
    for forbidden_attr in (
        "send_email",
        "send_message",
        "deliver_email",
        "transport",
        "smtp",
    ):
        assert not hasattr(mod, forbidden_attr), (
            f"module exposes forbidden attribute: {forbidden_attr!r}"
        )
