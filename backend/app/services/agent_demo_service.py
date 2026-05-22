"""Demo wiring for the Phase 5.5A Research Agent service.

Bridges the existing demo loaders (Phase 4.2) and the
:class:`app.agents.research_agent.ResearchAgentService` so the
agent can be exercised end-to-end against the bundled demo dataset
without any new data dependency.

Hard guarantees:

* Deterministic and read-only. No DB writes, no network I/O, no
  knowledge-file parsing, no LLM call. Internally the agent uses
  ``MockModelService`` (Phase 5.4) only.
* Does not mutate the Phase 5.1 simulation pipeline. This is a
  separate demo path for the first executable agent service and is
  intentionally NOT wired into ``/api/demo/simulation``.
* ``available_context`` is built via ``DemoCompanyResearch.model_dump()``
  so the agent receives a plain ``dict`` matching the
  ``ResearchAgentInput.available_context: dict | None`` contract
  (Phase 5.5A FIX 2).

Public surface:

* :func:`build_demo_research_agent_output(lead_id)` -- single lead.
* :func:`build_all_demo_research_agent_outputs()`   -- every demo lead.
"""

from __future__ import annotations

from app.agents.research_agent import ResearchAgentService
from app.schemas.agents import ResearchAgentInput, ResearchAgentOutput
from app.schemas.demo import DemoCompanyResearch
from app.schemas.lead import LeadIn
from app.services.demo_data_loader import (
    load_demo_company_research,
    load_demo_leads,
)

_DEMO_RUN_ID: str = "research_agent_demo_run_001"


def _build_available_context(
    research: DemoCompanyResearch | None,
) -> dict | None:
    """Return the plain dict form of a research record (Phase 5.5A FIX 2).

    The :class:`ResearchAgentInput.available_context` field is typed as
    ``dict | None``; passing the Pydantic model directly would be
    rejected by Pydantic v2. ``model_dump()`` is the supported v2 way
    to project a model to a plain dict.
    """

    if research is None:
        return None
    return research.model_dump()


def _run_research_agent_for(
    lead: LeadIn,
    research: DemoCompanyResearch | None,
    *,
    service: ResearchAgentService | None = None,
) -> ResearchAgentOutput:
    agent = service if service is not None else ResearchAgentService()
    agent_input = ResearchAgentInput(
        lead=lead,
        run_id=_DEMO_RUN_ID,
        available_context=_build_available_context(research),
    )
    return agent.run(agent_input)


def build_demo_research_agent_output(lead_id: str) -> ResearchAgentOutput:
    """Run the Research Agent against a single demo lead.

    Raises
    ------
    ValueError
        If ``lead_id`` is not present in the demo lead dataset. The
        route layer translates this into HTTP 404.
    """

    leads = load_demo_leads()
    matching_lead: LeadIn | None = next(
        (lead for lead in leads if lead.lead_id == lead_id), None
    )
    if matching_lead is None:
        raise ValueError(
            f"Lead '{lead_id}' not found in the demo dataset."
        )

    research_records = load_demo_company_research()
    matching_research = next(
        (record for record in research_records if record.lead_id == lead_id),
        None,
    )
    return _run_research_agent_for(matching_lead, matching_research)


def build_all_demo_research_agent_outputs() -> list[ResearchAgentOutput]:
    """Run the Research Agent against every demo lead.

    The output order mirrors :func:`load_demo_leads` (i.e. CSV row
    order), which is deterministic.
    """

    leads = load_demo_leads()
    research_records = load_demo_company_research()
    research_by_id = {record.lead_id: record for record in research_records}

    # Single ResearchAgentService instance so every lead shares the
    # same MockModelService — small allocation, deterministic results.
    service = ResearchAgentService()

    outputs: list[ResearchAgentOutput] = []
    for lead in leads:
        outputs.append(
            _run_research_agent_for(
                lead, research_by_id.get(lead.lead_id), service=service
            )
        )
    return outputs


__all__ = [
    "build_demo_research_agent_output",
    "build_all_demo_research_agent_outputs",
]
