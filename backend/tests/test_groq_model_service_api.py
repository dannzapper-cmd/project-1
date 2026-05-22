"""Integration tests for the Phase 5.5B Groq API surface and
regression checks for the pre-existing endpoints.

No real Groq call is made. The ``groq-check`` endpoint should respond
with HTTP 503 when ``GROQ_API_KEY`` is missing, which is the case in
the standard test environment (``monkeypatch.delenv`` enforces it).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_GROQ_CHECK_URL = "/api/demo/model-service/groq-check"
_MOCK_CHECK_URL = "/api/demo/model-service/mock-check"


def test_1_groq_check_returns_503_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """1: GET /api/demo/model-service/groq-check returns 503 when
    GROQ_API_KEY is missing."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get(_GROQ_CHECK_URL)
    assert response.status_code == 503
    body = response.json()
    assert "GROQ_API_KEY" in body["detail"]


def test_2_mock_check_still_returns_200(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """2: GET /api/demo/model-service/mock-check still returns 200."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get(_MOCK_CHECK_URL)
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"


def test_3_demo_run_still_returns_replay() -> None:
    """3: GET /api/demo/run still returns run_mode == "replay"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/run")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "replay"


def test_4_demo_simulation_still_returns_simulation() -> None:
    """4: GET /api/demo/simulation still returns run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/simulation")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "simulation"


def test_5_health_still_returns_200() -> None:
    """5: GET /health still returns 200."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
