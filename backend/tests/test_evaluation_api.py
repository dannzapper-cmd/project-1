"""Integration tests for the Phase 5.3 trace & evaluation endpoints
and stability of the pre-existing replay / simulation / health endpoints.

Test IDs map 1:1 to the Phase 5.3 spec (A-01 .. A-13).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

_TRACE_RUN_URL = "/api/demo/simulation/trace"
_TRACE_LEAD_URL = "/api/demo/simulation/trace/{lead_id}"
_EVAL_RUN_URL = "/api/demo/simulation/evaluation"
_EVAL_LEAD_URL = "/api/demo/simulation/evaluation/{lead_id}"


# --------------------------------------------------------------------------- #
# Trace endpoints                                                             #
# --------------------------------------------------------------------------- #


def test_a01_get_simulation_trace_returns_200() -> None:
    """A-01: GET /api/demo/simulation/trace returns 200."""

    with TestClient(app) as client:
        response = client.get(_TRACE_RUN_URL)
    assert response.status_code == 200


def test_a02_trace_response_run_mode_is_simulation() -> None:
    """A-02: trace response run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get(_TRACE_RUN_URL)
    assert response.json()["run_mode"] == "simulation"


def test_a03_trace_response_leads_non_empty() -> None:
    """A-03: trace response leads is non-empty."""

    with TestClient(app) as client:
        response = client.get(_TRACE_RUN_URL)
    body = response.json()
    assert isinstance(body["leads"], list)
    assert len(body["leads"]) > 0


def test_a04_get_lead_trace_returns_200_for_known_lead() -> None:
    """A-04: GET /api/demo/simulation/trace/lead_001 returns 200."""

    with TestClient(app) as client:
        response = client.get(_TRACE_LEAD_URL.format(lead_id="lead_001"))
    assert response.status_code == 200
    body = response.json()
    assert body["lead_id"] == "lead_001"
    assert body["run_mode"] == "simulation"


def test_a05_get_lead_trace_returns_404_for_missing_lead() -> None:
    """A-05: GET /api/demo/simulation/trace/missing_lead returns 404."""

    with TestClient(app) as client:
        response = client.get(_TRACE_LEAD_URL.format(lead_id="missing_lead"))
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Evaluation endpoints                                                        #
# --------------------------------------------------------------------------- #


def test_a06_get_simulation_evaluation_returns_200() -> None:
    """A-06: GET /api/demo/simulation/evaluation returns 200."""

    with TestClient(app) as client:
        response = client.get(_EVAL_RUN_URL)
    assert response.status_code == 200


def test_a07_evaluation_response_run_mode_is_simulation() -> None:
    """A-07: evaluation response run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get(_EVAL_RUN_URL)
    assert response.json()["run_mode"] == "simulation"


def test_a08_evaluation_response_leads_non_empty() -> None:
    """A-08: evaluation response leads is non-empty."""

    with TestClient(app) as client:
        response = client.get(_EVAL_RUN_URL)
    body = response.json()
    assert isinstance(body["leads"], list)
    assert len(body["leads"]) > 0


def test_a09_get_lead_evaluation_returns_200_for_known_lead() -> None:
    """A-09: GET /api/demo/simulation/evaluation/lead_001 returns 200."""

    with TestClient(app) as client:
        response = client.get(_EVAL_LEAD_URL.format(lead_id="lead_001"))
    assert response.status_code == 200
    body = response.json()
    assert body["lead_id"] == "lead_001"


def test_a10_get_lead_evaluation_returns_404_for_missing_lead() -> None:
    """A-10: GET /api/demo/simulation/evaluation/missing_lead returns 404."""

    with TestClient(app) as client:
        response = client.get(_EVAL_LEAD_URL.format(lead_id="missing_lead"))
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Regression / stability                                                      #
# --------------------------------------------------------------------------- #


def test_a11_demo_run_still_returns_replay_mode() -> None:
    """A-11: GET /api/demo/run still returns 200 and run_mode == "replay"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/run")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "replay"


def test_a12_demo_simulation_still_returns_simulation_mode() -> None:
    """A-12: GET /api/demo/simulation still returns 200 and
    run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/simulation")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "simulation"


def test_a13_health_still_returns_200() -> None:
    """A-13: GET /health still returns 200."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
