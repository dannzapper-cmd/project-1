"""Integration tests for the Fase 4.3A intake endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_post_intake_preview_records_json_returns_expected_keys() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/intake/preview",
            json={
                "input_type": "records_json",
                "records": [
                    {
                        "company_name": "API Co",
                        "industry": "SaaS",
                        "website": "api.test",
                        "contact_role": "CEO",
                    }
                ],
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "normalized_leads" in payload
    assert "capabilities" in payload


def test_get_demo_summary_still_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/summary")

    assert response.status_code == 200


def test_get_demo_leads_still_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/leads")

    assert response.status_code == 200


def test_get_health_still_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
