"""Integration tests for the Phase 5.5C Groq-backed research endpoint
and regression checks for every pre-existing endpoint we must not break.

No real Groq call is made. When ``GROQ_API_KEY`` is missing — which is
enforced by ``monkeypatch.delenv`` in test 1 — the new endpoint must
respond with HTTP 503.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_GROQ_RESEARCH_URL = "/api/demo/agents/research-groq/{lead_id}"


def test_1_groq_research_returns_503_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """1: GET /api/demo/agents/research-groq/lead_001 returns 503 when
    GROQ_API_KEY is missing."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get(_GROQ_RESEARCH_URL.format(lead_id="lead_001"))
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]


def test_2_existing_research_endpoint_still_returns_200() -> None:
    """2: GET /api/demo/agents/research/lead_001 still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/agents/research/lead_001")
    assert response.status_code == 200
    body = response.json()
    assert body["lead_id"] == "lead_001"
    assert body["result"]["metadata"]["agent_name"] == "research_agent"


def test_3_existing_research_list_still_returns_200() -> None:
    """3: GET /api/demo/agents/research still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/agents/research")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list) and len(body) > 0


def test_4_groq_check_behaviour_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """4: GET /api/demo/model-service/groq-check still returns 503 when
    GROQ_API_KEY is missing (behavior from Phase 5.5B unchanged)."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/demo/model-service/groq-check")
    assert response.status_code == 503


def test_5_demo_simulation_still_returns_simulation() -> None:
    """5: GET /api/demo/simulation still returns run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/simulation")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "simulation"


def test_6_demo_run_still_returns_replay() -> None:
    """6: GET /api/demo/run still returns run_mode == "replay"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/run")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "replay"


def test_7_health_still_returns_200() -> None:
    """7: GET /health still returns 200."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
