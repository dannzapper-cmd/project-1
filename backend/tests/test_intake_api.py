"""Integration tests for the Fase 4.3A intake endpoint and stability of
the pre-existing Fase 4.1 / 4.2 endpoints.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_13_post_intake_preview_records_json_returns_200_and_expected_keys() -> None:
    payload = {
        "input_type": "records_json",
        "source_name": "manual_paste",
        "records": [
            {
                "company_name": "Acme Corp",
                "industry": "SaaS",
                "website": "acme.com",
                "contact_role": "CTO",
            }
        ],
    }
    with TestClient(app) as client:
        response = client.post("/api/intake/preview", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "normalized_leads" in body
    assert "capabilities" in body


def test_14_get_demo_summary_still_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/summary")

    assert response.status_code == 200


def test_15_get_demo_leads_still_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/leads")

    assert response.status_code == 200


def test_16_get_health_still_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
