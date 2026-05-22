"""Integration tests for the Phase 5.8 Email Drafter Agent endpoints
and regression checks for the pre-existing endpoints we must not break.

Test IDs map 1:1 to the Phase 5.8 spec (A-01 .. A-16).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

_LIST_URL = "/api/demo/agents/email-drafter"
_DETAIL_URL = "/api/demo/agents/email-drafter/{lead_id}"
_GROQ_URL = "/api/demo/agents/email-drafter-groq/{lead_id}"


def test_a01_get_email_drafter_list_returns_200() -> None:
    """A-01: GET /api/demo/agents/email-drafter returns 200."""

    with TestClient(app) as client:
        response = client.get(_LIST_URL)
    assert response.status_code == 200


def test_a02_email_drafter_list_is_non_empty() -> None:
    """A-02: response is a non-empty list."""

    with TestClient(app) as client:
        response = client.get(_LIST_URL)
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0


def test_a03_every_output_has_email_drafter_agent_name() -> None:
    """A-03: every output has agent_name == "email_drafter_agent"."""

    with TestClient(app) as client:
        response = client.get(_LIST_URL)
    body = response.json()
    for output in body:
        meta = output["result"]["metadata"]
        assert meta["agent_name"] == "email_drafter_agent"
        assert meta["simulated"] is True


def test_a04_get_email_drafter_for_known_lead_returns_200() -> None:
    """A-04: GET /api/demo/agents/email-drafter/lead_001 returns 200."""

    with TestClient(app) as client:
        response = client.get(_DETAIL_URL.format(lead_id="lead_001"))
    assert response.status_code == 200


def test_a05_email_drafter_for_lead_001_returns_matching_lead_id() -> None:
    """A-05: lead_001 response lead_id == "lead_001"."""

    with TestClient(app) as client:
        response = client.get(_DETAIL_URL.format(lead_id="lead_001"))
    assert response.json()["lead_id"] == "lead_001"


def test_a06_email_drafter_for_missing_lead_returns_404() -> None:
    """A-06: GET /api/demo/agents/email-drafter/missing_lead returns 404."""

    with TestClient(app) as client:
        response = client.get(_DETAIL_URL.format(lead_id="missing_lead"))
    assert response.status_code == 404


def test_a07_email_drafter_groq_returns_503_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A-07: GET /api/demo/agents/email-drafter-groq/lead_001 returns 503
    when no GROQ_API_KEY."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get(_GROQ_URL.format(lead_id="lead_001"))
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]


# --------------------------------------------------------------------------- #
# Regression / stability                                                      #
# --------------------------------------------------------------------------- #


def test_a08_research_list_still_returns_200() -> None:
    """A-08: GET /api/demo/agents/research still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/agents/research")
    assert response.status_code == 200


def test_a09_qualifier_list_still_returns_200() -> None:
    """A-09: GET /api/demo/agents/qualifier still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/agents/qualifier")
    assert response.status_code == 200


def test_a10_strategist_list_still_returns_200() -> None:
    """A-10: GET /api/demo/agents/strategist still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/agents/strategist")
    assert response.status_code == 200


def test_a11_research_groq_returns_503_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A-11: GET /api/demo/agents/research-groq/lead_001 returns 503
    when no GROQ_API_KEY."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/demo/agents/research-groq/lead_001")
    assert response.status_code == 503


def test_a12_qualifier_groq_returns_503_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A-12: GET /api/demo/agents/qualifier-groq/lead_001 returns 503
    when no GROQ_API_KEY."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/demo/agents/qualifier-groq/lead_001")
    assert response.status_code == 503


def test_a13_strategist_groq_returns_503_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A-13: GET /api/demo/agents/strategist-groq/lead_001 returns 503
    when no GROQ_API_KEY."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/demo/agents/strategist-groq/lead_001")
    assert response.status_code == 503


def test_a14_demo_simulation_still_returns_simulation() -> None:
    """A-14: GET /api/demo/simulation still returns run_mode == "simulation"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/simulation")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "simulation"


def test_a15_demo_run_still_returns_replay() -> None:
    """A-15: GET /api/demo/run still returns run_mode == "replay"."""

    with TestClient(app) as client:
        response = client.get("/api/demo/run")
    assert response.status_code == 200
    assert response.json()["run_mode"] == "replay"


def test_a16_health_still_returns_200() -> None:
    """A-16: GET /health still returns 200."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
