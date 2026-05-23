"""Block 8.3 — unit tests for the live Groq single-lead pipeline service.

These tests exercise ``run_live_groq_pipeline_for_lead`` directly with
an injected ``groq_service_factory`` so no real network call is ever
made. The deterministic baseline path must keep working even when the
live path fails, and the response shape must remain valid in both
cases.

Normal test runs do NOT require ``GROQ_API_KEY``: the only test that
needs the key sets it via ``monkeypatch.setenv`` to a synthetic
placeholder, never to a real provider key.
"""

from __future__ import annotations

import pytest

from app.schemas.agents import (
    AgentContractResult,
    AgentExecutionMetadata,
    QualifierAgentOutput,
    ResearchAgentOutput,
)
from app.schemas.common import (
    Confidence,
    HallucinationRisk,
    Priority,
    RunMode,
)
from app.schemas.live_pipeline import (
    LivePipelineComparison,
    LivePipelineResponse,
)
from app.services import telemetry_service as telemetry_module
from app.services.live_pipeline_service import (
    LIVE_GROQ_MODEL,
    LivePipelineDisabledError,
    LivePipelineKeyMissingError,
    LivePipelineLeadNotFoundError,
    MAX_LIVE_TOKENS_PER_RUN,
    run_live_groq_pipeline_for_lead,
)


_DEMO_LEAD_ID = "lead_001"


# --------------------------------------------------------------------------- #
# Fake provider error classes / stub model services                           #
# --------------------------------------------------------------------------- #


class _FakeRateLimitError(Exception):
    """Mimics a Groq SDK rate-limit error (HTTP 429)."""

    def __init__(self, message: str = "rate limit exceeded") -> None:
        super().__init__(message)
        self.status_code = 429


class _AlwaysRaisesService:
    """Stub model service whose ``complete`` always raises a given error."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def complete(self, request):  # noqa: ANN001 — mirror BaseModelService
        raise self._exc


# --------------------------------------------------------------------------- #
# Common fixtures                                                             #
# --------------------------------------------------------------------------- #


@pytest.fixture
def live_mode_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable the live pipeline opt-in flag and a synthetic API key.

    The synthetic key is never sent to a real provider — every test
    that uses this fixture also injects a stub model service via
    ``groq_service_factory``.
    """

    monkeypatch.setenv("ENABLE_LIVE_MODEL_PIPELINE", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-only-not-a-real-key")


@pytest.fixture(autouse=True)
def _clear_telemetry() -> None:
    telemetry_module.clear_telemetry()
    yield
    telemetry_module.clear_telemetry()


# --------------------------------------------------------------------------- #
# Gating tests                                                                #
# --------------------------------------------------------------------------- #


def test_live_disabled_by_default_raises_disabled_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ENABLE_LIVE_MODEL_PIPELINE", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(LivePipelineDisabledError):
        run_live_groq_pipeline_for_lead(_DEMO_LEAD_ID)


def test_live_enabled_but_no_api_key_raises_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_LIVE_MODEL_PIPELINE", "true")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(LivePipelineKeyMissingError):
        run_live_groq_pipeline_for_lead(_DEMO_LEAD_ID)


def test_unknown_lead_raises_lead_not_found(
    live_mode_enabled: None,
) -> None:
    with pytest.raises(LivePipelineLeadNotFoundError):
        run_live_groq_pipeline_for_lead(
            "lead_does_not_exist",
            groq_service_factory=lambda: _AlwaysRaisesService(
                RuntimeError("should not be called")
            ),
        )


# --------------------------------------------------------------------------- #
# Failure-path tests                                                          #
# --------------------------------------------------------------------------- #


def test_research_failure_marks_live_failed_with_failed_agent(
    live_mode_enabled: None,
) -> None:
    """The very first stage failing must produce a structured failure."""

    response = run_live_groq_pipeline_for_lead(
        _DEMO_LEAD_ID,
        groq_service_factory=lambda: _AlwaysRaisesService(
            RuntimeError("boom — provider crashed")
        ),
    )

    assert isinstance(response, LivePipelineResponse)
    assert response.live_success is False
    assert response.run_mode == "live_failed"
    assert response.live_model_used == LIVE_GROQ_MODEL
    assert response.failed_agent == "research_agent"
    assert response.failure_stage == "research"
    assert response.error_code == "provider_error"
    assert response.fallback_used is True
    assert response.fallback_reason
    assert response.deterministic_baseline_available is True
    assert response.deterministic_result is not None
    assert response.live_result is None


def test_rate_limit_yields_error_code_rate_limited(
    live_mode_enabled: None,
) -> None:
    """HTTP 429 from the provider must surface as ``error_code='rate_limited'``."""

    response = run_live_groq_pipeline_for_lead(
        _DEMO_LEAD_ID,
        groq_service_factory=lambda: _AlwaysRaisesService(
            _FakeRateLimitError("rate limit exceeded")
        ),
    )

    assert response.live_success is False
    assert response.error_code == "rate_limited"
    assert response.failed_agent == "research_agent"
    assert response.failure_stage == "research"


def test_provider_init_failure_yields_provider_init_stage(
    live_mode_enabled: None,
) -> None:
    """Factory raising before any agent runs is reported as ``provider_init``."""

    def _factory() -> object:
        raise RuntimeError("client could not be built")

    response = run_live_groq_pipeline_for_lead(
        _DEMO_LEAD_ID,
        groq_service_factory=_factory,
    )

    assert response.live_success is False
    assert response.failure_stage == "provider_init"
    assert response.failed_agent == "(none)"
    assert response.deterministic_baseline_available is True


def test_failed_response_has_all_comparison_deltas_none(
    live_mode_enabled: None,
) -> None:
    """Block 8.3: when live run fails, every delta field must be None."""

    response = run_live_groq_pipeline_for_lead(
        _DEMO_LEAD_ID,
        groq_service_factory=lambda: _AlwaysRaisesService(RuntimeError("x")),
    )

    comparison = response.comparison
    assert isinstance(comparison, LivePipelineComparison)
    assert comparison.fit_score_delta is None
    assert comparison.priority_changed is None
    assert comparison.qa_score_delta is None
    assert comparison.email_subject_changed is None
    assert comparison.risk_level_changed is None
    assert comparison.live_summary is None
    assert "no comparison" in comparison.comparison_notes
    # Deterministic baseline still produces a usable summary string.
    assert comparison.deterministic_summary is not None


def test_failed_response_does_not_silently_claim_live_succeeded(
    live_mode_enabled: None,
) -> None:
    """Even with the deterministic baseline available, ``run_mode`` must
    not be 'live' when the live path failed."""

    response = run_live_groq_pipeline_for_lead(
        _DEMO_LEAD_ID,
        groq_service_factory=lambda: _AlwaysRaisesService(RuntimeError("x")),
    )

    assert response.run_mode != "live"
    assert response.run_mode == "live_failed"
    assert response.live_success is False


# --------------------------------------------------------------------------- #
# Telemetry safety tests                                                      #
# --------------------------------------------------------------------------- #


def test_telemetry_does_not_store_forbidden_content(
    live_mode_enabled: None,
) -> None:
    """Recorded telemetry must be summary-level only; no email body, no
    raw provider response, no full lead payload."""

    response = run_live_groq_pipeline_for_lead(
        _DEMO_LEAD_ID,
        groq_service_factory=lambda: _AlwaysRaisesService(RuntimeError("x")),
    )

    summaries = telemetry_module.recent_run_summaries(limit=50)
    detail = telemetry_module.get_run_detail(response.run_id)

    forbidden_attrs = {
        "email_body",
        "email_subject",
        "raw_response",
        "raw_provider_response",
        "prompt",
        "system_prompt",
        "lead_payload",
    }

    for summary in summaries:
        for attr in forbidden_attrs:
            assert not hasattr(summary, attr)

    if detail is not None:
        for entry in detail.entries:
            for attr in forbidden_attrs:
                assert not hasattr(entry, attr)


# --------------------------------------------------------------------------- #
# Sanity: comparison schema instantiates standalone                          #
# --------------------------------------------------------------------------- #


def test_live_pipeline_comparison_is_independently_constructible() -> None:
    comparison = LivePipelineComparison(
        fit_score_delta=None,
        priority_changed=None,
        qa_score_delta=None,
        email_subject_changed=None,
        risk_level_changed=None,
        live_summary=None,
        deterministic_summary="fit=70 priority=Medium qa=85 risk=Low",
        comparison_notes="live run failed — no comparison available",
    )
    assert comparison.fit_score_delta is None
    assert comparison.deterministic_summary is not None
    assert comparison.comparison_notes


# --------------------------------------------------------------------------- #
# Token budget                                                                #
# --------------------------------------------------------------------------- #


def test_max_live_tokens_per_run_constant_is_a_positive_integer() -> None:
    assert isinstance(MAX_LIVE_TOKENS_PER_RUN, int)
    assert MAX_LIVE_TOKENS_PER_RUN >= 1000


# --------------------------------------------------------------------------- #
# Helper: type sanity for fake outputs (kept here in case future tests use   #
# them to simulate downstream success).                                       #
# --------------------------------------------------------------------------- #


def _make_research_output(lead_id: str) -> ResearchAgentOutput:
    return ResearchAgentOutput(
        result=AgentContractResult(
            success=True,
            metadata=AgentExecutionMetadata(
                agent_name="research_agent",
                run_mode=RunMode.SIMULATION,
                model="stub",
                prompt_version="research_agent_groq_json_v1",
                latency="1ms",
                tokens=10,
                cost="$0.0000",
                simulated=False,
            ),
            error=None,
        ),
        lead_id=lead_id,
        company_summary="A short stub research summary.",
        opportunity_signals=["growth", "hiring"],
        pain_hypotheses=["fragmented prospecting"],
        evidence_cards=[],
        information_risks=[],
        confidence=Confidence.MEDIUM,
    )


def _make_qualifier_output(lead_id: str) -> QualifierAgentOutput:
    return QualifierAgentOutput(
        result=AgentContractResult(
            success=True,
            metadata=AgentExecutionMetadata(
                agent_name="qualifier_agent",
                run_mode=RunMode.SIMULATION,
                model="stub",
                prompt_version="qualifier_agent_groq_json_v1",
                latency="1ms",
                tokens=10,
                cost="$0.0000",
                simulated=False,
            ),
            error=None,
        ),
        lead_id=lead_id,
        fit_score=70,
        priority=Priority.MEDIUM,
        fit_reasons=["industry match"],
        fit_risks=[],
        confidence=Confidence.MEDIUM,
    )


def test_internal_helpers_construct_valid_outputs() -> None:
    """Cheap sanity check that the helper builders produce models that
    Pydantic accepts. Not exported; future Block 8.x success-path tests
    can extend on these helpers without re-deriving them."""

    research = _make_research_output(_DEMO_LEAD_ID)
    qualifier = _make_qualifier_output(_DEMO_LEAD_ID)

    assert research.lead_id == _DEMO_LEAD_ID
    assert qualifier.priority == Priority.MEDIUM
    assert HallucinationRisk.LOW.value == "Low"
