"""Contract tests for the Phase 5.2 agent schemas.

These tests verify that every agent input/output pair instantiates with
minimal valid data, that bounded integers reject out-of-range values,
that defaults on shared envelopes are correct, and that existing schemas
(``EvidenceCard``, ``QAScores``, ``TraceEntry``) compose cleanly inside
the new agent contracts. No agent runtime exists yet; these tests are
purely contract-shape assertions.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.agents import (
    AgentContractResult,
    AgentError,
    AgentExecutionMetadata,
    EmailDrafterAgentInput,
    EmailDrafterAgentOutput,
    IntakeAgentInput,
    IntakeAgentOutput,
    LeadPipelineContractOutput,
    QAEvaluatorAgentInput,
    QAEvaluatorAgentOutput,
    QualifierAgentInput,
    QualifierAgentOutput,
    ResearchAgentInput,
    ResearchAgentOutput,
    StrategistAgentInput,
    StrategistAgentOutput,
)
from app.schemas.common import (
    Confidence,
    EvidenceSource,
    HallucinationRisk,
    Priority,
    Recommendation,
    RunMode,
)
from app.schemas.lead import LeadIn
from app.schemas.qa import EvidenceCard, QAScores
from app.schemas.run import TraceEntry


# --------------------------------------------------------------------------- #
# Helpers — minimal fixture factories                                         #
# --------------------------------------------------------------------------- #


def _lead() -> LeadIn:
    return LeadIn(
        lead_id="lead_test_001",
        company_name="Test Co",
        industry="B2B SaaS",
        country="United States",
        employee_count=120,
        contact_name="Test Person",
        contact_role="VP Sales",
    )


def _metadata(agent_name: str) -> AgentExecutionMetadata:
    return AgentExecutionMetadata(
        agent_name=agent_name,
        run_mode=RunMode.SIMULATION,
    )


def _result(agent_name: str) -> AgentContractResult:
    return AgentContractResult(success=True, metadata=_metadata(agent_name))


def _evidence_card(idx: int = 1) -> EvidenceCard:
    return EvidenceCard(
        id=f"evidence_{idx:02d}",
        headline="Sample headline",
        source_type=EvidenceSource.DEMO_CONTEXT,
        description="Sample description.",
        confidence=Confidence.HIGH,
    )


def _qa_scores() -> QAScores:
    return QAScores(
        personalization=70,
        evidence_coverage=70,
        cta_quality=70,
        tone_match=70,
        hallucination_risk=HallucinationRisk.LOW,
        recommendation=Recommendation.REVIEW,
    )


# --------------------------------------------------------------------------- #
# 1) Minimal-valid-data instantiation for every input/output schema           #
# --------------------------------------------------------------------------- #


def test_01_all_input_output_schemas_instantiate_with_minimal_valid_data() -> None:
    """Every Phase 5.2 input/output schema must construct from minimal
    valid data without raising."""

    lead = _lead()

    intake_in = IntakeAgentInput(raw_lead=lead)
    intake_out = IntakeAgentOutput(
        result=_result("intake"),
        normalized_lead=lead,
        confidence=Confidence.HIGH,
    )
    research_in = ResearchAgentInput(lead=lead)
    research_out = ResearchAgentOutput(
        result=_result("research"),
        lead_id=lead.lead_id,
        company_summary="Sample summary",
        confidence=Confidence.MEDIUM,
    )
    qualifier_in = QualifierAgentInput(lead=lead)
    qualifier_out = QualifierAgentOutput(
        result=_result("qualifier"),
        lead_id=lead.lead_id,
        fit_score=75,
        priority=Priority.HIGH,
        confidence=Confidence.MEDIUM,
    )
    strategist_in = StrategistAgentInput(
        lead=lead,
        company_summary="Sample summary",
        fit_score=75,
        priority=Priority.HIGH,
    )
    strategist_out = StrategistAgentOutput(
        result=_result("strategist"),
        lead_id=lead.lead_id,
        pain_hypothesis="Sample pain",
        pain_confidence=Confidence.MEDIUM,
        sales_angle="Sample angle",
        core_message="Sample core message",
        likely_objection="Sample objection",
    )
    drafter_in = EmailDrafterAgentInput(
        lead=lead,
        company_summary="Sample summary",
        pain_hypothesis="Sample pain",
        sales_angle="Sample angle",
        core_message="Sample core message",
    )
    drafter_out = EmailDrafterAgentOutput(
        result=_result("email_drafter"),
        lead_id=lead.lead_id,
        email_subject="Subject",
        email_body="Body",
        confidence=Confidence.MEDIUM,
    )
    qa_in = QAEvaluatorAgentInput(
        lead=lead,
        email_subject="Subject",
        email_body="Body",
    )
    qa_out = QAEvaluatorAgentOutput(
        result=_result("qa_evaluator"),
        lead_id=lead.lead_id,
        qa_score=72,
        qa_scores=_qa_scores(),
        hallucination_risk=HallucinationRisk.LOW,
        recommendation=Recommendation.REVIEW,
    )

    assert intake_in.raw_lead.lead_id == lead.lead_id
    assert intake_out.normalized_lead.lead_id == lead.lead_id
    assert research_in.lead.lead_id == lead.lead_id
    assert research_out.lead_id == lead.lead_id
    assert qualifier_in.lead.lead_id == lead.lead_id
    assert qualifier_out.fit_score == 75
    assert strategist_in.fit_score == 75
    assert strategist_out.sales_angle == "Sample angle"
    assert drafter_in.core_message == "Sample core message"
    assert drafter_out.email_subject == "Subject"
    assert qa_in.email_body == "Body"
    assert qa_out.qa_score == 72


# --------------------------------------------------------------------------- #
# 2) Every output contains AgentContractResult                                #
# --------------------------------------------------------------------------- #


def test_02_every_output_contains_agent_contract_result() -> None:
    """Each of the six output models must surface an AgentContractResult
    on its ``result`` field."""

    lead = _lead()
    outputs = [
        IntakeAgentOutput(
            result=_result("intake"),
            normalized_lead=lead,
            confidence=Confidence.HIGH,
        ),
        ResearchAgentOutput(
            result=_result("research"),
            lead_id=lead.lead_id,
            company_summary="x",
            confidence=Confidence.MEDIUM,
        ),
        QualifierAgentOutput(
            result=_result("qualifier"),
            lead_id=lead.lead_id,
            fit_score=50,
            priority=Priority.MEDIUM,
            confidence=Confidence.MEDIUM,
        ),
        StrategistAgentOutput(
            result=_result("strategist"),
            lead_id=lead.lead_id,
            pain_hypothesis="x",
            pain_confidence=Confidence.MEDIUM,
            sales_angle="x",
            core_message="x",
            likely_objection="x",
        ),
        EmailDrafterAgentOutput(
            result=_result("email_drafter"),
            lead_id=lead.lead_id,
            email_subject="x",
            email_body="x",
            confidence=Confidence.MEDIUM,
        ),
        QAEvaluatorAgentOutput(
            result=_result("qa_evaluator"),
            lead_id=lead.lead_id,
            qa_score=50,
            qa_scores=_qa_scores(),
            hallucination_risk=HallucinationRisk.LOW,
            recommendation=Recommendation.REVIEW,
        ),
    ]

    for output in outputs:
        assert isinstance(output.result, AgentContractResult)
        assert isinstance(output.result.metadata, AgentExecutionMetadata)


# --------------------------------------------------------------------------- #
# 3) AgentExecutionMetadata defaults                                          #
# --------------------------------------------------------------------------- #


def test_03_agent_execution_metadata_defaults_are_correct() -> None:
    """Default metadata values must match the contract:
    model == "none", tokens == 0, cost == "$0.00", simulated is False."""

    meta = AgentExecutionMetadata(
        agent_name="intake",
        run_mode=RunMode.SIMULATION,
    )
    assert meta.model == "none"
    assert meta.prompt_version == "contract_v1"
    assert meta.latency == "0ms"
    assert meta.tokens == 0
    assert meta.cost == "$0.00"
    assert meta.simulated is False


# --------------------------------------------------------------------------- #
# 4) fit_score bounded 0..100                                                 #
# --------------------------------------------------------------------------- #


def test_04_fit_score_rejects_out_of_range_values() -> None:
    """QualifierAgentOutput.fit_score must reject values < 0 and > 100.
    StrategistAgentInput.fit_score is bounded the same way."""

    lead = _lead()
    base_out_kwargs = dict(
        result=_result("qualifier"),
        lead_id=lead.lead_id,
        priority=Priority.LOW,
        confidence=Confidence.LOW,
    )

    with pytest.raises(ValidationError):
        QualifierAgentOutput(fit_score=-1, **base_out_kwargs)
    with pytest.raises(ValidationError):
        QualifierAgentOutput(fit_score=101, **base_out_kwargs)

    # Boundary values must be accepted.
    QualifierAgentOutput(fit_score=0, **base_out_kwargs)
    QualifierAgentOutput(fit_score=100, **base_out_kwargs)

    base_in_kwargs = dict(
        lead=lead,
        company_summary="x",
        priority=Priority.LOW,
    )
    with pytest.raises(ValidationError):
        StrategistAgentInput(fit_score=-1, **base_in_kwargs)
    with pytest.raises(ValidationError):
        StrategistAgentInput(fit_score=101, **base_in_kwargs)


# --------------------------------------------------------------------------- #
# 5) qa_score bounded 0..100                                                  #
# --------------------------------------------------------------------------- #


def test_05_qa_score_rejects_out_of_range_values() -> None:
    """QAEvaluatorAgentOutput.qa_score must reject values < 0 and > 100."""

    lead = _lead()
    base_kwargs = dict(
        result=_result("qa_evaluator"),
        lead_id=lead.lead_id,
        qa_scores=_qa_scores(),
        hallucination_risk=HallucinationRisk.LOW,
        recommendation=Recommendation.REVIEW,
    )

    with pytest.raises(ValidationError):
        QAEvaluatorAgentOutput(qa_score=-1, **base_kwargs)
    with pytest.raises(ValidationError):
        QAEvaluatorAgentOutput(qa_score=101, **base_kwargs)

    # Boundary values must be accepted.
    QAEvaluatorAgentOutput(qa_score=0, **base_kwargs)
    QAEvaluatorAgentOutput(qa_score=100, **base_kwargs)


# --------------------------------------------------------------------------- #
# 6) Existing enums are accepted correctly                                    #
# --------------------------------------------------------------------------- #


def test_06_existing_enums_are_accepted_correctly() -> None:
    """All enum-typed fields on the new contracts must accept every
    expected member of the existing common.py enums."""

    lead = _lead()

    for priority in Priority:
        QualifierAgentOutput(
            result=_result("qualifier"),
            lead_id=lead.lead_id,
            fit_score=50,
            priority=priority,
            confidence=Confidence.MEDIUM,
        )

    for confidence in Confidence:
        IntakeAgentOutput(
            result=_result("intake"),
            normalized_lead=lead,
            confidence=confidence,
        )

    for risk in HallucinationRisk:
        for rec in Recommendation:
            QAEvaluatorAgentOutput(
                result=_result("qa_evaluator"),
                lead_id=lead.lead_id,
                qa_score=50,
                qa_scores=_qa_scores(),
                hallucination_risk=risk,
                recommendation=rec,
            )

    for mode in RunMode:
        AgentExecutionMetadata(agent_name="intake", run_mode=mode)


# --------------------------------------------------------------------------- #
# 7) EvidenceCard and QAScores can be reused inside agent outputs             #
# --------------------------------------------------------------------------- #


def test_07_evidence_card_and_qa_scores_compose_into_outputs() -> None:
    """Existing EvidenceCard and QAScores models must drop straight into
    the new agent outputs without redefinition."""

    lead = _lead()
    cards = [_evidence_card(1), _evidence_card(2)]

    research_out = ResearchAgentOutput(
        result=_result("research"),
        lead_id=lead.lead_id,
        company_summary="x",
        evidence_cards=cards,
        confidence=Confidence.HIGH,
    )
    qa_out = QAEvaluatorAgentOutput(
        result=_result("qa_evaluator"),
        lead_id=lead.lead_id,
        qa_score=80,
        qa_scores=_qa_scores(),
        hallucination_risk=HallucinationRisk.LOW,
        recommendation=Recommendation.REVIEW,
    )
    qa_in = QAEvaluatorAgentInput(
        lead=lead,
        email_subject="s",
        email_body="b",
        evidence_cards=cards,
    )

    assert len(research_out.evidence_cards) == 2
    assert all(isinstance(c, EvidenceCard) for c in research_out.evidence_cards)
    assert isinstance(qa_out.qa_scores, QAScores)
    assert qa_in.evidence_cards[0].source_type == EvidenceSource.DEMO_CONTEXT


# --------------------------------------------------------------------------- #
# 8) LeadPipelineContractOutput holds all six agent outputs                   #
# --------------------------------------------------------------------------- #


def test_08_pipeline_container_can_hold_all_six_agent_outputs() -> None:
    """LeadPipelineContractOutput must accept every agent's output in its
    matching slot, plus a TraceEntry list."""

    lead = _lead()
    container = LeadPipelineContractOutput(
        run_id="run_test_001",
        lead_id=lead.lead_id,
        intake=IntakeAgentOutput(
            result=_result("intake"),
            normalized_lead=lead,
            confidence=Confidence.HIGH,
        ),
        research=ResearchAgentOutput(
            result=_result("research"),
            lead_id=lead.lead_id,
            company_summary="x",
            confidence=Confidence.MEDIUM,
        ),
        qualification=QualifierAgentOutput(
            result=_result("qualifier"),
            lead_id=lead.lead_id,
            fit_score=80,
            priority=Priority.HIGH,
            confidence=Confidence.HIGH,
        ),
        strategy=StrategistAgentOutput(
            result=_result("strategist"),
            lead_id=lead.lead_id,
            pain_hypothesis="x",
            pain_confidence=Confidence.MEDIUM,
            sales_angle="x",
            core_message="x",
            likely_objection="x",
        ),
        email=EmailDrafterAgentOutput(
            result=_result("email_drafter"),
            lead_id=lead.lead_id,
            email_subject="s",
            email_body="b",
            confidence=Confidence.MEDIUM,
        ),
        qa=QAEvaluatorAgentOutput(
            result=_result("qa_evaluator"),
            lead_id=lead.lead_id,
            qa_score=75,
            qa_scores=_qa_scores(),
            hallucination_risk=HallucinationRisk.LOW,
            recommendation=Recommendation.REVIEW,
        ),
        trace=[
            TraceEntry(
                agent="intake",
                status="success",
                input_summary="x",
                output_summary="y",
                latency="0ms",
                tokens=0,
                prompt_version="contract_v1",
            )
        ],
    )

    assert container.intake is not None
    assert container.research is not None
    assert container.qualification is not None
    assert container.strategy is not None
    assert container.email is not None
    assert container.qa is not None
    assert len(container.trace) == 1

    # Every slot is Optional and defaults to None.
    empty = LeadPipelineContractOutput(run_id="x", lead_id="y")
    assert empty.intake is None
    assert empty.research is None
    assert empty.qualification is None
    assert empty.strategy is None
    assert empty.email is None
    assert empty.qa is None
    assert empty.trace == []


# --------------------------------------------------------------------------- #
# 9) No schema requires LLM/model-specific fields                             #
# --------------------------------------------------------------------------- #


def test_09_no_schema_requires_llm_or_model_specific_fields() -> None:
    """The contracts must be instantiable without any LLM provider, model
    name, prompt template, token usage figure, latency measurement, or
    cost figure being supplied by the caller. Every such field is either
    absent from the contract or carries a default."""

    lead = _lead()

    # The minimal-input forms below intentionally omit every provider /
    # model / cost / latency / token field. If the contracts started
    # requiring any of those, these constructions would raise.
    IntakeAgentInput(raw_lead=lead)
    ResearchAgentInput(lead=lead)
    QualifierAgentInput(lead=lead)
    StrategistAgentInput(
        lead=lead,
        company_summary="x",
        fit_score=0,
        priority=Priority.LOW,
    )
    EmailDrafterAgentInput(
        lead=lead,
        company_summary="x",
        pain_hypothesis="x",
        sales_angle="x",
        core_message="x",
    )
    QAEvaluatorAgentInput(lead=lead, email_subject="x", email_body="x")

    # The shared metadata envelope has provider-neutral defaults.
    meta = AgentExecutionMetadata(agent_name="x", run_mode=RunMode.SIMULATION)
    assert meta.model == "none"
    assert meta.cost == "$0.00"
    assert meta.tokens == 0


# --------------------------------------------------------------------------- #
# 10) AgentError envelope behaves as documented                               #
# --------------------------------------------------------------------------- #


def test_10_agent_error_envelope_defaults_and_acceptance() -> None:
    """AgentError must accept the minimal (code, message) shape with
    ``recoverable`` defaulting to True and ``details`` defaulting to
    None, and must compose into AgentContractResult."""

    minimal = AgentError(code="example", message="example message")
    assert minimal.recoverable is True
    assert minimal.details is None

    detailed = AgentError(
        code="missing_field",
        message="industry missing",
        recoverable=False,
        details={"field": "industry"},
    )
    assert detailed.recoverable is False
    assert detailed.details == {"field": "industry"}

    failing_result = AgentContractResult(
        success=False,
        metadata=_metadata("intake"),
        error=detailed,
    )
    assert failing_result.success is False
    assert failing_result.error is not None
    assert failing_result.error.code == "missing_field"
