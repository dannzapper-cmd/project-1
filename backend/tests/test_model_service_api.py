"""Integration tests for the Phase 5.4 ``GET /api/demo/model-service/mock-check``
endpoint plus regressions for pre-existing endpoints.

Test IDs map 1:1 to the Phase 5.4 spec (A-01 .. A-07).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

_MOCK_CHECK_URL = "/api/demo/model-service/mock-check"
_MOCK_MARKER = "[MOCK MODEL RESPONSE — no external model was called]"


def test_a01_get_mock_check_returns_200() -> None:
    """A-01: GET /api/demo/model-service/mock-check returns 200."""

    with TestClient(app) as client:
        response = client.get(_MOCK_CHECK_URL)
    assert response.status_code == 200


def test_a02_mock_check_response_provider_is_mock() -> None:
    """A-02: response provider == "mock"."""

    with TestClient(app) as client:
        response = client.get(_MOCK_CHECK_URL)
    assert response.json()["provider"] == "mock"


def test_a03_mock_check_response_is_simulated() -> None:
    """A-03: response simulated == True."""

    with TestClient(app) as client:
        response = client.get(_MOCK_CHECK_URL)
    assert response.json()["simulated"] is True


def test_a04_mock_check_content_contains_marker() -> None:
    """A-04: response content contains the mock marker."""

    with TestClient(app) as client:
        response = client.get(_MOCK_CHECK_URL)
    body = response.json()
    assert _MOCK_MARKER in body["content"]
    assert body["finish_reason"] == "mock_stop"


# --------------------------------------------------------------------------- #
# Regression / stability                                                      #
# --------------------------------------------------------------------------- #


def test_a05_demo_run_still_returns_replay_mode() -> None:
    """A-05: GET /api/demo/run still returns 200 and run_mode == "replay"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/run")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "replay"


def test_a06_demo_simulation_still_returns_simulation_mode() -> None:
    """A-06: GET /api/demo/simulation still returns 200 and
    run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/simulation")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "simulation"


def test_a07_health_still_returns_200() -> None:
    """A-07: GET /health still returns 200."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
