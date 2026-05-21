"""Unit tests for the Phase 4.4 replay run service.

Test numbers map 1:1 to the Phase 4.4 spec test list.
"""

from __future__ import annotations

from app.schemas.lead import LeadIn
from app.schemas.run import ReplayRunResponse
from app.services.run_service import build_replay_run


def _sample_leads() -> list[LeadIn]:
    """Hand-crafted, deterministic sample covering every code path."""

    return [
        # 1: complete row → high-fit, no warnings
        LeadIn(
            lead_id="lead_001",
            company_name="Acme Corp",
            website="acme.com",
            industry="SaaS",
            country="USA",
            employee_count=120,
            contact_name="Alice",
            contact_role="CTO",
        ),
        # 2: missing industry → counts as a warning row
        LeadIn(
            lead_id="lead_002",
            company_name="Globex",
            website="globex.com",
            industry=None,
            country="USA",
            contact_name="Bob",
            contact_role="CFO",
        ),
        # 3: missing website → also a warning row
        LeadIn(
            lead_id="lead_003",
            company_name="Initech",
            website=None,
            industry="Finance",
            country="CAN",
            contact_name=None,
            contact_role="CEO",
        ),
        # 4: missing company_name → failed
        LeadIn(
            lead_id="lead_004",
            company_name="",
            website="ghost.com",
            industry="SaaS",
            country="USA",
            contact_name="Dana",
            contact_role="Lead",
        ),
    ]


def test_01_build_replay_run_returns_replay_run_response() -> None:
    """01: build_replay_run() returns a ReplayRunResponse object."""

    response = build_replay_run(_sample_leads())
    assert isinstance(response, ReplayRunResponse)


def test_02_run_mode_is_exactly_replay() -> None:
    """02: run_mode is exactly "replay"."""

    response = build_replay_run(_sample_leads())
    assert response.run_mode == "replay"


def test_03_status_is_exactly_completed() -> None:
    """03: status is exactly "completed"."""

    response = build_replay_run(_sample_leads())
    assert response.status == "completed"


def test_04_data_source_is_exactly_demo() -> None:
    """04: data_source is exactly "demo"."""

    response = build_replay_run(_sample_leads())
    assert response.data_source == "demo"


def test_05_run_id_is_fixed_deterministic_value() -> None:
    """05: run_id is exactly "replay_demo_run_001"."""

    response_a = build_replay_run(_sample_leads())
    response_b = build_replay_run(_sample_leads())
    assert response_a.run_id == "replay_demo_run_001"
    assert response_b.run_id == "replay_demo_run_001"


def test_06_model_calls_is_zero() -> None:
    """06: model_calls is exactly 0."""

    response = build_replay_run(_sample_leads())
    assert response.model_calls == 0


def test_07_estimated_cost_is_zero_dollars() -> None:
    """07: estimated_cost is exactly "$0.00"."""

    response = build_replay_run(_sample_leads())
    assert response.estimated_cost == "$0.00"


def test_08_total_leads_equals_input_length() -> None:
    """08: total_leads equals len(input leads)."""

    leads = _sample_leads()
    response = build_replay_run(leads)
    assert response.total_leads == len(leads)


def test_09_valid_leads_counts_only_non_empty_company_names() -> None:
    """09: valid_leads counts only leads with non-empty company_name."""

    response = build_replay_run(_sample_leads())
    assert response.valid_leads == 3


def test_10_failed_leads_counts_missing_company_name() -> None:
    """10: failed_leads counts leads with missing company_name."""

    response = build_replay_run(_sample_leads())
    assert response.failed_leads == 1


def test_11_rows_with_warnings_counts_missing_industry_or_website() -> None:
    """11: rows_with_warnings counts leads missing industry or website."""

    response = build_replay_run(_sample_leads())
    # Sample has: 1 missing industry, 1 missing website, 1 missing both
    # company_name (but its industry+website are present), so the rows
    # with at least one of (industry, website) missing are: lead_002 and
    # lead_003 = 2.
    assert response.rows_with_warnings == 2


def test_12_industries_represented_is_sorted_and_excludes_none() -> None:
    """12: industries_represented is sorted and contains no None values."""

    response = build_replay_run(_sample_leads())
    industries = response.summary.industries_represented
    assert industries == sorted(industries)
    assert all(industry is not None for industry in industries)
    assert industries == ["Finance", "SaaS"]


def test_13_countries_represented_is_sorted_and_excludes_none() -> None:
    """13: countries_represented is sorted and contains no None values."""

    response = build_replay_run(_sample_leads())
    countries = response.summary.countries_represented
    assert countries == sorted(countries)
    assert all(country is not None for country in countries)
    assert countries == ["CAN", "USA"]


def test_14_include_leads_true_returns_non_empty_list() -> None:
    """14: include_leads=True → leads is a non-empty list."""

    response = build_replay_run(_sample_leads(), include_leads=True)
    assert isinstance(response.leads, list)
    assert len(response.leads) > 0


def test_15_include_leads_false_returns_none_for_leads() -> None:
    """15: include_leads=False → leads is None."""

    response = build_replay_run(_sample_leads(), include_leads=False)
    assert response.leads is None


def test_extra_leads_with_company_research_is_passed_through() -> None:
    """Sanity check: the route-supplied count is reflected in summary
    and ``leads_without_company_research`` is computed as the
    complement.
    """

    leads = _sample_leads()
    response = build_replay_run(leads, leads_with_company_research=2)
    assert response.summary.leads_with_company_research == 2
    assert response.summary.leads_without_company_research == len(leads) - 2


def test_extra_leads_with_contact_count_excludes_none() -> None:
    """Sanity check: ``leads_with_contact`` counts non-None contacts."""

    response = build_replay_run(_sample_leads())
    # lead_001 (Alice), lead_002 (Bob), lead_004 (Dana) have contact_name;
    # lead_003 does not.
    assert response.summary.leads_with_contact == 3
    assert response.summary.leads_without_contact == 1
