"""Unit tests for the Phase 5.5A Research Agent service.

Test IDs map 1:1 to the Phase 5.5A spec (S-01 .. S-14).
"""

from __future__ import annotations

from app.agents.research_agent import ResearchAgentService
from app.schemas.agents import ResearchAgentInput, ResearchAgentOutput
from app.schemas.common import Confidence, EvidenceSource, RunMode
from app.schemas.lead import LeadIn
from app.schemas.model import (
    ModelConfig,
    ModelCostEstimate,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)
from app.services.model_service import BaseModelService, MockModelService


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _lead(**overrides) -> LeadIn:
    base = dict(
        lead_id="lead_test_001",
        company_name="Veltrix Systems",
        industry="B2B SaaS",
        country="United States",
        employee_count=140,
        contact_name="Sarah Whitmore",
        contact_role="VP Revenue Operations",
        website="veltrixsystems.io",
        notes="Recently closed Series B.",
    )
    base.update(overrides)
    return LeadIn(**base)


def _rich_context() -> dict:
    return {
        "lead_id": "lead_test_001",
        "company_name": "Veltrix Systems",
        "research_status": "complete",
        "company_summary": "Veltrix is a growth-stage B2B SaaS company.",
        "recommended_research_summary": "Solid Tier 1 SaaS fit with strong signals.",
        "opportunity_signals": [
            {"signal": "Hiring SDRs", "confidence": "high"},
            {"signal": "Series B raised", "confidence": "high"},
            {"signal": "Mid-market expansion", "confidence": "medium"},
        ],
        "pain_hypotheses": [
            {"pain": "Pipeline quality at scale", "confidence": "high"}
        ],
        "evidence_cards": [
            {
                "title": "Hiring evidence",
                "description": "Three SDR roles open simultaneously.",
                "source_type": "synthetic_demo_context",
                "confidence": "high",
            },
            {
                "title": "Funding evidence",
                "description": "Series B closed last quarter.",
                "source_type": "synthetic_demo_context",
                "confidence": "high",
            },
        ],
        "information_risks": ["Budget authority unverified."],
    }


def _run_default(
    overrides_lead: dict | None = None,
    *,
    context: dict | None = None,
) -> ResearchAgentOutput:
    service = ResearchAgentService()
    return service.run(
        ResearchAgentInput(
            lead=_lead(**(overrides_lead or {})),
            run_id="run_test",
            available_context=context if context is not None else _rich_context(),
        )
    )


class _FaultyModelService(BaseModelService):
    """Helper for S-13: raises on every call."""

    def complete(self, request: ModelRequest) -> ModelResponse:  # noqa: D401
        raise RuntimeError("Simulated model service failure for testing.")


# --------------------------------------------------------------------------- #
# Tests                                                                       #
# --------------------------------------------------------------------------- #


def test_s01_returns_research_agent_output_for_complete_input() -> None:
    """S-01: returns a ResearchAgentOutput for a complete lead/context."""

    output = _run_default()
    assert isinstance(output, ResearchAgentOutput)
    assert output.lead_id == "lead_test_001"


def test_s02_result_success_is_true() -> None:
    """S-02: result.success is True."""

    output = _run_default()
    assert output.result.success is True
    assert output.result.error is None


def test_s03_metadata_agent_name_is_research_agent() -> None:
    """S-03: result.metadata.agent_name == "research_agent"."""

    output = _run_default()
    assert output.result.metadata.agent_name == "research_agent"


def test_s04_metadata_run_mode_is_simulation() -> None:
    """S-04: result.metadata.run_mode == RunMode.SIMULATION ("simulation")."""

    output = _run_default()
    assert output.result.metadata.run_mode == RunMode.SIMULATION
    assert output.result.metadata.run_mode.value == "simulation"


def test_s05_metadata_simulated_is_true() -> None:
    """S-05: result.metadata.simulated is True."""

    output = _run_default()
    assert output.result.metadata.simulated is True


def test_s06_metadata_model_name_is_mock_research_agent() -> None:
    """S-06: result.metadata.model == "mock-research-agent"."""

    output = _run_default()
    assert output.result.metadata.model == "mock-research-agent"


def test_s07_metadata_tokens_nonnegative_and_cost_dollar_prefixed() -> None:
    """S-07: result.metadata.tokens >= 0 and cost starts with "$"."""

    output = _run_default()
    assert output.result.metadata.tokens >= 0
    assert output.result.metadata.cost.startswith("$")


def test_s08_output_uses_available_context_summary() -> None:
    """S-08: company_summary is taken from available_context
    company_summary or recommended_research_summary."""

    output = _run_default()
    context = _rich_context()
    # Implementation prefers company_summary when both are present.
    assert output.company_summary == context["company_summary"]

    # When only recommended_research_summary is present, that's used.
    sparse_context = {
        "recommended_research_summary": "Only the recommended summary is present.",
        "evidence_cards": [
            {"title": "x", "description": "y", "confidence": "high"}
        ],
    }
    output_sparse = _run_default(context=sparse_context)
    assert output_sparse.company_summary == sparse_context["recommended_research_summary"]


def test_s09_evidence_cards_use_demo_context_source() -> None:
    """S-09: every emitted EvidenceCard uses EvidenceSource.DEMO_CONTEXT."""

    output = _run_default()
    assert output.evidence_cards, "expected at least one evidence card"
    for card in output.evidence_cards:
        assert card.source_type == EvidenceSource.DEMO_CONTEXT


def test_s10_missing_context_produces_low_confidence_and_risks() -> None:
    """S-10: missing / empty available_context produces Confidence.LOW
    and a non-empty information_risks list."""

    service = ResearchAgentService()
    output_none = service.run(
        ResearchAgentInput(lead=_lead(), available_context=None)
    )
    assert output_none.confidence == Confidence.LOW
    assert len(output_none.information_risks) >= 1
    assert output_none.evidence_cards == []
    assert output_none.opportunity_signals == []
    assert output_none.pain_hypotheses == []

    output_empty = service.run(
        ResearchAgentInput(lead=_lead(), available_context={})
    )
    assert output_empty.confidence == Confidence.LOW
    assert len(output_empty.information_risks) >= 1


def test_s11_output_does_not_claim_live_web_research() -> None:
    """S-11: output text never claims live web research or public LLM use."""

    output = _run_default()
    forbidden = [
        "live web research",
        "scraped",
        "fetched from the web",
        "according to my training",
        "I am an AI",
    ]
    blob = " ".join(
        [
            output.company_summary,
            " ".join(output.opportunity_signals),
            " ".join(output.pain_hypotheses),
            " ".join(output.information_risks),
            " ".join(card.headline + " " + card.description for card in output.evidence_cards),
        ]
    ).lower()
    for phrase in forbidden:
        assert phrase not in blob, f"output contains forbidden phrase: {phrase!r}"


def test_s12_mock_marker_not_copied_into_company_summary() -> None:
    """S-12: the MockModelService marker must not be copied into
    company_summary (the model response is NOT used as evidence)."""

    output = _run_default()
    assert "[MOCK MODEL RESPONSE" not in output.company_summary
    # And not into any other text-bearing field either.
    for signal in output.opportunity_signals:
        assert "[MOCK MODEL RESPONSE" not in signal
    for pain in output.pain_hypotheses:
        assert "[MOCK MODEL RESPONSE" not in pain
    for card in output.evidence_cards:
        assert "[MOCK MODEL RESPONSE" not in card.headline
        assert "[MOCK MODEL RESPONSE" not in card.description


def test_s13_unexpected_model_failure_returns_safe_failure_output() -> None:
    """S-13: when the model service raises, the agent returns
    success=False with safe fallback fields and never propagates."""

    service = ResearchAgentService(model_service=_FaultyModelService())
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert output.result.success is False
    assert output.result.error is not None
    assert output.result.error.code == "research_agent_error"
    assert "Simulated model service failure for testing." in output.result.error.message
    assert output.company_summary == "Research agent failed safely."
    assert output.opportunity_signals == []
    assert output.pain_hypotheses == []
    assert output.evidence_cards == []
    assert output.information_risks == [
        "Research agent failed before producing evidence."
    ]
    assert output.confidence == Confidence.LOW
    # Even the failure path must keep simulation honesty.
    assert output.result.metadata.simulated is True


def test_s14_no_real_provider_is_required() -> None:
    """S-14: the agent runs without any real provider.

    The default model service factory returns the mock provider in
    Phase 5.4. We assert that explicitly here: the service the agent
    constructs by default is a MockModelService instance.
    """

    service = ResearchAgentService()
    assert isinstance(service.model_service, MockModelService)
    # And we can run end-to-end without any custom config / API key.
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert output.result.success is True


def test_extra_full_context_yields_high_confidence() -> None:
    """Auxiliary: a rich context (3+ combined signals/evidence) ⇒ HIGH."""

    output = _run_default()
    assert output.confidence == Confidence.HIGH


def test_extra_model_config_default_is_used_when_constructed_manually() -> None:
    """Auxiliary: smoke check that a hand-rolled ModelResponse + minimal
    ModelConfig also satisfies the schema constraints we exercise."""

    cfg = ModelConfig(
        provider=ModelProvider.MOCK,
        model_name="mock-research-agent",
    )
    usage = ModelUsage(input_tokens=1, output_tokens=1, total_tokens=2)
    cost = ModelCostEstimate(
        input_cost=0.0, output_cost=0.0, total_cost=0.0, display_cost="$0.0000"
    )
    ModelResponse(
        provider=cfg.provider,
        model_name=cfg.model_name,
        content="anything",
        usage=usage,
        cost=cost,
    )


# --------------------------------------------------------------------------- #
# Phase 5.5C — structured-synthesis path tests                                #
# --------------------------------------------------------------------------- #
import json as _json  # noqa: E402  (test-local import keeps section self-contained)


_VALID_SYNTHESIS_JSON: str = _json.dumps(
    {
        "company_summary": "Synthesised summary from the Groq path.",
        "opportunity_signals": ["sig-a", "sig-b"],
        "pain_hypotheses": ["pain-x"],
        "evidence_cards": [
            {
                "headline": "Synthesised headline",
                "description": "Synthesised description.",
                "confidence": "high",
            }
        ],
        "information_risks": ["risk-z"],
        "confidence": "high",
    }
)


class _FakeGroqLikeModelService(BaseModelService):
    """Test double that mimics the surface of a real (non-simulated)
    provider response. Returns a configurable content string."""

    def __init__(self, content: str) -> None:
        self.content = content

    def complete(self, request):  # type: ignore[override]
        from app.schemas.model import (
            ModelCostEstimate,
            ModelProvider,
            ModelResponse,
            ModelUsage,
        )

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


def test_c01_default_service_behaviour_unchanged() -> None:
    """C-01: Default ResearchAgentService behaviour remains unchanged."""

    service = ResearchAgentService()
    assert isinstance(service.model_service, MockModelService)
    assert service.use_model_synthesis is False
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert output.result.success is True
    assert output.result.metadata.prompt_version == "research_agent_mock_v1"
    assert output.result.metadata.simulated is True


def test_c02_flag_false_with_groq_like_does_not_consume_model_content() -> None:
    """C-02: With use_model_synthesis=False the model content is never
    consumed, even when a non-simulated model service is injected."""

    fake = _FakeGroqLikeModelService(content=_VALID_SYNTHESIS_JSON)
    service = ResearchAgentService(model_service=fake, use_model_synthesis=False)
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    # Deterministic path used: company_summary is taken from context,
    # not from the synthesised JSON.
    context_summary = _rich_context()["company_summary"]
    assert output.company_summary == context_summary
    assert output.result.metadata.prompt_version == "research_agent_mock_v1"


def test_c03_flag_true_with_mock_service_does_not_consume_mock_marker() -> None:
    """C-03: With use_model_synthesis=True but a simulated (mock) service,
    mock content is NOT consumed; the deterministic path runs."""

    service = ResearchAgentService(
        model_service=MockModelService(), use_model_synthesis=True
    )
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert "[MOCK MODEL RESPONSE" not in output.company_summary
    assert output.company_summary == _rich_context()["company_summary"]
    assert output.result.metadata.simulated is True


def test_c04_flag_true_with_groq_like_consumes_valid_json() -> None:
    """C-04: With use_model_synthesis=True and a non-simulated service
    returning valid JSON, the response is consumed as evidence."""

    fake = _FakeGroqLikeModelService(content=_VALID_SYNTHESIS_JSON)
    service = ResearchAgentService(model_service=fake, use_model_synthesis=True)
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert output.company_summary == "Synthesised summary from the Groq path."
    assert output.opportunity_signals == ["sig-a", "sig-b"]
    assert output.pain_hypotheses == ["pain-x"]
    assert output.confidence == Confidence.HIGH


def test_c05_valid_json_metadata_is_groq_json_v1_and_not_simulated() -> None:
    """C-05: Valid JSON output → metadata prompt_version is
    ``research_agent_groq_json_v1`` and ``simulated`` is False."""

    fake = _FakeGroqLikeModelService(content=_VALID_SYNTHESIS_JSON)
    service = ResearchAgentService(model_service=fake, use_model_synthesis=True)
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert output.result.metadata.prompt_version == "research_agent_groq_json_v1"
    assert output.result.metadata.simulated is False  # FIX 1
    assert output.result.metadata.model == "llama-3.1-8b-instant"
    assert output.result.metadata.cost.startswith("$")


def test_c06_evidence_cards_use_demo_context_source() -> None:
    """C-06: EvidenceCards emitted from the Groq path use
    ``EvidenceSource.DEMO_CONTEXT``."""

    fake = _FakeGroqLikeModelService(content=_VALID_SYNTHESIS_JSON)
    service = ResearchAgentService(model_service=fake, use_model_synthesis=True)
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert output.evidence_cards
    for card in output.evidence_cards:
        assert card.source_type == EvidenceSource.DEMO_CONTEXT


def test_c07_evidence_descriptions_include_demo_context_provenance() -> None:
    """C-07: Evidence card descriptions include the explicit provenance
    note ``"provided demo context only"``."""

    fake = _FakeGroqLikeModelService(content=_VALID_SYNTHESIS_JSON)
    service = ResearchAgentService(model_service=fake, use_model_synthesis=True)
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    for card in output.evidence_cards:
        assert "provided demo context only" in card.description.lower()


def test_c08_invalid_json_triggers_deterministic_fallback_with_risk_note() -> None:
    """C-08: Invalid JSON from a non-simulated service triggers the
    deterministic fallback with a clear risk note and a ``_fallback``
    prompt_version. ``simulated`` is True in the fallback because the
    OUTPUT origin is deterministic (FIX 1), even though Groq was
    actually called."""

    fake = _FakeGroqLikeModelService(content="garbage with no json at all")
    service = ResearchAgentService(model_service=fake, use_model_synthesis=True)
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert output.result.success is True
    assert (
        output.result.metadata.prompt_version
        == "research_agent_groq_json_v1_fallback"
    )
    assert output.result.metadata.simulated is True  # FIX 1
    # The deterministic fallback's company_summary should be the
    # context summary, not garbage from the model.
    assert output.company_summary == _rich_context()["company_summary"]
    assert any(
        "fallback" in risk.lower() for risk in output.information_risks
    ), "expected a fallback risk note in information_risks"


def test_c09_unexpected_model_failure_returns_safe_success_false() -> None:
    """C-09: Unexpected failure on the synthesis path still returns
    success=False with a safe fallback output (existing behaviour
    preserved)."""

    service = ResearchAgentService(
        model_service=_FaultyModelService(), use_model_synthesis=True
    )
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert output.result.success is False
    assert output.result.error is not None
    assert output.result.error.code == "research_agent_error"
    assert output.company_summary == "Research agent failed safely."
    assert output.confidence == Confidence.LOW


def test_c10_no_raw_model_response_leaked_in_error_details() -> None:
    """C-10: The fallback path must not leak the raw model response.

    For invalid JSON the fallback uses the deterministic summary and
    a generic risk note that does not embed the model output. For an
    unexpected failure the error.message comes from str(exc); we assert
    the verbatim model content is never embedded in either field.
    """

    secret_marker = "MODEL_RAW_DUMP_THAT_SHOULD_NEVER_LEAK"

    # Invalid-JSON path.
    fake = _FakeGroqLikeModelService(content=f"prefix {secret_marker} suffix")
    service = ResearchAgentService(model_service=fake, use_model_synthesis=True)
    output = service.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    blob = (
        " ".join(output.information_risks)
        + " "
        + output.company_summary
    )
    assert secret_marker not in blob

    # Unexpected-failure path.
    class _LeakingFailure(BaseModelService):
        def complete(self, request):  # noqa: D401
            raise RuntimeError("benign agent failure")

    service2 = ResearchAgentService(
        model_service=_LeakingFailure(), use_model_synthesis=True
    )
    output2 = service2.run(
        ResearchAgentInput(lead=_lead(), available_context=_rich_context())
    )
    assert output2.result.error is not None
    # The error.message is the controlled str(exc), not raw model bytes.
    assert secret_marker not in output2.result.error.message
