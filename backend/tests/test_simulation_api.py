"""Integration tests for the Phase 5.1 ``GET /api/demo/simulation`` endpoint
and stability of the pre-existing endpoints.

Test IDs map 1:1 to the Phase 5.1 spec (A-01 .. A-09).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

_SIMULATION_URL = "/api/demo/simulation"

_EXPECTED_KEYS = {
    "run_id",
    "run_mode",
    "status",
    "model_calls",
    "estimated_cost",
    "total_leads",
    "results",
}


def test_a01_get_simulation_returns_200() -> None:
    """A-01: GET /api/demo/simulation → 200."""

    with TestClient(app) as client:
        response = client.get(_SIMULATION_URL)
    assert response.status_code == 200


def test_a02_response_contains_required_keys() -> None:
    """A-02: response contains required keys."""

    with TestClient(app) as client:
        response = client.get(_SIMULATION_URL)
    body = response.json()
    missing = _EXPECTED_KEYS - set(body.keys())
    assert not missing, f"missing keys: {sorted(missing)}"


def test_a03_run_mode_is_simulation() -> None:
    """A-03: run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get(_SIMULATION_URL)
    assert response.json()["run_mode"] == "simulation"


def test_a04_model_calls_is_zero() -> None:
    """A-04: model_calls == 0."""

    with TestClient(app) as client:
        response = client.get(_SIMULATION_URL)
    assert response.json()["model_calls"] == 0


def test_a05_estimated_cost_is_zero_dollars() -> None:
    """A-05: estimated_cost == "$0.00"."""

    with TestClient(app) as client:
        response = client.get(_SIMULATION_URL)
    assert response.json()["estimated_cost"] == "$0.00"


def test_a06_results_is_non_empty_list() -> None:
    """A-06: results is a list with length > 0."""

    with TestClient(app) as client:
        response = client.get(_SIMULATION_URL)
    body = response.json()
    assert isinstance(body["results"], list)
    assert len(body["results"]) > 0


def test_a07_demo_run_still_returns_replay_mode() -> None:
    """A-07: GET /api/demo/run → 200 and run_mode == "replay" (unchanged)."""

    with TestClient(app) as client:
        response = client.get("/api/demo/run")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "replay"


def test_a08_demo_leads_still_returns_200() -> None:
    """A-08: GET /api/demo/leads → 200 (unchanged)."""

    with TestClient(app) as client:
        response = client.get("/api/demo/leads")
    assert response.status_code == 200


def test_a09_health_still_returns_200() -> None:
    """A-09: GET /health → 200 (unchanged)."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
