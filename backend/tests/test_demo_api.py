"""Tests for the /api/demo/* endpoints (Fase 4.2)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_still_works() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_demo_leads_returns_200_and_list_shape() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/leads")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 10
    first = payload[0]
    assert first["lead_id"] == "lead_001"
    assert first["company_name"] == "Veltrix Systems"
    assert first["industry"] == "B2B SaaS"


def test_get_demo_lead_by_id_returns_200_for_known_id() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/leads/lead_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["lead_id"] == "lead_001"
    assert payload["company_name"] == "Veltrix Systems"


def test_get_demo_lead_by_id_returns_404_for_unknown_id() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/leads/lead_999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_demo_company_research_returns_200_and_list_shape() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/company-research")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 10
    first = payload[0]
    assert first["lead_id"] == "lead_001"
    assert first["company_name"] == "Veltrix Systems"
    assert first["research_status"] == "complete"
    assert isinstance(first["opportunity_signals"], list)
    assert isinstance(first["pain_hypotheses"], list)
    assert isinstance(first["evidence_cards"], list)


def test_get_demo_company_research_by_id_returns_200_for_known_id() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/company-research/lead_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["lead_id"] == "lead_001"
    assert payload["research_status"] == "complete"


def test_get_demo_company_research_by_id_returns_404_for_unknown_id() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/company-research/lead_999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_demo_summary_returns_expected_shape() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "total_leads": 10,
        "total_research_records": 10,
        "data_source": "synthetic_demo",
        "status": "ready",
    }
