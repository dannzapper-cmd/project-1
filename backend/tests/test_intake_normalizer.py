"""Unit tests for the Fase 4.3A intake normalizer."""

from __future__ import annotations

from app.schemas.intake import IntakeOptions, IntakePreviewRequest
from app.services.intake_normalizer import build_intake_preview


def _preview(request: IntakePreviewRequest):
    return build_intake_preview(request)


def test_csv_text_standard_headers_maps_all_required_fields() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="csv_text",
            content=(
                "company_name,industry,website,contact_role\n"
                "Acme Inc,SaaS,https://acme.test,VP Sales"
            ),
        )
    )

    row = response.normalized_leads[0]
    assert response.mapped_columns == {
        "company_name": "company_name",
        "industry": "industry",
        "website": "website",
        "contact_role": "contact_role",
    }
    assert row.lead is not None
    assert row.lead.company_name == "Acme Inc"
    assert row.lead.industry == "SaaS"
    assert row.lead.website == "https://acme.test"
    assert row.lead.contact_role == "VP Sales"


def test_csv_text_alias_headers_map_to_lead_fields() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="csv_text",
            content=(
                "Company Name,Sector,URL,Title\n"
                "Globex,Manufacturing,globex.test,COO"
            ),
        )
    )

    assert response.mapped_columns == {
        "Company Name": "company_name",
        "Sector": "industry",
        "URL": "website",
        "Title": "contact_role",
    }
    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.company_name == "Globex"
    assert row.lead.industry == "Manufacturing"
    assert row.lead.website == "globex.test"
    assert row.lead.contact_role == "COO"


def test_pasted_table_tab_separated_input_maps_correctly() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="pasted_table",
            content="Company Name\tSector\tURL\tTitle\nInitech\tSaaS\tinitech.test\tCTO",
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.company_name == "Initech"
    assert row.lead.industry == "SaaS"
    assert row.lead.website == "initech.test"
    assert row.lead.contact_role == "CTO"


def test_records_json_list_of_dicts_maps_correctly() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="records_json",
            records=[
                {
                    "company": "Umbrella",
                    "industry": "Biotech",
                    "website": "umbrella.test",
                    "role": "Head of Ops",
                }
            ],
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.company_name == "Umbrella"
    assert row.lead.industry == "Biotech"
    assert row.lead.website == "umbrella.test"
    assert row.lead.contact_role == "Head of Ops"


def test_raw_text_with_all_labels_present_maps_correctly() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="raw_text",
            content=(
                "Company: Hooli\n"
                "Website: hooli.test\n"
                "Industry: SaaS\n"
                "Country: US\n"
                "Employees: 1,400\n"
                "Contact: Jane Doe\n"
                "Role: VP Marketing\n"
                "Notes: Expansion signal\n"
                "Lead ID: lead_123"
            ),
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.company_name == "Hooli"
    assert row.lead.website == "hooli.test"
    assert row.lead.industry == "SaaS"
    assert row.lead.country == "US"
    assert row.lead.employee_count == 1400
    assert row.lead.contact_name == "Jane Doe"
    assert row.lead.contact_role == "VP Marketing"
    assert row.lead.notes == "Expansion signal"
    assert row.lead.lead_id == "lead_123"


def test_raw_text_without_company_line_returns_failed_row() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="raw_text",
            content="Website: missing-company.test\nIndustry: SaaS",
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is None
    assert row.confidence is None
    assert any(issue.code == "missing_company_name" for issue in row.issues)


def test_row_missing_company_name_produces_error_and_no_confidence() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="records_json",
            records=[{"industry": "SaaS", "website": "missing.test"}],
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is None
    assert row.confidence is None
    assert any(
        issue.severity == "error" and issue.code == "missing_company_name"
        for issue in row.issues
    )


def test_row_missing_industry_warns_without_failing() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="records_json",
            records=[
                {
                    "company_name": "No Industry Co",
                    "website": "no-industry.test",
                    "contact_role": "CEO",
                }
            ],
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert any(
        issue.severity == "warning" and issue.code == "missing_industry"
        for issue in row.issues
    )


def test_employee_count_with_comma_parses_to_integer() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="records_json",
            records=[
                {
                    "company_name": "Count Co",
                    "industry": "SaaS",
                    "website": "count.test",
                    "contact_role": "CEO",
                    "employee_count": "1,400",
                }
            ],
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.employee_count == 1400


def test_invalid_employee_count_warns_and_sets_none() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="records_json",
            records=[
                {
                    "company_name": "Bad Count Co",
                    "industry": "SaaS",
                    "website": "bad-count.test",
                    "contact_role": "CEO",
                    "employee_count": "abc",
                }
            ],
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.employee_count is None
    assert any(
        issue.severity == "warning" and issue.code == "invalid_employee_count"
        for issue in row.issues
    )


def test_missing_lead_id_generates_preview_id_and_info_issue() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="records_json",
            records=[
                {
                    "company_name": "Generated ID Co",
                    "industry": "SaaS",
                    "website": "generated.test",
                    "contact_role": "CEO",
                }
            ],
            options=IntakeOptions(generate_missing_lead_ids=True),
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.lead_id == "preview_001"
    assert any(issue.severity == "info" and issue.code == "generated_lead_id" for issue in row.issues)


def test_unknown_column_budget_appears_in_unmapped_columns() -> None:
    response = _preview(
        IntakePreviewRequest(
            input_type="records_json",
            records=[
                {
                    "company_name": "Budget Co",
                    "industry": "SaaS",
                    "website": "budget.test",
                    "contact_role": "CEO",
                    "Budget": "$50k",
                }
            ],
        )
    )

    assert "Budget" in response.unmapped_columns
    assert any(
        issue.code == "unmapped_column" and issue.field == "Budget"
        for issue in response.global_issues
    )
