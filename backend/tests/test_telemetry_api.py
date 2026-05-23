"""Integration tests for read-only telemetry API endpoints."""

from __future__ import annotations

import os
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.telemetry_service import clear_telemetry

_DEMO_LEAD_ID = "lead_001"


@pytest.fixture(autouse=True)
def _clear_telemetry() -> Iterator[None]:
    clear_telemetry()
    try:
        yield
    finally:
        clear_telemetry()


def test_get_telemetry_runs_empty_state_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/telemetry/runs")

    assert response.status_code == 200
    assert response.json() == []


def test_get_telemetry_runs_does_not_require_groq_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with TestClient(app) as client:
        response = client.get("/api/demo/telemetry/runs")

    assert "GROQ_API_KEY" not in os.environ
    assert response.status_code == 200


def test_get_telemetry_run_detail_after_pipeline_run_returns_200() -> None:
    with TestClient(app) as client:
        pipeline = client.get(f"/api/demo/pipeline/{_DEMO_LEAD_ID}")
        run_id = pipeline.json()["run_id"]
        response = client.get(f"/api/demo/telemetry/runs/{run_id}")

    assert pipeline.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["summary"]["agent_step_count"] == 5
    assert len(payload["entries"]) == 5
    assert [entry["agent_name"] for entry in payload["entries"]] == [
        "research_agent",
        "qualifier_agent",
        "strategist_agent",
        "email_drafter_agent",
        "qa_evaluator_agent",
    ]


def test_get_unknown_telemetry_run_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/telemetry/runs/run_does_not_exist")

    assert response.status_code == 404
    assert "run_does_not_exist" in response.json()["detail"]


def test_telemetry_api_payload_does_not_expose_prompt_or_email_body() -> None:
    with TestClient(app) as client:
        pipeline = client.get(f"/api/demo/pipeline/{_DEMO_LEAD_ID}")
        run_id = pipeline.json()["run_id"]
        response = client.get(f"/api/demo/telemetry/runs/{run_id}")

    assert response.status_code == 200
    forbidden = {
        "prompt",
        "prompt_body",
        "raw_input",
        "input",
        "email_body",
        "generated_email_body",
        "api_key",
        "secret",
    }
    for entry in response.json()["entries"]:
        assert set(entry.keys()).isdisjoint(forbidden)
