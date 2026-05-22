"""Unit tests for the Phase 5.9 QA Evaluator Agent service.

Test IDs map 1:1 to the Phase 5.9 spec (S-01 .. S-24).
"""

from __future__ import annotations

import importlib
import inspect
import json

from app.agents.qa_evaluator_agent import QAEvaluatorAgentService
from app.schemas.agents import (
    QAEvaluatorAgentInput,
    QAEvaluatorAgentOutput,
)
from app.schemas.common import (
    Confidence,
    EvidenceSource,
    HallucinationRisk,
    Recommendation,
    RunMode,
)
from app.schemas.lead import LeadIn
from app.schemas.model import (
    ModelCostEstimate,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)
from app.schemas.qa import EvidenceCard
from app.services.model_service import BaseModelService, MockModelService


# --------------------------------------------------------------------------- #
# Fixture factories                                                           #
# --------------------------------------------------------------------------- #


def _lead(**overrides) -> LeadIn:
    base = dict(
        lead_id="lead_qa_001",
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


def _good_email_body() -> str:
    return (
        "Hi Sarah, I'm reaching out because of how teams at Acme Corp "
        "often spend disproportionate time on lead research and "
        "qualification before outreach. LeadForge can help structure "
        "that work into a reviewable, prioritized pipeline. Would it "
        "be worth a quick look? Happy to share a short example."
    )


def _evidence_card(idx: int = 1) -> EvidenceCard:
    return EvidenceCard(
        id=f"ev_{idx:02d}",
        headline="Sample evidence",
        description="Sample evidence description.",
        confidence=Confidence.HIGH,
        source_type=EvidenceSource.DEMO_CONTEXT,
    )


def _input_for(
    *,
    lead: LeadIn | None = None,
    email_subject: str = "Idea for Acme Corp",
    email_body: str | None = None,
    evidence_cards: list[EvidenceCard] | None = None,
    personalization_notes: list[str] | None = None,
) -> QAEvaluatorAgentInput:
    return QAEvaluatorAgentInput(
        lead=lead if lead is not None else _lead(),
        email_subject=email_subject,
        email_body=email_body if email_body is not None else _good_email_body(),
        evidence_cards=(
            evidence_cards if evidence_cards is not None else [_evidence_card()]
        ),
        personalization_notes=(
            personalization_notes
            if personalization_notes is not None
            else ["Reference company name: Acme Corp."]
        ),
        run_id="test_run_001",
    )


def _valid_qa_json(
    *,
    qa_score: int = 85,
    personalization: int = 80,
    evidence_coverage: int = 80,
    cta_quality: int = 80,
    tone_match: int = 85,
    hallucination_risk: str = "low",
    recommendation: str = "review",
    strengths: list[str] | None = None,
    risks: list[str] | None = None,
    required_fixes: list[str] | None = None,
) -> str:
    return json.dumps(
        {
            "qa_score": qa_score,
            "personalization": personalization,
            "evidence_coverage": evidence_coverage,
            "cta_quality": cta_quality,
            "tone_match": tone_match,
            "hallucination_risk": hallucination_risk,
            "recommendation": recommendation,
            "strengths": strengths if strengths is not None else ["clear CTA"],
            "risks": risks if risks is not None else ["thin context"],
            "required_fixes": (
                required_fixes if required_fixes is not None else ["add lead source"]
            ),
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


def test_s01_default_returns_qa_evaluator_output() -> None:
    """S-01: Default deterministic behavior returns QAEvaluatorAgentOutput."""

    output = QAEvaluatorAgentService().run(_input_for())
    assert isinstance(output, QAEvaluatorAgentOutput)
    assert output.lead_id == "lead_qa_001"


def test_s02_result_success_is_true() -> None:
    """S-02: result.success is True."""

    output = QAEvaluatorAgentService().run(_input_for())
    assert output.result.success is True
    assert output.result.error is None


def test_s03_metadata_agent_name_is_qa_evaluator_agent() -> None:
    """S-03: metadata.agent_name == "qa_evaluator_agent"."""

    output = QAEvaluatorAgentService().run(_input_for())
    assert output.result.metadata.agent_name == "qa_evaluator_agent"


def test_s04_metadata_run_mode_is_simulation() -> None:
    """S-04: metadata.run_mode == RunMode.SIMULATION."""

    output = QAEvaluatorAgentService().run(_input_for())
    assert output.result.metadata.run_mode == RunMode.SIMULATION


def test_s05_metadata_simulated_is_true_by_default() -> None:
    """S-05: metadata.simulated is True by default."""

    output = QAEvaluatorAgentService().run(_input_for())
    assert output.result.metadata.simulated is True


def test_s06_metadata_tokens_zero_and_cost_zero_dollars() -> None:
    """S-06: metadata.tokens == 0 and metadata.cost == "$0.00" by default."""

    output = QAEvaluatorAgentService().run(_input_for())
    assert output.result.metadata.tokens == 0
    assert output.result.metadata.cost == "$0.00"
    assert output.result.metadata.model == "none"
    assert (
        output.result.metadata.prompt_version
        == "qa_evaluator_agent_deterministic_v1"
    )


# --------------------------------------------------------------------------- #
# S-07 .. S-13 — deterministic content semantics                              #
# --------------------------------------------------------------------------- #


def test_s07_good_draft_gets_high_qa_score_and_review_recommendation() -> None:
    """S-07: A clean draft gets a high qa_score and a REVIEW
    recommendation (the portfolio version never auto-approves)."""

    output = QAEvaluatorAgentService().run(_input_for())
    assert output.qa_score == 100
    assert output.hallucination_risk == HallucinationRisk.LOW
    assert output.recommendation == Recommendation.REVIEW


def test_s08_fake_live_research_claim_triggers_high_hallucination_risk() -> None:
    """S-08: A live-research claim triggers HIGH hallucination_risk and
    a non-approve (REGENERATE) recommendation."""

    body = (
        "Hi Sarah, we found on your website that Acme raised a Series B. "
        "LeadForge can help. Would it be worth a quick look?"
    )
    output = QAEvaluatorAgentService().run(_input_for(email_body=body))
    assert output.hallucination_risk == HallucinationRisk.HIGH
    assert output.recommendation == Recommendation.REGENERATE
    assert output.qa_score <= 100 - 30


def test_s09_manipulative_urgency_is_penalised() -> None:
    """S-09: Manipulative urgency phrasing is penalised."""

    body = (
        "Hi Sarah, why wait? Act now. LeadForge can help structure your "
        "outreach. Would it be worth a quick look?"
    )
    baseline_score = QAEvaluatorAgentService().run(_input_for()).qa_score
    urgent_score = QAEvaluatorAgentService().run(_input_for(email_body=body)).qa_score
    assert urgent_score < baseline_score
    assert urgent_score <= 100 - 20


def test_s10_guaranteed_outcome_is_penalised() -> None:
    """S-10: Guaranteed-outcome phrasing is penalised."""

    body = (
        "Hi Sarah, LeadForge is guaranteed to increase your pipeline "
        "quality. Would it be worth a quick look?"
    )
    output = QAEvaluatorAgentService().run(_input_for(email_body=body))
    assert output.qa_score <= 100 - 25
    assert output.hallucination_risk in (
        HallucinationRisk.MEDIUM,
        HallucinationRisk.HIGH,
    )


def test_s11_delivery_metadata_is_penalised() -> None:
    """S-11: Email body containing delivery / SMTP metadata is penalised."""

    body = (
        "Hi Sarah, this email was sent on behalf of LeadForge "
        "(message-id: 12345). Would it be worth a quick look?"
    )
    output = QAEvaluatorAgentService().run(_input_for(email_body=body))
    assert output.qa_score <= 100 - 25
    assert output.recommendation == Recommendation.REGENERATE


def test_s12_missing_cta_is_penalised() -> None:
    """S-12: Email body lacking a soft CTA is penalised."""

    body = (
        "Hi Sarah, I'm reaching out because LeadForge can help structure "
        "your outreach for Acme Corp's prospecting workflow. We focus on "
        "research and qualification."
    )
    output = QAEvaluatorAgentService().run(_input_for(email_body=body))
    assert any("[FIX] Add a low-pressure CTA" in note for note in output.qa_notes)
    assert output.qa_score <= 100 - 10


def test_s13_context_limited_lead_with_aggressive_email_is_penalised() -> None:
    """S-13: A LOW-context lead combined with aggressive (urgency + no
    CTA) phrasing is penalised heavily."""

    bad_body = (
        "Why wait — act now. LeadForge is guaranteed to deliver pipeline "
        "results. (This is for your team.)"
    )
    output = QAEvaluatorAgentService().run(
        _input_for(
            lead=_lead(
                industry=None,
                country=None,
                employee_count=None,
                contact_role=None,
            ),
            email_body=bad_body,
            evidence_cards=[],
            personalization_notes=[],
        )
    )
    assert output.recommendation == Recommendation.REGENERATE
    assert output.qa_score < 50


# --------------------------------------------------------------------------- #
# S-14 .. S-17 — synthesis flag behaviour                                     #
# --------------------------------------------------------------------------- #


def test_s14_flag_false_with_fake_groq_does_not_consume_content() -> None:
    """S-14: use_model_synthesis=False ignores model content."""

    fake = _FakeGroqLikeModelService(
        content=_valid_qa_json(qa_score=10, recommendation="approve")
    )
    output = QAEvaluatorAgentService(
        model_service=fake, use_model_synthesis=False
    ).run(_input_for())
    assert output.qa_score == 100
    assert (
        output.result.metadata.prompt_version
        == "qa_evaluator_agent_deterministic_v1"
    )


def test_s15_flag_true_with_simulated_response_returns_deterministic() -> None:
    """S-15: use_model_synthesis=True with simulated response returns
    deterministic output."""

    output = QAEvaluatorAgentService(
        model_service=MockModelService(), use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "qa_evaluator_agent_deterministic_v1"
    )
    assert output.result.metadata.simulated is True


def test_s16_flag_true_with_valid_json_consumes_payload() -> None:
    """S-16: use_model_synthesis=True + valid JSON + guardrails clean →
    LLM payload is consumed."""

    # Baseline qa_score for a clean input is 100; LLM proposes 95
    # (within +15) and adds a fresh strength note. With no hard
    # violations on the baseline, the LLM's REVIEW recommendation
    # is accepted.
    fake = _FakeGroqLikeModelService(
        content=_valid_qa_json(
            qa_score=95,
            strengths=["LLM saw a clean draft"],
            risks=["LLM noted a thin signal"],
            required_fixes=["LLM suggested adding one more anchor"],
        )
    )
    output = QAEvaluatorAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert output.qa_score == 95
    assert any("LLM saw a clean draft" in note for note in output.qa_notes)
    assert any("LLM suggested adding" in note for note in output.qa_notes)


def test_s17_valid_path_metadata_is_groq_json_v1_and_not_simulated() -> None:
    """S-17: Valid LLM path → prompt_version is
    ``qa_evaluator_agent_groq_json_v1`` and ``simulated`` is False."""

    fake = _FakeGroqLikeModelService(content=_valid_qa_json(qa_score=90))
    output = QAEvaluatorAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "qa_evaluator_agent_groq_json_v1"
    )
    assert output.result.metadata.simulated is False
    assert output.result.metadata.model == "llama-3.1-8b-instant"


# --------------------------------------------------------------------------- #
# S-18 .. S-21 — fallback / guardrail behaviour                               #
# --------------------------------------------------------------------------- #


def test_s18_invalid_json_triggers_fallback_with_note() -> None:
    """S-18: Invalid JSON triggers deterministic fallback + risk note +
    ``simulated=True``."""

    fake = _FakeGroqLikeModelService(content="garbage no json")
    output = QAEvaluatorAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "qa_evaluator_agent_groq_json_v1_fallback"
    )
    assert output.result.metadata.simulated is True
    assert any(
        "LLM QA evaluation failed" in note for note in output.qa_notes
    )


def test_s19_guardrail_violation_triggers_fallback() -> None:
    """S-19: Any guardrail violation triggers the deterministic fallback."""

    # LLM payload contains a forbidden live-research phrase in a risk.
    fake = _FakeGroqLikeModelService(
        content=_valid_qa_json(
            qa_score=90,
            risks=["we found on your website that the team is hiring"],
        )
    )
    output = QAEvaluatorAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "qa_evaluator_agent_groq_json_v1_fallback"
    )


def test_s20_llm_cannot_approve_when_baseline_has_hard_violation() -> None:
    """S-20: When the deterministic baseline detected a hard violation,
    the LLM cannot make the recommendation more permissive — even an
    APPROVE proposal from the LLM routes to the fallback."""

    # Bad body so baseline → REGENERATE; LLM tries to APPROVE anyway.
    bad_body = (
        "Hi Sarah, this email was sent. LeadForge is guaranteed to help. "
        "Would it be worth a quick look?"
    )
    fake = _FakeGroqLikeModelService(
        content=_valid_qa_json(
            qa_score=90,
            hallucination_risk="low",
            recommendation="approve",
        )
    )
    output = QAEvaluatorAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for(email_body=bad_body))
    assert output.recommendation == Recommendation.REGENERATE
    assert (
        output.result.metadata.prompt_version
        == "qa_evaluator_agent_groq_json_v1_fallback"
    )


def test_s21_llm_score_inflation_over_fifteen_triggers_fallback() -> None:
    """S-21: An LLM qa_score more than 15 above the deterministic
    baseline routes to the fallback.

    Baseline for a no-CTA body is 90 (qa_score=100 - 10 deduction);
    LLM proposes 100 → diff=10 → accepted. Construct a body that
    triggers two soft deductions (no-CTA + no-company) so the
    baseline is 80; LLM proposes 100 → diff=20 → fallback.
    """

    bad_body = (
        # No CTA, no company name → -10 -10 = baseline 80.
        "Hi there, I'm reaching out about your prospecting workflow. "
        "LeadForge focuses on research and qualification, and may be a "
        "fit for the way your team currently operates."
    )
    fake = _FakeGroqLikeModelService(content=_valid_qa_json(qa_score=100))
    output = QAEvaluatorAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for(email_body=bad_body))
    assert (
        output.result.metadata.prompt_version
        == "qa_evaluator_agent_groq_json_v1_fallback"
    )


# --------------------------------------------------------------------------- #
# S-22 .. S-24 — failure safety + "never sends email"                         #
# --------------------------------------------------------------------------- #


def test_s22_unexpected_model_failure_returns_safe_success_false() -> None:
    """S-22: Unexpected model failure returns ``success=False`` with a
    safe fallback output (qa_score=0, REGENERATE, HIGH risk)."""

    class _Explode(BaseModelService):
        def complete(self, request):  # noqa: D401
            raise RuntimeError("synthesis exploded")

    output = QAEvaluatorAgentService(
        model_service=_Explode(), use_model_synthesis=True
    ).run(_input_for())
    assert output.result.success is False
    assert output.result.error is not None
    assert output.result.error.code == "qa_evaluator_agent_error"
    assert output.qa_score == 0
    assert output.recommendation == Recommendation.REGENERATE
    assert output.hallucination_risk == HallucinationRisk.HIGH


def test_s23_no_raw_model_response_leaked() -> None:
    """S-23: Raw model response is not leaked through error messages or
    fallback notes."""

    secret_marker = "MODEL_RAW_DUMP_THAT_SHOULD_NEVER_LEAK"

    # Invalid-JSON fallback path.
    fake = _FakeGroqLikeModelService(content=f"prefix {secret_marker} suffix")
    output = QAEvaluatorAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    blob = " ".join(output.qa_notes)
    assert secret_marker not in blob

    # Unexpected-failure path.
    class _LeakyFailure(BaseModelService):
        def complete(self, request):  # noqa: D401
            raise RuntimeError("benign agent failure")

    output2 = QAEvaluatorAgentService(
        model_service=_LeakyFailure(), use_model_synthesis=True
    ).run(_input_for())
    assert output2.result.error is not None
    assert secret_marker not in output2.result.error.message


def test_s24_service_never_imports_smtp_or_defines_send() -> None:
    """S-24: The agent module never imports SMTP / email transport
    libraries and does not define any callable named ``send_*`` /
    ``deliver_*`` / ``transport`` / ``smtp`` — the QA Evaluator only
    evaluates."""

    mod = importlib.import_module("app.agents.qa_evaluator_agent")
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
