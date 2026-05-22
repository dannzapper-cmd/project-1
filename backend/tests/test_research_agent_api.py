"""Integration tests for the Phase 5.5A research-agent demo endpoints
and regression checks for the pre-existing demo / model-service / replay
/ simulation / health endpoints.

Test IDs map 1:1 to the Phase 5.5A spec (A-01 .. A-10).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

_LIST_URL = "/api/demo/agents/research"
_DETAIL_URL = "/api/demo/agents/research/{lead_id}"


def test_a01_get_research_list_returns_200() -> None:
    """A-01: GET /api/demo/agents/research returns 200."""

    with TestClient(app) as client:
        response = client.get(_LIST_URL)
    assert response.status_code == 200


def test_a02_research_list_is_non_empty() -> None:
    """A-02: response is a non-empty list."""

    with TestClient(app) as client:
        response = client.get(_LIST_URL)
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0


def test_a03_every_output_has_research_agent_name() -> None:
    """A-03: every output has result.metadata.agent_name == "research_agent"."""

    with TestClient(app) as client:
        response = client.get(_LIST_URL)
    body = response.json()
    for output in body:
        assert output["result"]["metadata"]["agent_name"] == "research_agent"
        assert output["result"]["metadata"]["simulated"] is True


def test_a04_get_research_for_known_lead_returns_200() -> None:
    """A-04: GET /api/demo/agents/research/lead_001 returns 200."""

    with TestClient(app) as client:
        response = client.get(_DETAIL_URL.format(lead_id="lead_001"))
    assert response.status_code == 200


def test_a05_research_for_lead_001_returns_matching_lead_id() -> None:
    """A-05: lead_001 response lead_id == "lead_001"."""

    with TestClient(app) as client:
        response = client.get(_DETAIL_URL.format(lead_id="lead_001"))
    body = response.json()
    assert body["lead_id"] == "lead_001"


def test_a06_research_for_missing_lead_returns_404() -> None:
    """A-06: GET /api/demo/agents/research/missing_lead returns 404."""

    with TestClient(app) as client:
        response = client.get(_DETAIL_URL.format(lead_id="missing_lead"))
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Regression / stability                                                      #
# --------------------------------------------------------------------------- #


def test_a07_model_service_mock_check_still_returns_200() -> None:
    """A-07: GET /api/demo/model-service/mock-check still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/model-service/mock-check")
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"


def test_a08_demo_simulation_still_returns_simulation_mode() -> None:
    """A-08: GET /api/demo/simulation still returns run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/simulation")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "simulation"


def test_a09_demo_run_still_returns_replay_mode() -> None:
    """A-09: GET /api/demo/run still returns run_mode == "replay"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/run")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "replay"


def test_a10_health_still_returns_200() -> None:
    """A-10: GET /health still returns 200."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
