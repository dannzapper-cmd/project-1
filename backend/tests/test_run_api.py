"""Integration tests for the Phase 4.4 replay run endpoint and
stability of the pre-existing endpoints.

Test numbers map 1:1 to the Phase 4.4 spec test list (16–28).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

_RUN_URL = "/api/demo/run"

_EXPECTED_TOP_LEVEL_KEYS = {
    "run_id",
    "run_mode",
    "status",
    "data_source",
    "source_name",
    "generated_at",
    "total_leads",
    "valid_leads",
    "failed_leads",
    "rows_with_warnings",
    "model_calls",
    "estimated_cost",
    "warnings",
    "summary",
    "leads",
}


def test_16_get_demo_run_returns_200() -> None:
    """16: GET /api/demo/run returns 200."""

    with TestClient(app) as client:
        response = client.get(_RUN_URL)
    assert response.status_code == 200


def test_17_response_contains_all_required_top_level_keys() -> None:
    """17: response contains every required top-level key."""

    with TestClient(app) as client:
        response = client.get(_RUN_URL)
    body = response.json()
    missing = _EXPECTED_TOP_LEVEL_KEYS - set(body.keys())
    assert not missing, f"missing keys: {sorted(missing)}"


def test_18_run_mode_is_replay() -> None:
    """18: run_mode is "replay"."""

    with TestClient(app) as client:
        response = client.get(_RUN_URL)
    assert response.json()["run_mode"] == "replay"


def test_19_status_is_completed() -> None:
    """19: status is "completed"."""

    with TestClient(app) as client:
        response = client.get(_RUN_URL)
    assert response.json()["status"] == "completed"


def test_20_model_calls_is_zero() -> None:
    """20: model_calls is 0."""

    with TestClient(app) as client:
        response = client.get(_RUN_URL)
    assert response.json()["model_calls"] == 0


def test_21_estimated_cost_is_zero_dollars() -> None:
    """21: estimated_cost is "$0.00"."""

    with TestClient(app) as client:
        response = client.get(_RUN_URL)
    assert response.json()["estimated_cost"] == "$0.00"


def test_22_leads_is_non_empty_list_when_include_leads_default() -> None:
    """22: leads is a non-empty list when include_leads is omitted."""

    with TestClient(app) as client:
        response = client.get(_RUN_URL)
    body = response.json()
    assert isinstance(body["leads"], list)
    assert len(body["leads"]) > 0


def test_23_include_leads_false_returns_null_leads() -> None:
    """23: GET /api/demo/run?include_leads=false returns leads as null."""

    with TestClient(app) as client:
        response = client.get(_RUN_URL, params={"include_leads": "false"})
    assert response.status_code == 200
    assert response.json()["leads"] is None


def test_24_total_leads_matches_demo_leads_endpoint() -> None:
    """24: total_leads matches len(GET /api/demo/leads)."""

    with TestClient(app) as client:
        run_response = client.get(_RUN_URL)
        leads_response = client.get("/api/demo/leads")

    assert run_response.status_code == 200
    assert leads_response.status_code == 200
    assert run_response.json()["total_leads"] == len(leads_response.json())


def test_25_demo_summary_still_returns_200() -> None:
    """25: existing GET /api/demo/summary still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/summary")
    assert response.status_code == 200


def test_26_demo_leads_still_returns_200() -> None:
    """26: existing GET /api/demo/leads still returns 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/leads")
    assert response.status_code == 200


def test_27_intake_preview_still_returns_200() -> None:
    """27: existing POST /api/intake/preview still returns 200."""

    payload = {
        "input_type": "records_json",
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


def test_28_health_still_returns_200() -> None:
    """28: existing GET /health still returns 200."""

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
