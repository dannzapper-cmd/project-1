"""Demo data endpoints (Fase 4.2).

Exposes read-only access to the static demo files shipped under
`data/demo/`. No DB writes, no LLM, no agents, no RAG.

Routing convention note: Fase 4.1 mounts `/health` at the application root
(no prefix). Feature endpoints introduced from Fase 4.2 onwards live under
`/api/...`. `/health` remains at the root unchanged.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.schemas.demo import DemoCompanyResearch, DemoSummary
from app.schemas.evaluation import (
    LeadEvaluationReport,
    LeadTraceReport,
    RunEvaluationSummary,
    RunTraceReport,
)
from app.schemas.lead import LeadIn
from app.schemas.run import ReplayRunResponse
from app.schemas.simulation import SimulationRunResponse
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
