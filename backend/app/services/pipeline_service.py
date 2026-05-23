"""Phase 6.1 — Plain Python Pipeline Orchestration (single lead).

A deterministic, in-process bridge that runs the five existing agent
services exactly once and in fixed order for a single demo lead:

    Research → Qualifier → Strategist → Email Drafter → QA Evaluator

Design rules (Phase 6.1):

* Minimal orchestration only. No LangGraph, no async, no background
  jobs, no DB writes, no email delivery, no live web research, no
  scraping, no Chroma/RAG, no Groq calls. Each agent is invoked via
  the already-existing :class:`MockModelService`-backed service
  classes from ``app.agents`` (the same classes the per-agent demo
  endpoints already use), so this module introduces no new model
  provider work.

* Outputs are passed forward explicitly between agents using the
  Phase 5.2 contract field names from :mod:`app.schemas.agents`. We
  intentionally do **not** route through
  :mod:`app.services.agent_demo_service`'s ``build_demo_*`` helpers
  because those re-run earlier agents internally (e.g. the Strategist
  demo path re-runs Research and Qualifier), which would execute the
  Research Agent up to three times for one lead.

* The pipeline is deterministic and read-only: ``run_pipeline_for_lead``
  is a pure function of the static demo dataset and the agents'
  deterministic baselines. Calling it repeatedly for the same
  ``lead_id`` produces the same output (modulo any deterministic
  metadata such as latency strings emitted by the mock model service).

Hard non-goals (kept structurally impossible in this module):

* No call to Groq or any real model provider.
* No call into any ``build_demo_*_groq_output`` function.
* No background task scheduling.
* No SMTP / email sending. The QA Evaluator only evaluates a draft.
* No new HTTP routes for the all-leads case.
"""

from __future__ import annotations

from uuid import uuid4

from app.agents.email_drafter_agent import EmailDrafterAgentService
from app.agents.qa_evaluator_agent import QAEvaluatorAgentService
from app.agents.qualifier_agent import QualifierAgentService
from app.agents.research_agent import ResearchAgentService
from app.agents.strategist_agent import StrategistAgentService
from app.schemas.agents import (
    AgentContractResult,
    EmailDrafterAgentInput,
    EmailDrafterAgentOutput,
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
from app.schemas.common import AgentRunStatus
from app.schemas.demo import DemoCompanyResearch
from app.schemas.lead import LeadIn
from app.schemas.run import TraceEntry
from app.services.demo_data_loader import (
    load_demo_company_research,
    load_demo_leads,
)

_PIPELINE_PROMPT_VERSION_FALLBACK: str = "pipeline_v1"


def _trace_status(result: AgentContractResult) -> AgentRunStatus:
    return AgentRunStatus.SUCCESS if result.success else AgentRunStatus.FAILED


def _trace_entry(
    agent_label: str,
    result: AgentContractResult,
    input_summary: str,
    output_summary: str,
) -> TraceEntry:
    """Build a ``TraceEntry`` from an agent's contract result.

    Phase 6.1: ``simulated=False`` is set explicitly on every pipeline
    trace entry, per the Phase 6.1 prompt. The agents themselves are
    still backed by ``MockModelService`` (so their per-agent
    ``AgentExecutionMetadata.simulated`` remains ``True``); the
    ``simulated`` flag on the *trace* records the orchestration mode,
    not the underlying model service. Phase 6.x will flip the model
    service backing without changing this module's surface.
    """

    metadata = result.metadata
    return TraceEntry(
        agent=agent_label,
        status=_trace_status(result),
        input_summary=input_summary,
        output_summary=output_summary,
        latency=metadata.latency,
        tokens=metadata.tokens,
        prompt_version=metadata.prompt_version or _PIPELINE_PROMPT_VERSION_FALLBACK,
        model=metadata.model,
        simulated=False,
    )


def _find_lead(lead_id: str) -> LeadIn:
    leads = load_demo_leads()
    for lead in leads:
        if lead.lead_id == lead_id:
            return lead
    raise ValueError(f"Lead '{lead_id}' not found in the demo dataset.")


def _find_research_record(lead_id: str) -> DemoCompanyResearch | None:
    research_records = load_demo_company_research()
    for record in research_records:
        if record.lead_id == lead_id:
            return record
    return None


def _available_context(
    research: DemoCompanyResearch | None,
) -> dict | None:
    if research is None:
        return None
    return research.model_dump()


def _qualifier_seed_signals(
    research_output: ResearchAgentOutput,
    research_record: DemoCompanyResearch | None,
) -> tuple[list[str], list[str]]:
    """Combine signals/risks from the Research Agent output with the
    matching demo record (signals only, no live research).

    The Research Agent output already carries ``opportunity_signals``
    derived from ``available_context`` deterministically, so in
    practice the demo record is a redundant source here. We still
    consult it as a backstop in case a future Research Agent
    implementation produces a leaner output; duplicates are dropped
    while preserving insertion order.
    """

    signals: list[str] = list(research_output.opportunity_signals)
    risks: list[str] = list(research_output.information_risks)

    if research_record is not None:
        for signal in research_record.opportunity_signals:
            if (
                isinstance(signal.signal, str)
                and signal.signal.strip()
                and signal.signal not in signals
            ):
                signals.append(signal.signal)
        for risk in research_record.information_risks:
            if (
                isinstance(risk, str)
                and risk.strip()
                and risk not in risks
            ):
                risks.append(risk)

    return signals, risks


def _research_summary_for_qualifier(
    research_output: ResearchAgentOutput,
    research_record: DemoCompanyResearch | None,
) -> str | None:
    if research_output.company_summary:
        return research_output.company_summary
    if research_record is None:
        return None
    return (
        research_record.recommended_research_summary
        or research_record.company_summary
        or None
    )


def run_pipeline_for_lead(lead_id: str) -> LeadPipelineContractOutput:
    """Run the deterministic Phase 6.1 pipeline for a single demo lead.

    Parameters
    ----------
    lead_id:
        The ``lead_id`` of a lead present in the demo dataset.

    Returns
    -------
    LeadPipelineContractOutput
        Container with all five agent slots populated, ``intake=None``
        (no Intake Agent runtime exists yet — only the contract
        schema), and a ``trace`` list with five entries (one per
        agent), in execution order.

    Raises
    ------
    ValueError
        If ``lead_id`` is not present in the demo dataset.
    """

    lead = _find_lead(lead_id)
    research_record = _find_research_record(lead_id)

    run_id = f"pipeline_{lead_id}_{uuid4().hex[:8]}"

    research_service = ResearchAgentService()
    research_input = ResearchAgentInput(
        lead=lead,
        run_id=run_id,
        available_context=_available_context(research_record),
    )
    research_output: ResearchAgentOutput = research_service.run(research_input)

    qualifier_signals, qualifier_risks = _qualifier_seed_signals(
        research_output, research_record
    )
    qualifier_service = QualifierAgentService()
    qualifier_input = QualifierAgentInput(
        lead=lead,
        research_summary=_research_summary_for_qualifier(
            research_output, research_record
        ),
        opportunity_signals=qualifier_signals,
        information_risks=qualifier_risks,
        run_id=run_id,
    )
    qualifier_output: QualifierAgentOutput = qualifier_service.run(qualifier_input)

    strategist_service = StrategistAgentService()
    strategist_input = StrategistAgentInput(
        lead=lead,
        company_summary=research_output.company_summary or "",
        opportunity_signals=list(research_output.opportunity_signals),
        pain_hypotheses=list(research_output.pain_hypotheses),
        fit_score=qualifier_output.fit_score,
        priority=qualifier_output.priority,
        run_id=run_id,
    )
    strategist_output: StrategistAgentOutput = strategist_service.run(
        strategist_input
    )

    email_service = EmailDrafterAgentService()
    email_input = EmailDrafterAgentInput(
        lead=lead,
        company_summary=research_output.company_summary or "",
        pain_hypothesis=strategist_output.pain_hypothesis,
        sales_angle=strategist_output.sales_angle,
        core_message=strategist_output.core_message,
        personalization_notes=list(strategist_output.personalization_notes),
        run_id=run_id,
    )
    email_output: EmailDrafterAgentOutput = email_service.run(email_input)

    qa_service = QAEvaluatorAgentService()
    qa_input = QAEvaluatorAgentInput(
        lead=lead,
        email_subject=email_output.email_subject,
        email_body=email_output.email_body,
        evidence_cards=list(research_output.evidence_cards),
        personalization_notes=list(email_output.personalization_notes),
        run_id=run_id,
    )
    qa_output: QAEvaluatorAgentOutput = qa_service.run(qa_input)

    trace: list[TraceEntry] = [
        _trace_entry(
            "research_agent",
            research_output.result,
            input_summary=f"lead={lead.lead_id}; available_context_keys="
            f"{sorted((_available_context(research_record) or {}).keys())}",
            output_summary=(
                f"company_summary_len={len(research_output.company_summary)}; "
                f"signals={len(research_output.opportunity_signals)}; "
                f"evidence={len(research_output.evidence_cards)}"
            ),
        ),
        _trace_entry(
            "qualifier_agent",
            qualifier_output.result,
            input_summary=(
                f"lead={lead.lead_id}; signals={len(qualifier_signals)}; "
                f"risks={len(qualifier_risks)}"
            ),
            output_summary=(
                f"fit_score={qualifier_output.fit_score}; "
                f"priority={qualifier_output.priority.value}"
            ),
        ),
        _trace_entry(
            "strategist_agent",
            strategist_output.result,
            input_summary=(
                f"lead={lead.lead_id}; fit_score={qualifier_output.fit_score}; "
                f"priority={qualifier_output.priority.value}"
            ),
            output_summary=(
                f"sales_angle_len={len(strategist_output.sales_angle)}; "
                f"pain_hypothesis_len={len(strategist_output.pain_hypothesis)}"
            ),
        ),
        _trace_entry(
            "email_drafter_agent",
            email_output.result,
            input_summary=(
                f"lead={lead.lead_id}; "
                f"core_message_len={len(strategist_output.core_message)}"
            ),
            output_summary=(
                f"subject_len={len(email_output.email_subject)}; "
                f"body_len={len(email_output.email_body)}"
            ),
        ),
        _trace_entry(
            "qa_evaluator_agent",
            qa_output.result,
            input_summary=(
                f"lead={lead.lead_id}; "
                f"evidence_cards={len(research_output.evidence_cards)}"
            ),
            output_summary=(
                f"qa_score={qa_output.qa_score}; "
                f"recommendation={qa_output.recommendation.value}"
            ),
        ),
    ]

    return LeadPipelineContractOutput(
        run_id=run_id,
        lead_id=lead_id,
        intake=None,
        research=research_output,
        qualification=qualifier_output,
        strategy=strategist_output,
        email=email_output,
        qa=qa_output,
        trace=trace,
    )


__all__ = ["run_pipeline_for_lead"]
