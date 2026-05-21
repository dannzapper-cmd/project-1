"""Tests for app.services.demo_data_loader (Fase 4.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.demo_data_loader import (
    DemoDataError,
    build_demo_summary,
    load_demo_company_research,
    load_demo_leads,
    validate_demo_dataset,
)


# --------------------------------------------------------------------------- #
# Happy paths against the real bundled demo files                             #
# --------------------------------------------------------------------------- #
def test_load_demo_leads_returns_expected_count_and_first_row() -> None:
    leads = load_demo_leads()

    assert len(leads) == 10
    first = leads[0]
    assert first.lead_id == "lead_001"
    assert first.company_name == "Veltrix Systems"
    assert first.industry == "B2B SaaS"
    assert first.employee_count == 140


def test_load_demo_company_research_returns_expected_count_and_shape() -> None:
    records = load_demo_company_research()

    assert len(records) == 10
    first = records[0]
    assert first.lead_id == "lead_001"
    assert first.company_name == "Veltrix Systems"
    assert first.research_status == "complete"
    assert first.opportunity_signals
    assert first.pain_hypotheses
    assert first.evidence_cards


def test_lead_ids_consistent_between_csv_and_json() -> None:
    leads = load_demo_leads()
    research = load_demo_company_research()
    validate_demo_dataset(leads, research)

    csv_ids = sorted(lead.lead_id for lead in leads)
    json_ids = sorted(rec.lead_id for rec in research)
    assert csv_ids == json_ids


def test_build_demo_summary_returns_expected_payload() -> None:
    summary = build_demo_summary()

    assert summary.total_leads == 10
    assert summary.total_research_records == 10
    assert summary.data_source == "synthetic_demo"
    assert summary.status == "ready"


# --------------------------------------------------------------------------- #
# Error paths                                                                 #
# --------------------------------------------------------------------------- #
def test_load_demo_leads_missing_file_raises_clear_error(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.csv"
    with pytest.raises(DemoDataError, match="not found"):
        load_demo_leads(missing)


def test_load_demo_company_research_missing_file_raises_clear_error(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(DemoDataError, match="not found"):
        load_demo_company_research(missing)


def test_load_demo_leads_missing_required_column_raises(tmp_path: Path) -> None:
    bad = tmp_path / "leads_bad.csv"
    bad.write_text(
        "lead_id,company_name,country\n" "lead_001,Acme Inc,United States\n",
        encoding="utf-8",
    )
    with pytest.raises(DemoDataError, match="missing required columns"):
        load_demo_leads(bad)


def test_load_demo_leads_missing_required_value_raises(tmp_path: Path) -> None:
    bad = tmp_path / "leads_bad_value.csv"
    bad.write_text(
        "lead_id,company_name,industry\n" ",Acme Inc,SaaS\n",
        encoding="utf-8",
    )
    with pytest.raises(DemoDataError, match="missing lead_id"):
        load_demo_leads(bad)


def test_load_demo_leads_missing_company_name_raises(tmp_path: Path) -> None:
    bad = tmp_path / "leads_bad_company.csv"
    bad.write_text(
        "lead_id,company_name,industry\n" "lead_001,,SaaS\n",
        encoding="utf-8",
    )
    with pytest.raises(DemoDataError, match="missing company_name"):
        load_demo_leads(bad)


def test_load_demo_leads_empty_industry_is_accepted_gracefully(
    tmp_path: Path,
) -> None:
    # The bundled demo dataset ships lead_010 with an intentionally empty
    # industry value (incomplete-data demo case). Empty optional values must
    # be handled gracefully per the Fase 4.2 spec, while the `industry`
    # COLUMN itself must still be present in the header.
    ok = tmp_path / "leads_empty_industry.csv"
    ok.write_text(
        "lead_id,company_name,industry\n" "lead_001,Acme Inc,\n",
        encoding="utf-8",
    )
    leads = load_demo_leads(ok)
    assert len(leads) == 1
    assert leads[0].lead_id == "lead_001"
    assert leads[0].industry is None


def test_load_demo_leads_duplicate_lead_id_raises(tmp_path: Path) -> None:
    bad = tmp_path / "leads_dup.csv"
    bad.write_text(
        "lead_id,company_name,industry\n"
        "lead_001,Acme Inc,SaaS\n"
        "lead_001,Beta Inc,Fintech\n",
        encoding="utf-8",
    )
    with pytest.raises(DemoDataError, match="duplicate lead_id"):
        load_demo_leads(bad)


def test_load_demo_leads_bad_employee_count_is_coerced_to_none_with_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """employee_count is OPTIONAL; non-integer garbage must not break
    loading but must be logged (not a silent failure)."""
    bad = tmp_path / "leads_emp.csv"
    bad.write_text(
        "lead_id,company_name,industry,employee_count\n"
        "lead_001,Acme Inc,SaaS,not-a-number\n",
        encoding="utf-8",
    )
    with caplog.at_level("WARNING"):
        leads = load_demo_leads(bad)

    assert len(leads) == 1
    assert leads[0].employee_count is None
    assert any(
        "employee_count" in record.message for record in caplog.records
    ), "non-integer employee_count should produce a WARNING log entry"


def test_load_demo_company_research_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "research_bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(DemoDataError, match="not valid JSON"):
        load_demo_company_research(bad)


def test_load_demo_company_research_wrong_top_level_type_raises(
    tmp_path: Path,
) -> None:
    bad = tmp_path / "research_dict.json"
    bad.write_text(
        json.dumps({"lead_001": {"company_name": "x", "research_status": "ok"}}),
        encoding="utf-8",
    )
    with pytest.raises(DemoDataError, match="top-level array"):
        load_demo_company_research(bad)


def test_load_demo_company_research_missing_required_field_raises(
    tmp_path: Path,
) -> None:
    bad = tmp_path / "research_missing.json"
    bad.write_text(
        json.dumps(
            [
                {
                    "lead_id": "lead_001",
                    "company_name": "Acme",
                    # research_status missing
                }
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(DemoDataError, match="missing required fields"):
        load_demo_company_research(bad)


def test_load_demo_company_research_duplicate_lead_id_raises(tmp_path: Path) -> None:
    bad = tmp_path / "research_dup.json"
    bad.write_text(
        json.dumps(
            [
                {
                    "lead_id": "lead_001",
                    "company_name": "Acme",
                    "research_status": "complete",
                },
                {
                    "lead_id": "lead_001",
                    "company_name": "Beta",
                    "research_status": "complete",
                },
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(DemoDataError, match="duplicate lead_id"):
        load_demo_company_research(bad)


def test_validate_demo_dataset_detects_mismatch(tmp_path: Path) -> None:
    csv_path = tmp_path / "leads.csv"
    csv_path.write_text(
        "lead_id,company_name,industry\n"
        "lead_001,Acme,SaaS\n"
        "lead_002,Beta,Fintech\n",
        encoding="utf-8",
    )
    json_path = tmp_path / "research.json"
    json_path.write_text(
        json.dumps(
            [
                {
                    "lead_id": "lead_001",
                    "company_name": "Acme",
                    "research_status": "complete",
                },
                {
                    "lead_id": "lead_003",
                    "company_name": "Gamma",
                    "research_status": "complete",
                },
            ]
        ),
        encoding="utf-8",
    )

    leads = load_demo_leads(csv_path)
    research = load_demo_company_research(json_path)

    with pytest.raises(DemoDataError, match="lead_id mismatch"):
        validate_demo_dataset(leads, research)
