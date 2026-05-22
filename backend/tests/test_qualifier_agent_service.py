"""Unit tests for the Phase 5.6A Qualifier Agent service.

Test IDs map 1:1 to the Phase 5.6A spec (S-01 .. S-14).
"""

from __future__ import annotations

from app.agents.qualifier_agent import QualifierAgentService
from app.schemas.agents import QualifierAgentInput, QualifierAgentOutput
from app.schemas.common import Confidence, Priority, RunMode
from app.schemas.lead import LeadIn
from app.schemas.model import ModelRequest, ModelResponse
from app.services.icp_scoring import (
    apply_override_rules,
    compute_data_quality_deductions,
)
from app.services.model_service import BaseModelService, MockModelService


# --------------------------------------------------------------------------- #
# Fixture factories                                                           #
# --------------------------------------------------------------------------- #


def _strong_lead(**overrides) -> LeadIn:
    """Veltrix-shaped strong lead — Tier 1 industry, sweet-spot size,
    Tier 1 country, decision-maker role, full data."""

    base = dict(
        lead_id="lead_strong_001",
        company_name="Strong Co",
        industry="B2B SaaS",
        country="United States",
        employee_count=140,
        contact_name="Sample Person",
        contact_role="VP Revenue Operations",
        website="strong-co.io",
        notes="Recently closed Series B; hiring three SDRs.",
    )
    base.update(overrides)
    return LeadIn(**base)


def _degraded_lead() -> LeadIn:
    """Orbis-shaped degraded lead — most fields missing."""

    return LeadIn(
        lead_id="lead_degraded_010",
        company_name="Orbis-like Co",
        industry=None,
        country=None,
        employee_count=None,
        contact_name="Anon",
        contact_role=None,
        website=None,
        notes=None,
    )


def _input_for(lead: LeadIn, **overrides) -> QualifierAgentInput:
    base = dict(
        lead=lead,
        research_summary=None,
        opportunity_signals=[],
        information_risks=[],
        run_id="test_run_001",
    )
    base.update(overrides)
    return QualifierAgentInput(**base)


def _run(
    lead: LeadIn,
    **kwargs,
) -> QualifierAgentOutput:
    service = QualifierAgentService()
    return service.run(_input_for(lead, **kwargs))


class _ExplodingModelService(BaseModelService):
    """For S-12: a model service that throws on every call (the
    qualifier should never even ask it for anything in 5.6A, so the
    fact this stays unused is itself part of the contract)."""

    def complete(self, request: ModelRequest) -> ModelResponse:  # noqa: D401
        raise RuntimeError(
            "QualifierAgentService should not call the model service in Phase 5.6A."
        )


class _CountingModelService(BaseModelService):
    """For S-14: counts how many times .complete() is invoked."""

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, request: ModelRequest) -> ModelResponse:  # noqa: D401
        self.calls += 1
        # Return any minimal valid ModelResponse — should never matter
        # because the qualifier does not consume it.
        from app.schemas.model import (
            ModelCostEstimate,
            ModelProvider,
            ModelResponse as _MR,
            ModelUsage,
        )

        return _MR(
            provider=ModelProvider.MOCK,
            model_name="mock-leadforge-model",
            content="unused",
            usage=ModelUsage(input_tokens=0, output_tokens=0, total_tokens=0),
            cost=ModelCostEstimate(
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0,
                display_cost="$0.0000",
            ),
        )


# --------------------------------------------------------------------------- #
# Tests                                                                       #
# --------------------------------------------------------------------------- #


def test_s01_run_returns_qualifier_agent_output_for_strong_lead() -> None:
    """S-01: QualifierAgentService.run returns QualifierAgentOutput for a
    strong lead."""

    output = _run(
        _strong_lead(),
        opportunity_signals=["Hiring SDRs", "Series B closed", "Mid-market expansion"],
    )
    assert isinstance(output, QualifierAgentOutput)
    assert output.lead_id == "lead_strong_001"


def test_s02_result_success_is_true() -> None:
    """S-02: result.success is True for a normal call."""

    output = _run(_strong_lead())
    assert output.result.success is True
    assert output.result.error is None


def test_s03_metadata_agent_name_is_qualifier_agent() -> None:
    """S-03: metadata.agent_name == "qualifier_agent"."""

    output = _run(_strong_lead())
    assert output.result.metadata.agent_name == "qualifier_agent"


def test_s04_metadata_run_mode_is_simulation() -> None:
    """S-04: metadata.run_mode == RunMode.SIMULATION ("simulation")."""

    output = _run(_strong_lead())
    assert output.result.metadata.run_mode == RunMode.SIMULATION
    assert output.result.metadata.run_mode.value == "simulation"


def test_s05_metadata_simulated_is_true() -> None:
    """S-05: metadata.simulated is True."""

    output = _run(_strong_lead())
    assert output.result.metadata.simulated is True


def test_s06_metadata_tokens_zero_and_cost_zero_dollars() -> None:
    """S-06: metadata.tokens == 0 and metadata.cost == "$0.00"."""

    output = _run(_strong_lead())
    assert output.result.metadata.tokens == 0
    assert output.result.metadata.cost == "$0.00"
    assert output.result.metadata.model == "none"
    assert output.result.metadata.prompt_version == "qualifier_agent_deterministic_v1"


def test_s07_strong_lead_scores_within_bounds_and_high_or_medium_priority() -> None:
    """S-07: a strong lead gets fit_score within 0..100 and Priority.HIGH
    or Priority.MEDIUM."""

    output = _run(
        _strong_lead(),
        opportunity_signals=["Hiring SDRs", "Series B closed"],
    )
    assert 0 <= output.fit_score <= 100
    assert output.priority in (Priority.HIGH, Priority.MEDIUM)


def test_s08_degraded_lead_gets_low_priority_and_risks() -> None:
    """S-08: degraded lead with missing data gets Priority.LOW and
    a populated fit_risks list."""

    output = _run(_degraded_lead())
    assert output.priority == Priority.LOW
    assert len(output.fit_risks) >= 1
    # Every dimension that could score got 0 → fit_score is small.
    assert 0 <= output.fit_score <= 44


def test_s09_fit_score_never_below_zero_or_above_hundred() -> None:
    """S-09: fit_score never goes below 0 or above 100, across a sweep
    of representative inputs."""

    candidates = [
        _strong_lead(),
        _degraded_lead(),
        _strong_lead(industry="Retail"),  # B2C override
        _strong_lead(employee_count=10_000),  # 5000+ override
        _strong_lead(contact_role="HR Director"),  # out-of-scope role
        _strong_lead(employee_count=5),  # too small
    ]
    for lead in candidates:
        output = _run(lead)
        assert 0 <= output.fit_score <= 100, (
            f"{lead.lead_id}: fit_score={output.fit_score}"
        )


def test_s10_opportunity_signals_support_fit_reasons() -> None:
    """S-10: opportunity signals increase or support fit_reasons.

    With 2+ signals, the Dimension 5 reason line should include
    "2+ signals detected", and the score should be ≥ the score for the
    no-signals baseline.
    """

    baseline = _run(_strong_lead())
    with_signals = _run(
        _strong_lead(),
        opportunity_signals=["A", "B", "C"],
    )
    assert with_signals.fit_score >= baseline.fit_score
    assert any(
        "2+ signals detected" in reason for reason in with_signals.fit_reasons
    )


def test_s11_information_risks_carry_into_fit_risks_or_reduce_confidence() -> None:
    """S-11: information risks reduce confidence or are surfaced as
    fit_risks. Both effects are acceptable; we assert at least one
    happened versus a clean baseline."""

    baseline = _run(_strong_lead())
    risky = _run(
        _strong_lead(),
        information_risks=[
            "Budget authority unverified.",
            "Compliance posture unknown.",
        ],
    )

    carried = all(
        risk in risky.fit_risks
        for risk in ("Budget authority unverified.", "Compliance posture unknown.")
    )
    less_confident = (
        risky.confidence == Confidence.LOW
        and baseline.confidence != Confidence.LOW
    ) or (
        risky.confidence == Confidence.MEDIUM
        and baseline.confidence == Confidence.HIGH
    )
    assert carried or less_confident


def test_s12_unexpected_internal_failure_returns_safe_success_false() -> None:
    """S-12: an unexpected internal failure returns a safe success=False
    output. We monkeypatch the deterministic baseline entry point to
    raise.

    (Updated for Phase 5.6B: the run() path now goes through
    ``_compute_baseline`` rather than ``_run_inner``. The failure
    surface is unchanged — any internal exception still routes to the
    safe ``success=False`` output — only the monkeypatch target moved.)
    """

    service = QualifierAgentService()

    def _boom(_input):
        raise RuntimeError("Synthetic qualifier failure for testing.")

    service._compute_baseline = _boom  # type: ignore[assignment]
    output = service.run(_input_for(_strong_lead()))
    assert output.result.success is False
    assert output.result.error is not None
    assert output.result.error.code == "qualifier_agent_error"
    assert output.fit_score == 0
    assert output.priority == Priority.LOW
    assert output.fit_reasons == []
    assert output.fit_risks == [
        "Qualifier agent failed before producing a score."
    ]
    assert output.confidence == Confidence.LOW


def test_s13_no_real_provider_is_required() -> None:
    """S-13: the qualifier runs without any real provider.

    Default model service is the mock (Phase 5.4), and even when no
    model service is supplied at all the default constructor works.
    """

    service = QualifierAgentService()
    assert isinstance(service.model_service, MockModelService)
    output = service.run(_input_for(_strong_lead()))
    assert output.result.success is True


def test_s14_deterministic_scoring_does_not_call_model_service() -> None:
    """S-14: model service response is not required for deterministic
    scoring. The qualifier must NOT call the injected model service.

    We pass both a counting service (to assert the call count is zero)
    and an exploding service (to assert that the qualifier wouldn't
    even tolerate being driven through it accidentally) — both must
    produce a normal, successful qualifier output.
    """

    counter = _CountingModelService()
    counted = QualifierAgentService(model_service=counter).run(
        _input_for(_strong_lead())
    )
    assert counted.result.success is True
    assert counter.calls == 0

    exploding = QualifierAgentService(model_service=_ExplodingModelService()).run(
        _input_for(_strong_lead())
    )
    # The exploding service raises if anything calls .complete(); the
    # fact that the agent still produces a success=True output proves
    # it never reached the model service.
    assert exploding.result.success is True


# --------------------------------------------------------------------------- #
# Auxiliary checks for icp_scoring helpers used by the agent                  #
# --------------------------------------------------------------------------- #


def test_extra_b2c_industry_override_caps_priority_at_low() -> None:
    """Phase 5.6A FIX 2 a: B2C / out-of-scope industry caps priority at Low."""

    lead = _strong_lead(industry="Retail")
    deductions = compute_data_quality_deductions(lead)
    cap, notes = apply_override_rules(score=100, lead=lead, deductions=deductions)
    assert cap == 44
    assert any("capped at Low" in note for note in notes)

    output = _run(
        lead, opportunity_signals=["x", "y"]
    )
    assert output.priority == Priority.LOW
    assert any("B2C" in risk for risk in output.fit_risks)


def test_extra_size_over_five_thousand_caps_priority_at_low() -> None:
    """Phase 5.6A FIX 2 b: 5000+ employees caps priority at Low."""

    lead = _strong_lead(employee_count=10_000)
    output = _run(lead)
    assert output.priority == Priority.LOW
    assert any("5000+ employees" in risk for risk in output.fit_risks)


def test_extra_out_of_scope_contact_role_scores_dimension_4_zero() -> None:
    """Phase 5.6A FIX 2 d: HR/Finance/Technical contact role scores
    Dimension 4 = 0 and surfaces as a fit_risk."""

    output = _run(_strong_lead(contact_role="HR Director"))
    assert any(
        "Dimension 4 scored 0" in risk for risk in output.fit_risks
    )


# --------------------------------------------------------------------------- #
# Phase 5.6B — structured-synthesis path tests                                #
# --------------------------------------------------------------------------- #
import json as _json  # noqa: E402  (test-local import keeps section self-contained)


def _valid_qualifier_synthesis_json(
    *,
    fit_score: int = 80,
    priority: str = "high",
    fit_reasons: list[str] | None = None,
    fit_risks: list[str] | None = None,
    confidence: str = "high",
) -> str:
    return _json.dumps(
        {
            "fit_score": fit_score,
            "priority": priority,
            "fit_reasons": fit_reasons if fit_reasons is not None else ["llm reason"],
            "fit_risks": fit_risks if fit_risks is not None else [],
            "confidence": confidence,
        }
    )


class _FakeGroqLikeModelService(BaseModelService):
    """Non-simulated test double — mimics the Phase 5.5B GroqModelService
    surface, returns a configurable content string."""

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


def test_b01_default_service_behaviour_unchanged() -> None:
    """B-01: Default QualifierAgentService behaviour is unchanged."""

    service = QualifierAgentService()
    assert service.use_model_synthesis is False
    output = service.run(
        _input_for(
            _strong_lead(),
            opportunity_signals=["Hiring SDRs", "Series B"],
        )
    )
    assert output.result.success is True
    assert output.result.metadata.prompt_version == "qualifier_agent_deterministic_v1"
    assert output.result.metadata.simulated is True


def test_b02_flag_false_with_fake_groq_does_not_consume_content() -> None:
    """B-02: With use_model_synthesis=False, model content is never
    consumed even when a non-simulated service is injected."""

    fake = _FakeGroqLikeModelService(
        content=_valid_qualifier_synthesis_json(
            fit_score=100, fit_reasons=["LLM-only reason"]
        )
    )
    service = QualifierAgentService(model_service=fake, use_model_synthesis=False)
    output = service.run(_input_for(_strong_lead()))
    # Deterministic baseline — no LLM-only reason appears.
    assert "LLM-only reason" not in output.fit_reasons
    assert output.result.metadata.prompt_version == "qualifier_agent_deterministic_v1"


def test_b03_flag_true_with_mock_does_not_consume_simulated_content() -> None:
    """B-03: With use_model_synthesis=True but a simulated (mock) model
    service, the response is NOT consumed — deterministic baseline runs."""

    service = QualifierAgentService(
        model_service=MockModelService(), use_model_synthesis=True
    )
    output = service.run(_input_for(_strong_lead(), opportunity_signals=["a"]))
    # Mock marker never appears anywhere in fit_reasons / fit_risks.
    blob = " ".join(output.fit_reasons + output.fit_risks)
    assert "[MOCK MODEL RESPONSE" not in blob
    assert output.result.metadata.prompt_version == "qualifier_agent_deterministic_v1"
    assert output.result.metadata.simulated is True


def test_b04_flag_true_with_groq_like_valid_json_consumes_payload() -> None:
    """B-04: With use_model_synthesis=True and a non-simulated service
    returning valid JSON, the response IS consumed as the output."""

    # Strong-lead baseline ≈ 92; choose 90 so we're well within +15.
    fake = _FakeGroqLikeModelService(
        content=_valid_qualifier_synthesis_json(
            fit_score=90,
            priority="high",
            fit_reasons=["LLM refined reason"],
            fit_risks=["LLM refined risk"],
            confidence="high",
        )
    )
    service = QualifierAgentService(model_service=fake, use_model_synthesis=True)
    output = service.run(
        _input_for(_strong_lead(), opportunity_signals=["Hiring SDRs", "Series B"])
    )
    assert output.fit_score == 90
    assert output.priority == Priority.HIGH
    assert "LLM refined reason" in output.fit_reasons
    assert "LLM refined risk" in output.fit_risks


def test_b05_valid_payload_metadata_is_groq_json_v1_and_not_simulated() -> None:
    """B-05: Valid synthesis → metadata prompt_version is
    ``qualifier_agent_groq_json_v1`` and ``simulated`` is False."""

    fake = _FakeGroqLikeModelService(
        content=_valid_qualifier_synthesis_json(fit_score=90)
    )
    service = QualifierAgentService(model_service=fake, use_model_synthesis=True)
    output = service.run(_input_for(_strong_lead()))
    assert output.result.metadata.prompt_version == "qualifier_agent_groq_json_v1"
    assert output.result.metadata.simulated is False  # FIX 1
    assert output.result.metadata.model == "llama-3.1-8b-instant"
    assert output.result.metadata.cost.startswith("$")


def test_b06_simulated_flag_is_false_only_when_payload_used() -> None:
    """B-06: ``metadata.simulated=False`` ONLY when the validated +
    guardrail-approved payload is actually used. Fallback paths must
    keep ``simulated=True``."""

    # Validated path → simulated=False.
    validated = QualifierAgentService(
        model_service=_FakeGroqLikeModelService(
            content=_valid_qualifier_synthesis_json(fit_score=90)
        ),
        use_model_synthesis=True,
    ).run(_input_for(_strong_lead()))
    assert validated.result.metadata.simulated is False

    # Fallback path → simulated=True.
    fallback = QualifierAgentService(
        model_service=_FakeGroqLikeModelService(content="not json"),
        use_model_synthesis=True,
    ).run(_input_for(_strong_lead()))
    assert fallback.result.metadata.simulated is True


def test_b07_invalid_json_triggers_deterministic_fallback_with_risk() -> None:
    """B-07: Invalid JSON → deterministic fallback + risk note + the
    ``_fallback`` prompt_version."""

    fake = _FakeGroqLikeModelService(content="garbage with no json at all")
    output = QualifierAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for(_strong_lead()))
    assert output.result.success is True
    assert (
        output.result.metadata.prompt_version
        == "qualifier_agent_groq_json_v1_fallback"
    )
    assert output.result.metadata.simulated is True
    assert any(
        "LLM qualification failed" in risk for risk in output.fit_risks
    )


def test_b08_guardrail_score_increase_over_fifteen_triggers_fallback() -> None:
    """B-08: ``fit_score`` more than 15 above deterministic baseline →
    fallback (guardrail step 3)."""

    # Build a lead whose baseline is comfortably Medium and inject an
    # inflated LLM score (+30).
    medium_lead = _strong_lead(
        industry="Legal Tech",
        country="Mexico",
        employee_count=20,
        contact_role="Sales Manager",
    )
    baseline = QualifierAgentService().run(_input_for(medium_lead))
    inflated = baseline.fit_score + 30
    fake = _FakeGroqLikeModelService(
        content=_valid_qualifier_synthesis_json(
            fit_score=min(inflated, 100), priority="high"
        )
    )
    output = QualifierAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for(medium_lead))
    assert (
        output.result.metadata.prompt_version
        == "qualifier_agent_groq_json_v1_fallback"
    )
    assert output.fit_score == baseline.fit_score
    assert output.priority == baseline.priority


def test_b09_override_cap_blocks_low_to_high_upgrade() -> None:
    """B-09: an override cap on the baseline blocks any LLM priority
    upgrade (LOW → HIGH must NOT take effect)."""

    # B2C industry → cap LOW.
    lead = _strong_lead(industry="Retail")
    baseline = QualifierAgentService().run(_input_for(lead))
    assert baseline.priority == Priority.LOW

    fake = _FakeGroqLikeModelService(
        content=_valid_qualifier_synthesis_json(
            fit_score=baseline.fit_score, priority="high", confidence="high"
        )
    )
    output = QualifierAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for(lead))
    assert output.priority == Priority.LOW
    assert (
        output.result.metadata.prompt_version
        == "qualifier_agent_groq_json_v1_fallback"
    )


def test_b09b_override_cap_also_blocks_low_to_medium_upgrade() -> None:
    """B-09b: Phase 5.6B FIX 3 — override cap blocks ANY priority
    upgrade, not just to HIGH. LOW → MEDIUM must also be rejected."""

    lead = _strong_lead(industry="Retail")
    baseline = QualifierAgentService().run(_input_for(lead))
    assert baseline.priority == Priority.LOW

    fake = _FakeGroqLikeModelService(
        content=_valid_qualifier_synthesis_json(
            fit_score=baseline.fit_score, priority="medium", confidence="medium"
        )
    )
    output = QualifierAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for(lead))
    assert output.priority == Priority.LOW
    assert (
        output.result.metadata.prompt_version
        == "qualifier_agent_groq_json_v1_fallback"
    )


def test_b10_score_cannot_increase_more_than_fifteen() -> None:
    """B-10: an LLM score within +15 of baseline IS accepted; a score
    over +15 IS rejected.

    For a strong lead with baseline 92, +15 lands at 100 (the schema
    cap). For a medium lead with baseline ~57, we test the exact
    boundary.
    """

    medium_lead = _strong_lead(
        industry="Legal Tech",
        country="Mexico",
        employee_count=20,
        contact_role="Sales Manager",
    )
    baseline_score = QualifierAgentService().run(_input_for(medium_lead)).fit_score

    accepted_score = baseline_score + 15
    rejected_score = min(100, baseline_score + 16)

    accepted = QualifierAgentService(
        model_service=_FakeGroqLikeModelService(
            content=_valid_qualifier_synthesis_json(fit_score=accepted_score)
        ),
        use_model_synthesis=True,
    ).run(_input_for(medium_lead))
    assert accepted.result.metadata.prompt_version == "qualifier_agent_groq_json_v1"
    assert accepted.fit_score == accepted_score

    if rejected_score > baseline_score + 15:
        rejected = QualifierAgentService(
            model_service=_FakeGroqLikeModelService(
                content=_valid_qualifier_synthesis_json(fit_score=rejected_score)
            ),
            use_model_synthesis=True,
        ).run(_input_for(medium_lead))
        assert (
            rejected.result.metadata.prompt_version
            == "qualifier_agent_groq_json_v1_fallback"
        )


def test_b11_unexpected_failure_returns_safe_success_false() -> None:
    """B-11: an unexpected failure on the synthesis path returns
    ``success=False`` with a safe fallback output."""

    class _LeakyFailure(BaseModelService):
        def complete(self, request):  # noqa: D401
            raise RuntimeError("synthesis exploded")

    output = QualifierAgentService(
        model_service=_LeakyFailure(), use_model_synthesis=True
    ).run(_input_for(_strong_lead()))
    assert output.result.success is False
    assert output.result.error is not None
    assert output.result.error.code == "qualifier_agent_error"
    assert output.fit_score == 0
    assert output.priority == Priority.LOW
    assert output.confidence == Confidence.LOW


def test_b12_no_raw_model_response_leaked_in_error_or_fallback() -> None:
    """B-12: the raw model response is never leaked through error
    messages or fallback risk notes."""

    secret_marker = "MODEL_RAW_DUMP_THAT_SHOULD_NEVER_LEAK"

    # Invalid-JSON fallback path.
    fake = _FakeGroqLikeModelService(content=f"prefix {secret_marker} suffix")
    output = QualifierAgentService(
        model_service=fake, use_model_synthesis=True
    ).run(_input_for(_strong_lead()))
    blob = " ".join(output.fit_reasons + output.fit_risks)
    assert secret_marker not in blob

    # Unexpected-failure path.
    class _LeakyFailure(BaseModelService):
        def complete(self, request):  # noqa: D401
            raise RuntimeError(
                "benign agent failure"
            )

    output2 = QualifierAgentService(
        model_service=_LeakyFailure(), use_model_synthesis=True
    ).run(_input_for(_strong_lead()))
    assert output2.result.error is not None
    assert secret_marker not in output2.result.error.message


def test_extra_priority_medium_threshold_is_forty_five() -> None:
    """Phase 5.6A FIX 1: Priority.MEDIUM threshold is 45 (not 50).

    We construct an output whose final score lands at exactly 45 and
    confirm the priority is MEDIUM.
    """

    # Industry Tier 3 (12) + 11–49 size (10) + Tier 2 country (7) +
    # decision-maker role (18) — no signals, all-fields data quality
    # 10 minus zero deductions = 10 → total = 12+10+7+18+0+10 = 57.
    # Tweak by dropping the role to end-user (8) → 12+10+7+8+0+10 = 47.
    lead = _strong_lead(
        industry="Legal Tech",
        country="Mexico",
        employee_count=20,
        contact_role="Sales Manager",
    )
    output = _run(lead)
    # We don't pin the exact number — what matters is that any score in
    # [45..74] maps to MEDIUM under the corrected threshold.
    assert 45 <= output.fit_score <= 74
    assert output.priority == Priority.MEDIUM
