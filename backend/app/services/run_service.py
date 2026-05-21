"""Replay run builder (Phase 4.4).

Pure function ``build_replay_run`` that turns an already-loaded list of
``LeadIn`` objects into a :class:`ReplayRunResponse`. This is the
backend contract that future real-run execution will eventually
populate; for now it is built from the static demo dataset only.

No model calls, no agents, no LangGraph, no DB writes, no external I/O.
"""

from __future__ import annotations

from datetime import datetime

from app.schemas.lead import LeadIn
from app.schemas.run import ReplayRunResponse, RunSummary

# ``ReplayRunResponse.leads`` uses a forward reference to ``LeadIn`` to
# avoid a circular import between ``app.schemas.run`` and
# ``app.schemas.lead`` (the latter already imports ``TraceEntry`` from
# the former). By the time this service module is imported, both schema
# modules are fully loaded, so resolving the reference here is safe.
ReplayRunResponse.model_rebuild(_types_namespace={"LeadIn": LeadIn})

_RUN_ID: str = "replay_demo_run_001"
_SOURCE_NAME: str = "LeadForge Demo Dataset"
_ESTIMATED_COST: str = "$0.00"


def _is_non_empty(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def build_replay_run(
    leads: list[LeadIn],
    leads_with_company_research: int = 0,
    include_leads: bool = True,
) -> ReplayRunResponse:
    """Build the replay run response from a list of demo leads.

    Parameters
    ----------
    leads:
        Already-loaded list of demo ``LeadIn`` objects. This function
        does NOT load anything from disk.
    leads_with_company_research:
        Pre-computed by the caller (the route) since cross-referencing
        leads against the company research file is the route's
        responsibility, not the service's.
    include_leads:
        If ``False``, ``ReplayRunResponse.leads`` is set to ``None`` so
        the response carries metadata + summary only.
    """

    total_leads = len(leads)

    valid_leads = sum(1 for lead in leads if _is_non_empty(lead.company_name))
    failed_leads = total_leads - valid_leads
    rows_with_warnings = sum(
        1
        for lead in leads
        if not _is_non_empty(lead.industry) or not _is_non_empty(lead.website)
    )

    industries_represented = sorted(
        {lead.industry for lead in leads if _is_non_empty(lead.industry)}
    )
    countries_represented = sorted(
        {lead.country for lead in leads if _is_non_empty(lead.country)}
    )

    leads_with_contact = sum(
        1 for lead in leads if _is_non_empty(lead.contact_name)
    )
    leads_without_contact = total_leads - leads_with_contact

    if leads_with_company_research < 0:
        leads_with_company_research = 0
    if leads_with_company_research > total_leads:
        leads_with_company_research = total_leads
    leads_without_company_research = total_leads - leads_with_company_research

    summary = RunSummary(
        industries_represented=industries_represented,
        countries_represented=countries_represented,
        leads_with_company_research=leads_with_company_research,
        leads_without_company_research=leads_without_company_research,
        leads_with_contact=leads_with_contact,
        leads_without_contact=leads_without_contact,
    )

    return ReplayRunResponse(
        run_id=_RUN_ID,
        run_mode="replay",
        status="completed",
        data_source="demo",
        source_name=_SOURCE_NAME,
        generated_at=datetime.utcnow(),
        total_leads=total_leads,
        valid_leads=valid_leads,
        failed_leads=failed_leads,
        rows_with_warnings=rows_with_warnings,
        model_calls=0,
        estimated_cost=_ESTIMATED_COST,
        warnings=[],
        summary=summary,
        leads=list(leads) if include_leads else None,
    )
