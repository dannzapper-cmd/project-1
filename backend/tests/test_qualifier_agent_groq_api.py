"""Integration tests for the Phase 5.6B Groq-backed qualifier endpoint
and regression checks for every pre-existing endpoint we must not break.

No real Groq call is made. When ``GROQ_API_KEY`` is missing — which is
enforced by ``monkeypatch.delenv`` — the new endpoint must respond
with HTTP 503.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_GROQ_QUALIFIER_URL = "/api/demo/agents/qualifier-groq/{lead_id}"


def test_1_qualifier_groq_returns_503_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """1: GET /api/demo/agents/qualifier-groq/lead_001 returns 503 when
    GROQ_API_KEY is missing."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get(_GROQ_QUALIFIER_URL.format(lead_id="lead_001"))
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]


def test_2_existing_qualifier_endpoint_for_lead_still_returns_200() -> None:
    """2: GET /api/demo/agents/qualifier/lead_001 still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/agents/qualifier/lead_001")
    assert response.status_code == 200
    body = response.json()
    assert body["lead_id"] == "lead_001"
    assert body["result"]["metadata"]["agent_name"] == "qualifier_agent"


def test_3_existing_qualifier_list_still_returns_200() -> None:
    """3: GET /api/demo/agents/qualifier still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/agents/qualifier")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list) and len(body) > 0


def test_4_research_groq_returns_503_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """4: GET /api/demo/agents/research-groq/lead_001 returns 503 when
    GROQ_API_KEY is missing (Phase 5.5C behaviour unchanged)."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/demo/agents/research-groq/lead_001")
    assert response.status_code == 503


def test_5_groq_check_behaviour_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """5: GET /api/demo/model-service/groq-check still returns 503 when
    GROQ_API_KEY is missing."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/demo/model-service/groq-check")
    assert response.status_code == 503


def test_6_demo_simulation_still_returns_simulation() -> None:
    """6: GET /api/demo/simulation still returns run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/simulation")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "simulation"


def test_7_demo_run_still_returns_replay() -> None:
    """7: GET /api/demo/run still returns run_mode == "replay"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/run")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "replay"


def test_8_health_still_returns_200() -> None:
    """8: GET /health still returns 200."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
