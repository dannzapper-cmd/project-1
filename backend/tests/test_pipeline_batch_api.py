"""Integration tests for Phase 6.2 — GET /api/demo/pipeline/batch."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


_DEMO_LEAD_ID = "lead_001"


def test_get_batch_pipeline_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/pipeline/batch")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_mode"] == "deterministic_pipeline"
    assert payload["model_mode"] == "mock"


def test_get_batch_pipeline_response_has_run_id_and_summary() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/pipeline/batch")

    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload["run_id"], str)
    assert payload["run_id"].startswith("pipeline_batch_")

    summary = payload["summary"]
    for field in (
        "total_leads",
        "processed_leads",
        "high_priority_leads",
        "medium_priority_leads",
        "low_priority_leads",
        "average_qa_score",
    ):
        assert field in summary, f"summary missing field: {field}"
    # average_qa_score must be a float or null.
    average = summary["average_qa_score"]
    assert average is None or isinstance(average, (int, float))


def test_get_batch_pipeline_results_not_empty() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/pipeline/batch")

    assert response.status_code == 200
    payload = response.json()
    results = payload["results"]
    assert isinstance(results, list)
    assert len(results) >= 1
    assert payload["lead_count"] == len(results)
    # The shared run_id propagates to every per-lead container.
    for result in results:
        assert result["run_id"] == payload["run_id"]


def test_get_batch_pipeline_each_result_has_five_trace_entries() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/pipeline/batch")

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) >= 1
    for result in results:
        trace = result["trace"]
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
        # Every per-agent slot must still be populated.
        for slot in ("research", "qualification", "strategy", "email", "qa"):
            assert result.get(slot) is not None, f"missing slot: {slot}"
        assert result.get("intake") is None


def test_single_lead_pipeline_endpoint_still_returns_200() -> None:
    # Regression: the Phase 6.1 endpoint must keep working and must
    # not be shadowed by the new /pipeline/batch route.
    with TestClient(app) as client:
        response = client.get(f"/api/demo/pipeline/{_DEMO_LEAD_ID}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["lead_id"] == _DEMO_LEAD_ID
    assert payload["run_id"].startswith(f"pipeline_{_DEMO_LEAD_ID}_")
    assert len(payload["trace"]) == 5
