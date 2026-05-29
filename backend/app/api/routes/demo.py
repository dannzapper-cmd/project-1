"""Demo data endpoints (Fase 4.2).

Exposes read-only access to the static demo files shipped under
`data/demo/`. No DB writes, no LLM, no agents, no RAG.

Routing convention note: Fase 4.1 mounts `/health` at the application root
(no prefix). Feature endpoints introduced from Fase 4.2 onwards live under
`/api/...`. `/health` remains at the root unchanged.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.agents import (
    EmailDrafterAgentOutput,
    LeadPipelineContractOutput,
    PipelineRunContractOutput,
    QAEvaluatorAgentOutput,
    QualifierAgentOutput,
    ResearchAgentOutput,
    StrategistAgentOutput,
)
from app.schemas.demo import DemoCompanyResearch, DemoSummary
from app.schemas.email_regenerate import (
    EmailRegenerateRequest,
    EmailRegenerateResponse,
)
from app.schemas.evaluation import (
    LeadEvaluationReport,
    LeadTraceReport,
    RunEvaluationSummary,
    RunTraceReport,
)
from app.schemas.lead import LeadBatchProcessRequest, LeadIn
from app.schemas.model import (
    ModelConfig,
    ModelMessage,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelRole,
)
from app.schemas.run import ReplayRunResponse
from app.schemas.simulation import SimulationRunResponse
from app.services.agent_demo_service import (
    build_all_demo_email_drafter_agent_outputs,
    build_all_demo_qa_evaluator_agent_outputs,
    build_all_demo_qualifier_agent_outputs,
    build_all_demo_research_agent_outputs,
    build_all_demo_strategist_agent_outputs,
    build_demo_email_drafter_agent_groq_output,
    build_demo_email_drafter_agent_output,
    build_demo_qa_evaluator_agent_groq_output,
    build_demo_qa_evaluator_agent_output,
    build_demo_qualifier_agent_output,
    build_demo_research_agent_output,
    build_demo_strategist_agent_groq_output,
    build_demo_strategist_agent_output,
)
from app.services.demo_data_loader import (
    DemoDataError,
    build_demo_summary,
    load_demo_company_research,
    load_demo_leads,
)
from app.services.evaluation_service import (
    build_lead_evaluation_report,
    build_lead_trace_report,
    build_run_evaluation_summary,
    build_run_trace_report,
)
from app.schemas.live_pipeline import LivePipelineResponse
from app.services.live_pipeline_service import (
    LivePipelineDisabledError,
    LivePipelineKeyMissingError,
    LivePipelineLeadNotFoundError,
    run_live_groq_pipeline_for_lead,
)
from app.services.model_service import GroqModelService, get_model_service
from app.services.pipeline_service import (
    run_pipeline_for_demo_leads,
    run_pipeline_for_lead,
    run_pipeline_for_user_leads,
)
from app.services.run_service import build_replay_run
from app.services.simulation_service import build_simulation_run

router = APIRouter(prefix="/api/demo", tags=["demo"])
logger = get_logger(__name__)


def _raise_500(exc: DemoDataError) -> None:
    logger.exception("Demo data loading failed")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(exc),
    )


@router.get("/leads", response_model=list[LeadIn])
def get_demo_leads() -> list[LeadIn]:
    try:
        return load_demo_leads()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover  (unreachable; _raise_500 always raises)


@router.get("/leads/{lead_id}", response_model=LeadIn)
def get_demo_lead(lead_id: str) -> LeadIn:
    try:
        leads = load_demo_leads()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover

    for lead in leads:
        if lead.lead_id == lead_id:
            return lead

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Lead '{lead_id}' not found in demo dataset",
    )


@router.get("/company-research", response_model=list[DemoCompanyResearch])
def get_demo_company_research() -> list[DemoCompanyResearch]:
    try:
        return load_demo_company_research()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get("/company-research/{lead_id}", response_model=DemoCompanyResearch)
def get_demo_company_research_by_id(lead_id: str) -> DemoCompanyResearch:
    try:
        research = load_demo_company_research()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover

    for record in research:
        if record.lead_id == lead_id:
            return record

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Company research for '{lead_id}' not found in demo dataset",
    )


@router.get("/summary", response_model=DemoSummary)
def get_demo_summary() -> DemoSummary:
    try:
        return build_demo_summary()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get("/run", response_model=ReplayRunResponse)
def get_demo_run(include_leads: bool = True) -> ReplayRunResponse:
    """Return a deterministic replay run built from the demo dataset.

    This endpoint reuses the Phase 4.2 demo loaders. It does not call
    any model, agent, or external service, and it does not write to the
    database. The ``run_id`` is fixed so repeated calls produce a
    stable, testable response.
    """

    try:
        leads = load_demo_leads()
        research = load_demo_company_research()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover

    lead_ids = {lead.lead_id for lead in leads}
    research_ids = {record.lead_id for record in research}
    leads_with_company_research = len(lead_ids & research_ids)

    return build_replay_run(
        leads=leads,
        leads_with_company_research=leads_with_company_research,
        include_leads=include_leads,
    )


@router.get("/simulation", response_model=SimulationRunResponse)
def get_simulation_run() -> SimulationRunResponse:
    """Return a deterministic pipeline simulation built from the demo dataset.

    Phase 5.1. This endpoint produces per-lead simulated agent outputs
    (research summary, qualification, strategy, email draft, QA scores,
    trace) using the rubric transcribed from ``knowledge/icp_rules.md``.
    It NEVER calls an LLM, agent framework, RAG system, scraper, or any
    external service, and it does not write to the database. The
    response is clearly labelled as a simulation (``run_mode="simulation"``,
    ``model_calls=0``, ``estimated_cost="$0.00"``, and every trace step
    carries ``simulated=True`` with ``model="none"``).
    """

    try:
        return build_simulation_run()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


# --------------------------------------------------------------------------- #
# Phase 5.3 — Trace & Evaluation Foundation                                   #
#                                                                             #
# Route ordering is intentional (Phase 5.3 FIX 1): the static                 #
# `/simulation/trace` and `/simulation/evaluation` routes are declared        #
# BEFORE the corresponding `/{lead_id}` dynamic routes so FastAPI's path      #
# matcher cannot interpret the literal segments as a lead id. The existing    #
# `GET /simulation` above has no path parameter, so it does not conflict.     #
# --------------------------------------------------------------------------- #


@router.get("/simulation/trace", response_model=RunTraceReport)
def get_simulation_trace() -> RunTraceReport:
    """Return a run-level trace report derived from the current simulation."""

    try:
        return build_run_trace_report()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get("/simulation/evaluation", response_model=RunEvaluationSummary)
def get_simulation_evaluation() -> RunEvaluationSummary:
    """Return a run-level evaluation summary derived from the current simulation."""

    try:
        return build_run_evaluation_summary()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get("/simulation/trace/{lead_id}", response_model=LeadTraceReport)
def get_simulation_trace_for_lead(lead_id: str) -> LeadTraceReport:
    """Return the trace report for a single simulated lead."""

    try:
        return build_lead_trace_report(lead_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get(
    "/simulation/evaluation/{lead_id}", response_model=LeadEvaluationReport
)
def get_simulation_evaluation_for_lead(lead_id: str) -> LeadEvaluationReport:
    """Return the evaluation report for a single simulated lead."""

    try:
        return build_lead_evaluation_report(lead_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


# --------------------------------------------------------------------------- #
# Phase 5.4 — Model service foundation                                        #
#                                                                             #
# The prefix /api/demo/model-service/ does not conflict with any existing     #
# /api/demo/simulation/ route (Phase 5.4 FIX 5). Phase 5.4 intentionally      #
# ships ONLY the mock-check endpoint: there is no POST completion endpoint    #
# and no way to feed an arbitrary prompt to a real provider through the      #
# HTTP surface in this phase.                                                 #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Phase 5.5A — Research agent foundation                                      #
#                                                                             #
# Routes live under /api/demo/agents/ to keep them clearly separated from     #
# /api/demo/simulation/ (Phase 5.1 / 5.3) and /api/demo/model-service/        #
# (Phase 5.4). No POST endpoint and no arbitrary-prompt HTTP surface is       #
# exposed: prompts are constructed server-side by ResearchAgentService.       #
# --------------------------------------------------------------------------- #


@router.get("/agents/research", response_model=list[ResearchAgentOutput])
def get_agents_research() -> list[ResearchAgentOutput]:
    """Run the Phase 5.5A Research Agent against every demo lead.

    Uses :class:`MockModelService` only; no real provider, no API key,
    no network call. Output ordering mirrors the demo CSV row order.
    """

    try:
        return build_all_demo_research_agent_outputs()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get(
    "/agents/research/{lead_id}", response_model=ResearchAgentOutput
)
def get_agents_research_for_lead(lead_id: str) -> ResearchAgentOutput:
    """Run the Phase 5.5A Research Agent against a single demo lead."""

    try:
        return build_demo_research_agent_output(lead_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


# --------------------------------------------------------------------------- #
# Phase 5.6A — Qualifier Agent foundation                                     #
#                                                                             #
# Sibling routes to /api/demo/agents/research. Deterministic and mock-only:   #
# the qualifier never calls Groq in this phase. No POST endpoint, no          #
# arbitrary-prompt surface.                                                   #
# --------------------------------------------------------------------------- #


@router.get("/agents/qualifier", response_model=list[QualifierAgentOutput])
def get_agents_qualifier() -> list[QualifierAgentOutput]:
    """Run the Phase 5.6A Qualifier Agent against every demo lead.

    Deterministic scoring via the shared :mod:`app.services.icp_scoring`
    rubric; no model service call, no real provider. Output order
    mirrors the demo CSV row order.
    """

    try:
        return build_all_demo_qualifier_agent_outputs()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get(
    "/agents/qualifier/{lead_id}", response_model=QualifierAgentOutput
)
def get_agents_qualifier_for_lead(lead_id: str) -> QualifierAgentOutput:
    """Run the Phase 5.6A Qualifier Agent against a single demo lead."""

    try:
        return build_demo_qualifier_agent_output(lead_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


# --------------------------------------------------------------------------- #
# Phase 5.5C — Optional Groq structured-synthesis path for ONE lead at a time #
#                                                                             #
# Existing /api/demo/agents/research[/lead_id] routes stay mock-backed by    #
# default. This endpoint is the only HTTP surface that routes through        #
# GroqModelService for the Research Agent in Phase 5.5C; it is one-lead-at-a- #
# time on purpose to control cost. No POST endpoint, no arbitrary-prompt     #
# surface, no all-leads Groq endpoint.                                       #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Phase 5.7 — Strategist Agent foundation + optional Groq synthesis           #
#                                                                             #
# Sibling routes to /api/demo/agents/research and /api/demo/agents/qualifier. #
# /strategist[/lead_id] are deterministic (no Groq); /strategist-groq/{id}   #
# is the single-lead-at-a-time Groq path (HTTP 503 when GROQ_API_KEY is       #
# missing). No POST endpoint and no all-leads Groq endpoint.                 #
# --------------------------------------------------------------------------- #


@router.get("/agents/strategist", response_model=list[StrategistAgentOutput])
def get_agents_strategist() -> list[StrategistAgentOutput]:
    """Run the Phase 5.7 deterministic Strategist Agent against every
    demo lead. No Groq call."""

    try:
        return build_all_demo_strategist_agent_outputs()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get(
    "/agents/strategist/{lead_id}", response_model=StrategistAgentOutput
)
def get_agents_strategist_for_lead(lead_id: str) -> StrategistAgentOutput:
    """Run the Phase 5.7 deterministic Strategist Agent against a single
    demo lead."""

    try:
        return build_demo_strategist_agent_output(lead_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get(
    "/agents/strategist-groq/{lead_id}", response_model=StrategistAgentOutput
)
def get_agents_strategist_groq_for_lead(lead_id: str) -> StrategistAgentOutput:
    """Run the Phase 5.7 Strategist Agent against a single demo lead
    via :class:`GroqModelService` with ``use_model_synthesis=True``.

    Returns HTTP 503 when ``GROQ_API_KEY`` is missing, HTTP 404 when
    ``lead_id`` is unknown. On JSON validation or guardrail failure
    the agent falls back to the deterministic strategy with an
    explicit risk note.
    """

    # Catch both flavours of ValueError raised below: "not found in the
    # demo dataset" → 404; "GROQ_API_KEY is required..." → 503. We
    # branch on substring rather than the exception type so the helper
    # does not need to introduce a new exception class.
    try:
        return build_demo_strategist_agent_groq_output(lead_id)
    except ValueError as exc:
        message = str(exc)
        if "GROQ_API_KEY" in message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=message,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


# --------------------------------------------------------------------------- #
# Phase 5.9 — QA Evaluator Agent foundation + optional Groq synthesis         #
#                                                                             #
# Sibling routes to /api/demo/agents/research, /qualifier, /strategist and    #
# /email-drafter. /qa-evaluator[/lead_id] are deterministic (no Groq);       #
# /qa-evaluator-groq/{id} is the single-lead-at-a-time Groq path (HTTP 503    #
# when GROQ_API_KEY is missing). No POST endpoint, no all-leads Groq         #
# endpoint, no email is ever sent — the QA Evaluator only evaluates.        #
# --------------------------------------------------------------------------- #


@router.get("/agents/qa-evaluator", response_model=list[QAEvaluatorAgentOutput])
def get_agents_qa_evaluator() -> list[QAEvaluatorAgentOutput]:
    """Run the Phase 5.9 deterministic QA Evaluator Agent against every
    demo lead. No Groq call. No email is sent."""

    try:
        return build_all_demo_qa_evaluator_agent_outputs()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get(
    "/agents/qa-evaluator/{lead_id}", response_model=QAEvaluatorAgentOutput
)
def get_agents_qa_evaluator_for_lead(
    lead_id: str,
) -> QAEvaluatorAgentOutput:
    """Run the Phase 5.9 deterministic QA Evaluator Agent against a
    single demo lead."""

    try:
        return build_demo_qa_evaluator_agent_output(lead_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get(
    "/agents/qa-evaluator-groq/{lead_id}",
    response_model=QAEvaluatorAgentOutput,
)
def get_agents_qa_evaluator_groq_for_lead(
    lead_id: str,
) -> QAEvaluatorAgentOutput:
    """Run the Phase 5.9 QA Evaluator Agent against a single demo lead
    via :class:`GroqModelService` with ``use_model_synthesis=True``.

    Returns HTTP 503 when ``GROQ_API_KEY`` is missing, HTTP 404 when
    ``lead_id`` is unknown. On JSON validation or guardrail failure
    the agent falls back to the deterministic evaluation with an
    explicit risk note.
    """

    try:
        return build_demo_qa_evaluator_agent_groq_output(lead_id)
    except ValueError as exc:
        message = str(exc)
        if "GROQ_API_KEY" in message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=message,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


# --------------------------------------------------------------------------- #
# Phase 5.8 — Email Drafter Agent foundation + optional Groq synthesis        #
#                                                                             #
# Sibling routes to /api/demo/agents/research, /qualifier and /strategist.    #
# /email-drafter[/lead_id] are deterministic (no Groq); /email-drafter-groq/  #
# {id} is the single-lead-at-a-time Groq path (HTTP 503 when GROQ_API_KEY     #
# is missing). No POST endpoint, no all-leads Groq endpoint, no email is      #
# ever sent — these endpoints only return reviewable draft text.              #
# --------------------------------------------------------------------------- #


@router.get("/agents/email-drafter", response_model=list[EmailDrafterAgentOutput])
def get_agents_email_drafter() -> list[EmailDrafterAgentOutput]:
    """Run the Phase 5.8 deterministic Email Drafter Agent against every
    demo lead. No Groq call. No email is sent."""

    try:
        return build_all_demo_email_drafter_agent_outputs()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get(
    "/agents/email-drafter/{lead_id}", response_model=EmailDrafterAgentOutput
)
def get_agents_email_drafter_for_lead(
    lead_id: str,
) -> EmailDrafterAgentOutput:
    """Run the Phase 5.8 deterministic Email Drafter Agent against a
    single demo lead."""

    try:
        return build_demo_email_drafter_agent_output(lead_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get(
    "/agents/email-drafter-groq/{lead_id}",
    response_model=EmailDrafterAgentOutput,
)
def get_agents_email_drafter_groq_for_lead(
    lead_id: str,
) -> EmailDrafterAgentOutput:
    """Run the Phase 5.8 Email Drafter Agent against a single demo lead
    via :class:`GroqModelService` with ``use_model_synthesis=True``.

    Returns HTTP 503 when ``GROQ_API_KEY`` is missing, HTTP 404 when
    ``lead_id`` is unknown. On JSON validation or guardrail failure
    the agent falls back to the deterministic draft with an explicit
    risk note. No email is ever sent.
    """

    try:
        return build_demo_email_drafter_agent_groq_output(lead_id)
    except ValueError as exc:
        message = str(exc)
        if "GROQ_API_KEY" in message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=message,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.post(
    "/email/regenerate-draft/{lead_id}",
    response_model=EmailRegenerateResponse,
)
def post_regenerate_email_draft_for_lead(
    lead_id: str,
    payload: EmailRegenerateRequest,
) -> EmailRegenerateResponse:
    """Regenerate one reviewable email draft via controlled backend Groq.

    One selected lead context enters, one draft-only response leaves. This
    route never sends email, never writes CRM, and never exposes a batch live
    model surface. The global safety middleware protects it with demo access
    and live request rate limits when configured.
    """

    settings = get_settings()
    if not settings.enable_live_model_pipeline:
        return EmailRegenerateResponse(
            status="disabled",
            mode="off",
            lead_id=lead_id,
            user_message="Regenerate draft requires controlled backend live mode.",
            warnings=[
                "ENABLE_LIVE_MODEL_PIPELINE is not enabled on this backend.",
            ],
        )
    if not settings.groq_api_key:
        return EmailRegenerateResponse(
            status="unavailable",
            mode="off",
            lead_id=lead_id,
            user_message="Regenerate draft requires backend Groq configuration.",
            warnings=["No frontend API key is accepted or exposed."],
        )
    if not settings.rate_limit_enabled or not (settings.demo_access_code or "").strip():
        return EmailRegenerateResponse(
            status="disabled",
            mode="off",
            lead_id=lead_id,
            user_message="Regenerate draft requires demo access and live rate limits.",
            warnings=[
                "Live draft generation stays disabled until demo access and "
                "rate limiting are configured.",
            ],
        )

    from app.agents.email_drafter_agent import EmailDrafterAgentService
    from app.schemas.agents import EmailDrafterAgentInput

    context = payload.lead
    personalization_notes = [
        note.strip()[:300]
        for note in context.personalization_notes
        if isinstance(note, str) and note.strip()
    ][:5]
    if not personalization_notes:
        personalization_notes = [
            "Use only the selected lead context and keep the draft exploratory."
        ]

    agent_input = EmailDrafterAgentInput(
        lead=LeadIn(
            lead_id=lead_id,
            company_name=context.company_name,
            website=context.website,
            industry=context.industry,
            country=context.country,
            employee_count=context.employee_count,
            contact_name=context.contact_name,
            contact_role=context.contact_role,
            notes=None,
        ),
        company_summary=context.company_summary or "",
        pain_hypothesis=(
            context.pain_hypothesis
            or "Explore whether the team is spending too much time on manual lead qualification."
        ),
        sales_angle=(
            context.sales_angle
            or "Use a concise, low-pressure sales-operations angle based on available context."
        ),
        core_message=(
            context.core_message
            or "Offer a reviewable example of how LeadForge prioritizes and drafts outreach."
        ),
        personalization_notes=personalization_notes,
        run_id=f"email_regenerate_{lead_id}",
    )

    try:
        groq_service = GroqModelService(default_model=settings.groq_default_model)
        output = EmailDrafterAgentService(
            model_service=groq_service,
            use_model_synthesis=True,
        ).run(agent_input)
    except ValueError:
        return EmailRegenerateResponse(
            status="provider_error",
            mode="off",
            lead_id=lead_id,
            user_message=(
                "The backend could not regenerate this draft. Replay draft "
                "remains available."
            ),
            warnings=["Provider configuration or response validation failed."],
        )

    metadata = output.result.metadata
    if output.result.success and not metadata.simulated:
        response_status = "ok"
        response_mode = "live_groq"
        message = "Live Groq draft regenerated for this lead only. Draft not sent."
        warnings: list[str] = []
    elif output.result.success:
        response_status = "deterministic_fallback"
        response_mode = "deterministic_fallback"
        message = (
            "Live draft failed guardrails, so the deterministic replay draft "
            "was kept for review."
        )
        warnings = list(output.personalization_notes[-1:])
    else:
        response_status = "provider_error"
        response_mode = "off"
        message = (
            "The backend could not regenerate this draft. Replay draft remains "
            "available."
        )
        warnings = [
            "Provider generation failed before a safe live draft was produced.",
        ]

    return EmailRegenerateResponse(
        status=response_status,
        mode=response_mode,
        lead_id=output.lead_id,
        email_subject=output.email_subject,
        email_body=output.email_body,
        personalization_notes=list(output.personalization_notes),
        provider="groq" if response_mode == "live_groq" else "none",
        model=metadata.model,
        latency=metadata.latency,
        tokens=metadata.tokens,
        estimated_cost=metadata.cost,
        user_message=message,
        warnings=warnings,
    )


# --------------------------------------------------------------------------- #
# Phase 5.6B — Optional Groq qualifier path for ONE lead at a time            #
# --------------------------------------------------------------------------- #


@router.get(
    "/agents/qualifier-groq/{lead_id}", response_model=QualifierAgentOutput
)
def get_agents_qualifier_groq_for_lead(lead_id: str) -> QualifierAgentOutput:
    """Run the Qualifier Agent against a single demo lead via GroqModelService.

    Returns HTTP 503 when ``GROQ_API_KEY`` is missing, HTTP 404 when
    ``lead_id`` is unknown. Otherwise routes the lead's demo context
    through :class:`GroqModelService` with
    ``QualifierAgentService(use_model_synthesis=True)``; on validation
    or guardrail failure the agent falls back to its deterministic
    output with an explicit risk note.
    """

    # Local imports keep FastAPI startup independent of the Groq SDK
    # (same defensive pattern as ``/groq-check`` and ``/research-groq``).
    from app.agents.qualifier_agent import QualifierAgentService
    from app.schemas.agents import QualifierAgentInput
    from app.schemas.demo import DemoCompanyResearch
    from app.services.demo_data_loader import (
        load_demo_company_research,
        load_demo_leads,
    )
    from app.services.model_service import GroqModelService

    try:
        leads = load_demo_leads()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover

    matching_lead = next((lead for lead in leads if lead.lead_id == lead_id), None)
    if matching_lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead '{lead_id}' not found in the demo dataset.",
        )

    try:
        research_records = load_demo_company_research()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover

    matching_research: DemoCompanyResearch | None = next(
        (record for record in research_records if record.lead_id == lead_id),
        None,
    )

    research_summary: str | None = None
    opportunity_signals: list[str] = []
    information_risks: list[str] = []
    if matching_research is not None:
        research_summary = (
            matching_research.recommended_research_summary
            or matching_research.company_summary
            or None
        )
        opportunity_signals = [
            signal.signal
            for signal in matching_research.opportunity_signals
            if isinstance(signal.signal, str) and signal.signal.strip()
        ]
        information_risks = [
            risk
            for risk in matching_research.information_risks
            if isinstance(risk, str) and risk.strip()
        ]

    try:
        groq_service = GroqModelService(default_model="llama-3.1-8b-instant")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    agent = QualifierAgentService(
        model_service=groq_service, use_model_synthesis=True
    )
    return agent.run(
        QualifierAgentInput(
            lead=matching_lead,
            research_summary=research_summary,
            opportunity_signals=opportunity_signals,
            information_risks=information_risks,
            run_id="qualifier_agent_groq_demo_run_001",
        )
    )


@router.get(
    "/agents/research-groq/{lead_id}", response_model=ResearchAgentOutput
)
def get_agents_research_groq_for_lead(lead_id: str) -> ResearchAgentOutput:
    """Run the Research Agent against a single demo lead via GroqModelService.

    Returns HTTP 503 with a clear configuration message when
    ``GROQ_API_KEY`` is missing. Returns HTTP 404 if ``lead_id`` is
    unknown. Otherwise routes the lead's demo context through
    :class:`GroqModelService` with ``use_model_synthesis=True``; if
    JSON validation fails the agent falls back to the deterministic
    Phase 5.5A output (with an explicit risk note).
    """

    # Local imports keep the FastAPI startup path independent of the
    # Groq SDK availability — the same defensive pattern used for
    # /model-service/groq-check.
    from app.agents.research_agent import ResearchAgentService
    from app.schemas.agents import ResearchAgentInput
    from app.services.demo_data_loader import (
        load_demo_company_research,
        load_demo_leads,
    )
    from app.services.model_service import GroqModelService

    try:
        leads = load_demo_leads()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover

    matching_lead = next((lead for lead in leads if lead.lead_id == lead_id), None)
    if matching_lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead '{lead_id}' not found in the demo dataset.",
        )

    try:
        research_records = load_demo_company_research()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover

    matching_research = next(
        (record for record in research_records if record.lead_id == lead_id),
        None,
    )
    available_context = (
        matching_research.model_dump() if matching_research is not None else None
    )

    try:
        groq_service = GroqModelService(default_model="llama-3.1-8b-instant")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    agent = ResearchAgentService(
        model_service=groq_service, use_model_synthesis=True
    )
    return agent.run(
        ResearchAgentInput(
            lead=matching_lead,
            run_id="research_agent_groq_demo_run_001",
            available_context=available_context,
        )
    )


@router.get("/model-service/mock-check", response_model=ModelResponse)
def model_service_mock_check() -> ModelResponse:
    """Return a deterministic mock ``ModelResponse`` for foundation checks.

    Uses ``MockModelService`` only — no external provider, no API key,
    no network call. The response is clearly labelled with
    ``provider="mock"``, ``simulated=True``, and a ``[MOCK MODEL
    RESPONSE — no external model was called]`` marker in the content.
    """

    service = get_model_service(ModelProvider.MOCK)
    request = ModelRequest(
        request_id="model_service_mock_check",
        messages=[
            ModelMessage(
                role=ModelRole.USER,
                content="Check LeadForge model service foundation.",
            )
        ],
    )
    return service.complete(request)


# --------------------------------------------------------------------------- #
# Phase 5.5B — Groq provider foundation                                       #
#                                                                             #
# Optional, read-only endpoint that proves the Groq pathway end-to-end        #
# WHEN a ``GROQ_API_KEY`` has been configured. When the key is missing,       #
# the endpoint returns HTTP 503 with a clear configuration message — the      #
# app itself starts and serves normally without the key.                      #
# --------------------------------------------------------------------------- #

_GROQ_CHECK_MODEL: str = "llama-3.1-8b-instant"
_GROQ_CHECK_PROMPT: str = "Return exactly: LeadForge Groq check OK"
_GROQ_CHECK_MAX_TOKENS: int = 32


@router.get("/model-service/groq-check", response_model=ModelResponse)
def model_service_groq_check() -> ModelResponse:
    """One-shot, server-side prompt routed through ``GroqModelService``.

    No user input. No arbitrary-prompt surface. When ``GROQ_API_KEY`` is
    missing, returns HTTP 503 with a clear configuration message instead
    of attempting a call.
    """

    try:
        service = GroqModelService(default_model=_GROQ_CHECK_MODEL)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    request = ModelRequest(
        request_id="model_service_groq_check",
        messages=[
            ModelMessage(role=ModelRole.USER, content=_GROQ_CHECK_PROMPT)
        ],
        config=ModelConfig(
            provider=ModelProvider.GROQ,
            model_name=_GROQ_CHECK_MODEL,
            max_tokens=_GROQ_CHECK_MAX_TOKENS,
        ),
    )
    return service.complete(request)


# --------------------------------------------------------------------------- #
# Phase 6.1 — Plain Python Pipeline Orchestration (single demo lead)          #
#                                                                             #
# Deterministic in-process orchestration over the existing Research,          #
# Qualifier, Strategist, Email Drafter and QA Evaluator agent services.       #
# No Groq, no LangGraph, no DB writes, no email sending, no all-leads         #
# endpoint, no arbitrary-prompt surface.                                      #
#                                                                             #
# Phase 6.2 adds GET /pipeline/batch *before* GET /pipeline/{lead_id} so      #
# FastAPI's path matcher cannot interpret "batch" as a lead_id (same          #
# ordering rule already applied to /simulation/trace and                      #
# /simulation/evaluation in Phase 5.3).                                       #
# --------------------------------------------------------------------------- #


@router.get("/pipeline/batch", response_model=PipelineRunContractOutput)
def get_pipeline_batch() -> PipelineRunContractOutput:
    """Phase 6.2 — Deterministic batch pipeline for demo leads.
    Processes up to 10 demo leads. No Groq, no email sending."""
    try:
        return run_pipeline_for_demo_leads()
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.post("/pipeline/batch", response_model=PipelineRunContractOutput)
def post_pipeline_batch(
    request: LeadBatchProcessRequest,
) -> PipelineRunContractOutput:
    """Block 10A — deterministic batch pipeline for user-provided leads.

    Leads must already be normalized and preview-confirmed by the intake UI/API.
    This reuses the existing deterministic five-agent pipeline, never calls
    Groq, never performs live research, and respects MAX_LEADS_PER_RUN.
    """

    settings = get_settings()
    if len(request.leads) > settings.max_leads_per_run:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"This demo processes up to {settings.max_leads_per_run} "
                "leads per run. Remove extra rows and try again."
            ),
        )

    try:
        return run_pipeline_for_user_leads(
            request.leads,
            max_leads=settings.max_leads_per_run,
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


@router.get("/pipeline/{lead_id}", response_model=LeadPipelineContractOutput)
def get_pipeline_for_lead(lead_id: str) -> LeadPipelineContractOutput:
    """Phase 6.1 — Deterministic pipeline for a single demo lead.
    Returns 404 for unknown lead_id. No Groq, no email sending."""
    try:
        return run_pipeline_for_lead(lead_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover


# --------------------------------------------------------------------------- #
# Block 8.3 — Minimal live Groq single-lead pipeline                          #
#                                                                             #
# POST is used because the call incurs a real cost and is not idempotent in   #
# a meaningful sense (the deterministic baseline is reproducible, but each    #
# Groq call consumes provider quota). The endpoint runs the live chain for   #
# exactly one lead, returns the deterministic baseline alongside the live    #
# result for comparison, and never silently substitutes deterministic output #
# for a failed live run. There is no batch live endpoint by design.          #
# --------------------------------------------------------------------------- #


@router.post(
    "/pipeline/live-groq/{lead_id}",
    response_model=LivePipelineResponse,
)
def post_pipeline_live_groq_for_lead(lead_id: str) -> LivePipelineResponse:
    """Block 8.3 — Live Groq pipeline for exactly one demo lead.

    Returns:
    * HTTP 503 when ``ENABLE_LIVE_MODEL_PIPELINE`` is not enabled,
    * HTTP 503 when ``GROQ_API_KEY`` is missing,
    * HTTP 404 when ``lead_id`` is unknown,
    * HTTP 200 otherwise — including when the live run itself fails
      mid-pipeline. In the failure case the body's ``live_success``
      is ``False``, ``failed_agent`` / ``failure_stage`` / ``error_code``
      are set, and the deterministic baseline is preserved as
      comparison context.
    """

    try:
        return run_live_groq_pipeline_for_lead(lead_id)
    except LivePipelineDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except LivePipelineKeyMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except LivePipelineLeadNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DemoDataError as exc:
        _raise_500(exc)
        raise  # pragma: no cover
