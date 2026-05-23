"""Integration tests for Phase 6.1 — GET /api/demo/pipeline/{lead_id}."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


_DEMO_LEAD_ID = "lead_001"


def test_get_pipeline_known_lead_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get(f"/api/demo/pipeline/{_DEMO_LEAD_ID}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["lead_id"] == _DEMO_LEAD_ID
    assert isinstance(payload["run_id"], str)
    assert payload["run_id"].startswith(f"pipeline_{_DEMO_LEAD_ID}_")


def test_get_pipeline_unknown_lead_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/pipeline/lead_does_not_exist")

    assert response.status_code == 404
    payload = response.json()
    assert "lead_does_not_exist" in payload["detail"]


def test_get_pipeline_response_has_all_slots() -> None:
    with TestClient(app) as client:
        response = client.get(f"/api/demo/pipeline/{_DEMO_LEAD_ID}")

    assert response.status_code == 200
    payload = response.json()
    for slot in ("research", "qualification", "strategy", "email", "qa"):
        assert payload.get(slot) is not None, f"missing slot: {slot}"
    # Phase 6.1: intake is intentionally None (no Intake Agent runtime).
    assert payload.get("intake") is None


def test_get_pipeline_trace_length_is_five() -> None:
    with TestClient(app) as client:
        response = client.get(f"/api/demo/pipeline/{_DEMO_LEAD_ID}")

    assert response.status_code == 200
    trace = response.json()["trace"]
    assert isinstance(trace, list)
    assert len(trace) == 5
    agents = [entry["agent"] for entry in trace]
    assert agents == [
        "research_agent",
        "qualifier_agent",
        "strategist_agent",
        "email_drafter_agent",
        "qa_evaluator_agent",
    ]
    # Phase 6.1: every trace entry is flagged simulated=False on the
    # orchestration layer.
    for entry in trace:
        assert entry["simulated"] is False


def test_existing_agent_endpoints_still_work() -> None:
    # Regression coverage: a handful of pre-Phase-6.1 endpoints must
    # still respond 200 with the same broad shape they did before.
    with TestClient(app) as client:
        leads = client.get("/api/demo/leads")
        assert leads.status_code == 200
        assert isinstance(leads.json(), list)
        assert len(leads.json()) >= 1

        research = client.get(f"/api/demo/agents/research/{_DEMO_LEAD_ID}")
        assert research.status_code == 200
        assert research.json()["lead_id"] == _DEMO_LEAD_ID

        qualifier = client.get(f"/api/demo/agents/qualifier/{_DEMO_LEAD_ID}")
        assert qualifier.status_code == 200
        assert qualifier.json()["lead_id"] == _DEMO_LEAD_ID

        qa = client.get(f"/api/demo/agents/qa-evaluator/{_DEMO_LEAD_ID}")
        assert qa.status_code == 200
        assert qa.json()["lead_id"] == _DEMO_LEAD_ID
