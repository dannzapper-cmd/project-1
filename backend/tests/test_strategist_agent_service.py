"""Unit tests for the Phase 5.7 Strategist Agent service.

Test IDs map 1:1 to the Phase 5.7 spec (S-01 .. S-20).
"""

from __future__ import annotations

import json

from app.agents.strategist_agent import StrategistAgentService
from app.schemas.agents import StrategistAgentInput, StrategistAgentOutput
from app.schemas.common import Confidence, Priority, RunMode
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
        lead_id="lead_strategist_001",
        company_name="Acme Corp",
        industry="B2B SaaS",
        country="United States",
        employee_count=140,
        contact_name="Sample Person",
        contact_role="VP Revenue Operations",
        website="acme.io",
        notes="Recently closed Series B; hiring three SDRs.",
    )
    base.update(overrides)
    return LeadIn(**base)


def _input_for(
    lead: LeadIn | None = None,
    *,
    fit_score: int = 92,
    priority: Priority = Priority.HIGH,
    opportunity_signals: list[str] | None = None,
    pain_hypotheses: list[str] | None = None,
    company_summary: str | None = None,
) -> StrategistAgentInput:
    return StrategistAgentInput(
        lead=lead if lead is not None else _lead(),
        company_summary=(
            company_summary
            if company_summary is not None
            else "Acme is a growth-stage B2B SaaS company."
        ),
        # Use explicit ``is None`` checks so an explicit ``[]`` survives
        # (falsy ``or`` would silently fall back to the defaults and the
        # S-08 empty-context test would never see an empty list).
        opportunity_signals=(
            opportunity_signals
            if opportunity_signals is not None
            else ["Hiring SDRs", "Series B"]
        ),
        pain_hypotheses=(
            pain_hypotheses
            if pain_hypotheses is not None
            else ["Pipeline quality at scale"]
        ),
        fit_score=fit_score,
        priority=priority,
        run_id="test_run_001",
    )


def _valid_strategist_synthesis_json(
    *,
    pain_hypothesis: str = "Refined pain.",
    pain_confidence: str = "high",
    sales_angle: str = "Position LeadForge as the qualification layer.",
    core_message: str = "For Acme Corp, LeadForge structures outreach.",
    likely_objection: str = "We already have a CRM.",
    personalization_notes: list[str] | None = None,
) -> str:
    return json.dumps(
        {
            "pain_hypothesis": pain_hypothesis,
            "pain_confidence": pain_confidence,
            "sales_angle": sales_angle,
            "core_message": core_message,
            "likely_objection": likely_objection,
            "personalization_notes": personalization_notes
            or ["LLM note 1", "LLM note 2"],
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
# S-01 .. S-06 — deterministic default                                        #
# --------------------------------------------------------------------------- #


def test_s01_default_returns_strategist_agent_output() -> None:
    """S-01: Default deterministic behavior returns StrategistAgentOutput."""

    output = StrategistAgentService().run(_input_for())
    assert isinstance(output, StrategistAgentOutput)
    assert output.lead_id == "lead_strategist_001"


def test_s02_result_success_is_true() -> None:
    """S-02: result.success is True."""

    output = StrategistAgentService().run(_input_for())
    assert output.result.success is True
    assert output.result.error is None


def test_s03_metadata_agent_name_is_strategist_agent() -> None:
    """S-03: metadata.agent_name == "strategist_agent"."""

    output = StrategistAgentService().run(_input_for())
    assert output.result.metadata.agent_name == "strategist_agent"


def test_s04_metadata_run_mode_is_simulation() -> None:
    """S-04: metadata.run_mode == RunMode.SIMULATION ("simulation")."""

    output = StrategistAgentService().run(_input_for())
    assert output.result.metadata.run_mode == RunMode.SIMULATION
    assert output.result.metadata.run_mode.value == "simulation"


def test_s05_metadata_simulated_is_true_by_default() -> None:
    """S-05: metadata.simulated is True by default."""

    output = StrategistAgentService().run(_input_for())
    assert output.result.metadata.simulated is True


def test_s06_metadata_tokens_zero_and_cost_zero_dollars() -> None:
    """S-06: metadata.tokens == 0 and metadata.cost == "$0.00" by default."""

    output = StrategistAgentService().run(_input_for())
    assert output.result.metadata.tokens == 0
    assert output.result.metadata.cost == "$0.00"
    assert output.result.metadata.model == "none"
    assert (
        output.result.metadata.prompt_version
        == "strategist_agent_deterministic_v1"
    )


# --------------------------------------------------------------------------- #
# S-07 .. S-11 — deterministic content semantics                              #
# --------------------------------------------------------------------------- #


def test_s07_strong_high_priority_lead_has_non_empty_strategy() -> None:
    """S-07: Strong high-priority lead gets non-empty pain_hypothesis,
    sales_angle, core_message."""

    output = StrategistAgentService().run(_input_for())
    assert output.pain_hypothesis.strip() != ""
    assert output.sales_angle.strip() != ""
    assert output.core_message.strip() != ""


def test_s08_empty_signals_and_pains_produces_conservative_hypothesis() -> None:
    """S-08: Empty pain_hypotheses and signals produces a conservative
    generic hypothesis."""

    output = StrategistAgentService().run(
        _input_for(
            opportunity_signals=[],
            pain_hypotheses=[],
            fit_score=30,
            priority=Priority.LOW,
        )
    )
    assert "fragmented prospecting" in output.pain_hypothesis.lower()
    assert output.pain_confidence == Confidence.LOW


def test_s09_low_priority_lead_has_cautious_sales_angle() -> None:
    """S-09: LOW priority lead gets a cautious / discovery-oriented angle."""

    output = StrategistAgentService().run(
        _input_for(fit_score=20, priority=Priority.LOW)
    )
    lowered = output.sales_angle.lower()
    assert any(
        keyword in lowered
        for keyword in ("cautious", "discovery", "validate")
    )


def test_s10_personalization_notes_between_two_and_five_with_context() -> None:
    """S-10: personalization_notes has between 2 and 5 notes when enough
    context exists."""

    output = StrategistAgentService().run(_input_for())
    assert 2 <= len(output.personalization_notes) <= 5


def test_s11_output_does_not_claim_live_web_research() -> None:
    """S-11: output text never claims live web research or public sources."""

    output = StrategistAgentService().run(_input_for())
    blob = " ".join(
        [
            output.pain_hypothesis,
            output.sales_angle,
            output.core_message,
            output.likely_objection,
            " ".join(output.personalization_notes),
        ]
    ).lower()
    for forbidden in (
        "live web research",
        "scraped",
        "according to your website",
        "we found online",
        "i found online",
        "recent news about",
        "your recent funding",
        "we noticed online",
    ):
        assert forbidden not in blob, f"forbidden phrase present: {forbidden!r}"


# --------------------------------------------------------------------------- #
# S-12 .. S-15 — synthesis flag behaviour                                     #
# --------------------------------------------------------------------------- #


def test_s12_flag_false_with_fake_groq_does_not_consume_content() -> None:
    """S-12: use_model_synthesis=False ignores model content."""

    fake = _FakeGroqLikeModelService(
        content=_valid_strategist_synthesis_json(
            pain_hypothesis="LLM-only pain"
        )
    )
    output = StrategistAgentService(
        model_service=fake, use_model_synthesis=False
    ).run(_input_for())
    assert output.pain_hypothesis != "LLM-only pain"
    assert (
        output.result.metadata.prompt_version
        == "strategist_agent_deterministic_v1"
    )


def test_s13_flag_true_with_simulated_response_returns_deterministic() -> None:
    """S-13: use_model_synthesis=True with simulated response returns
    deterministic output (mock content is not consumed)."""

    output = StrategistAgentService(
        model_service=MockModelService(), use_model_synthesis=True
    ).run(_input_for())
    blob = " ".join(output.personalization_notes + [output.core_message])
    assert "[MOCK MODEL RESPONSE" not in blob
    assert (
        output.result.metadata.prompt_version
        == "strategist_agent_deterministic_v1"
    )
    assert output.result.metadata.simulated is True


def test_s14_flag_true_with_valid_json_consumes_payload() -> None:
    """S-14: use_model_synthesis=True with a valid JSON Groq response
    consumes the payload."""

    fake = _FakeGroqLikeModelService(
        content=_valid_strategist_synthesis_json(
            pain_hypothesis="Refined LLM pain",
            sales_angle="Position LeadForge as the qualification layer.",
            personalization_notes=["LLM note A", "LLM note B"],
        )
    )
    output = StrategistAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert output.pain_hypothesis == "Refined LLM pain"
    assert "qualification layer" in output.sales_angle.lower()
    assert "LLM note A" in output.personalization_notes


def test_s15_valid_path_metadata_is_groq_json_v1_and_not_simulated() -> None:
    """S-15: Valid LLM path → prompt_version is
    ``strategist_agent_groq_json_v1`` and ``simulated`` is False."""

    fake = _FakeGroqLikeModelService(content=_valid_strategist_synthesis_json())
    output = StrategistAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "strategist_agent_groq_json_v1"
    )
    assert output.result.metadata.simulated is False
    assert output.result.metadata.model == "llama-3.1-8b-instant"


# --------------------------------------------------------------------------- #
# S-16 .. S-18 — fallback / guardrail behaviour                               #
# --------------------------------------------------------------------------- #


def test_s16_invalid_json_triggers_fallback_with_note() -> None:
    """S-16: Invalid JSON triggers deterministic fallback with fallback
    note and ``simulated=True``."""

    fake = _FakeGroqLikeModelService(content="garbage no json")
    output = StrategistAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "strategist_agent_groq_json_v1_fallback"
    )
    assert output.result.metadata.simulated is True
    assert any(
        "LLM strategy failed" in note for note in output.personalization_notes
    )


def test_s17_guardrail_forbidden_phrase_triggers_fallback() -> None:
    """S-17: A forbidden live-research phrase in any synthesised field
    triggers the deterministic fallback."""

    # core_message claims live research → fallback.
    fake = _FakeGroqLikeModelService(
        content=_valid_strategist_synthesis_json(
            core_message=(
                "We found on your website that you raised your recent funding. "
                "We are reaching out."
            )
        )
    )
    output = StrategistAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    assert (
        output.result.metadata.prompt_version
        == "strategist_agent_groq_json_v1_fallback"
    )
    assert output.result.metadata.simulated is True


def test_s18_low_priority_aggressive_sales_angle_triggers_fallback() -> None:
    """S-18: LOW priority lead + aggressive (non-cautious) sales_angle
    triggers the deterministic fallback."""

    fake = _FakeGroqLikeModelService(
        content=_valid_strategist_synthesis_json(
            sales_angle="Close them this week with an aggressive demo.",
        )
    )
    output = StrategistAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for(fit_score=20, priority=Priority.LOW))
    assert (
        output.result.metadata.prompt_version
        == "strategist_agent_groq_json_v1_fallback"
    )
    # And the deterministic LOW angle is what the caller sees.
    assert any(
        keyword in output.sales_angle.lower()
        for keyword in ("cautious", "discovery", "validate")
    )


# --------------------------------------------------------------------------- #
# S-19 .. S-20 — failure safety                                               #
# --------------------------------------------------------------------------- #


def test_s19_unexpected_model_failure_returns_safe_success_false() -> None:
    """S-19: Unexpected model failure returns ``success=False`` with a
    safe fallback output."""

    class _Explode(BaseModelService):
        def complete(self, request):  # noqa: D401
            raise RuntimeError("synthesis exploded")

    output = StrategistAgentService(
        model_service=_Explode(), use_model_synthesis=True
    ).run(_input_for())
    assert output.result.success is False
    assert output.result.error is not None
    assert output.result.error.code == "strategist_agent_error"
    assert output.pain_confidence == Confidence.LOW
    assert "Strategy agent failed" in output.pain_hypothesis
    assert output.personalization_notes == []


def test_s20_no_raw_model_response_leaked() -> None:
    """S-20: Raw model response is not leaked through error messages or
    fallback notes."""

    secret_marker = "MODEL_RAW_DUMP_THAT_SHOULD_NEVER_LEAK"

    # Invalid-JSON fallback path.
    fake = _FakeGroqLikeModelService(content=f"prefix {secret_marker} suffix")
    output = StrategistAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for())
    blob = " ".join(
        [
            output.pain_hypothesis,
            output.sales_angle,
            output.core_message,
            output.likely_objection,
            " ".join(output.personalization_notes),
        ]
    )
    assert secret_marker not in blob

    # Unexpected-failure path.
    class _LeakyFailure(BaseModelService):
        def complete(self, request):  # noqa: D401
            raise RuntimeError("benign agent failure")

    output2 = StrategistAgentService(
        model_service=_LeakyFailure(), use_model_synthesis=True
    ).run(_input_for())
    assert output2.result.error is not None
    assert secret_marker not in output2.result.error.message
