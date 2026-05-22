"""Pipeline Simulation Layer response schema (Phase 5.1).

This module intentionally contains a single class, ``SimulationRunResponse``,
which wraps a deterministic, in-memory replay of the demo dataset with
per-lead simulated outputs shaped exactly like the existing ``LeadDetail``
contract.

The simulation never calls an LLM, agent framework, RAG system, scraper,
external API, or writes to the database. ``run_mode`` is fixed to
``"simulation"``, ``model_calls`` to ``0``, and ``estimated_cost`` to
``"$0.00"`` so callers can never confuse a simulated run with a real one.

Agent contracts, scoring logic, and any other behavior live in
``app.services.simulation_service``. This schema is only the response
envelope.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lead import LeadDetail
from app.schemas.run import RunSummary


class SimulationRunResponse(BaseModel):
    """Response body for ``GET /api/demo/simulation``."""

    model_config = ConfigDict(extra="ignore")

    run_id: str
    run_mode: str
    status: str
    data_source: str
    source_name: str
    generated_at: datetime
    total_leads: int = Field(..., ge=0)
    model_calls: int = Field(..., ge=0)
    estimated_cost: str
    summary: RunSummary
    results: list[LeadDetail]
