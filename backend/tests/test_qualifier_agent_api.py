"""Integration tests for the Phase 5.6A Qualifier Agent endpoints and
regression checks for the pre-existing endpoints we must not break.

Test IDs map 1:1 to the Phase 5.6A spec (A-01 .. A-12).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_LIST_URL = "/api/demo/agents/qualifier"
_DETAIL_URL = "/api/demo/agents/qualifier/{lead_id}"


def test_a01_get_qualifier_list_returns_200() -> None:
    """A-01: GET /api/demo/agents/qualifier returns 200."""

    with TestClient(app) as client:
        response = client.get(_LIST_URL)
    assert response.status_code == 200


def test_a02_qualifier_list_is_non_empty() -> None:
    """A-02: response is a non-empty list."""

    with TestClient(app) as client:
        response = client.get(_LIST_URL)
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0


def test_a03_every_output_has_qualifier_agent_name() -> None:
    """A-03: every output has result.metadata.agent_name == "qualifier_agent"."""

    with TestClient(app) as client:
        response = client.get(_LIST_URL)
    body = response.json()
    for output in body:
        meta = output["result"]["metadata"]
        assert meta["agent_name"] == "qualifier_agent"
        assert meta["simulated"] is True


def test_a04_get_qualifier_for_known_lead_returns_200() -> None:
    """A-04: GET /api/demo/agents/qualifier/lead_001 returns 200."""

    with TestClient(app) as client:
        response = client.get(_DETAIL_URL.format(lead_id="lead_001"))
    assert response.status_code == 200


def test_a05_qualifier_for_lead_001_returns_matching_lead_id() -> None:
    """A-05: lead_001 response lead_id == "lead_001"."""

    with TestClient(app) as client:
        response = client.get(_DETAIL_URL.format(lead_id="lead_001"))
    body = response.json()
    assert body["lead_id"] == "lead_001"


def test_a06_qualifier_for_missing_lead_returns_404() -> None:
    """A-06: GET /api/demo/agents/qualifier/missing_lead returns 404."""

    with TestClient(app) as client:
        response = client.get(_DETAIL_URL.format(lead_id="missing_lead"))
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Regression / stability                                                      #
# --------------------------------------------------------------------------- #


def test_a07_research_list_still_returns_200() -> None:
    """A-07: GET /api/demo/agents/research still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/agents/research")
    assert response.status_code == 200


def test_a08_research_for_lead_001_still_returns_200() -> None:
    """A-08: GET /api/demo/agents/research/lead_001 still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/agents/research/lead_001")
    assert response.status_code == 200
    assert response.json()["lead_id"] == "lead_001"


def test_a09_research_groq_returns_503_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A-09: GET /api/demo/agents/research-groq/lead_001 returns 503
    when no GROQ_API_KEY."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/demo/agents/research-groq/lead_001")
    assert response.status_code == 503


def test_a10_demo_simulation_still_returns_simulation_mode() -> None:
    """A-10: GET /api/demo/simulation still returns run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/simulation")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "simulation"


def test_a11_demo_run_still_returns_replay_mode() -> None:
    """A-11: GET /api/demo/run still returns run_mode == "replay"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/run")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "replay"


def test_a12_health_still_returns_200() -> None:
    """A-12: GET /health still returns 200."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
