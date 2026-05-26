"""Unit tests for the Fase 4.3A intake normalizer service.

Test numbering aligns with the implementation spec for Fase 4.3A.
"""

from __future__ import annotations

from app.schemas.intake import IntakeOptions, IntakePreviewRequest
from app.services.intake_normalizer import build_preview


def _issues_with_code(row, code: str) -> list:
    return [issue for issue in row.issues if issue.code == code]


def test_01_csv_text_standard_headers_maps_all_four_fields() -> None:
    """Test 1: csv_text with standard headers maps all 4 fields correctly."""

    content = (
        "company_name,industry,website,contact_role\n"
        "Acme Corp,SaaS,acme.com,CTO\n"
    )
    response = build_preview(
        IntakePreviewRequest(input_type="csv_text", content=content)
    )

    assert response.mapped_columns == {
        "company_name": "company_name",
        "industry": "industry",
        "website": "website",
        "contact_role": "contact_role",
    }
    assert response.unmapped_columns == []
    assert response.total_rows == 1
    assert response.valid_rows == 1
    assert response.failed_rows == 0
    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.company_name == "Acme Corp"
    assert row.lead.industry == "SaaS"
    assert row.lead.website == "acme.com"
    assert row.lead.contact_role == "CTO"


def test_02_csv_text_alias_headers_map_to_lead_in_fields() -> None:
    """Test 2: csv_text with alias headers maps to canonical fields."""

    content = (
        "Company Name,Sector,URL,Title\n"
        "Acme Corp,SaaS,acme.com,CTO\n"
    )
    response = build_preview(
        IntakePreviewRequest(input_type="csv_text", content=content)
    )

    assert response.mapped_columns == {
        "Company Name": "company_name",
        "Sector": "industry",
        "URL": "website",
        "Title": "contact_role",
    }
    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.company_name == "Acme Corp"
    assert row.lead.industry == "SaaS"
    assert row.lead.website == "acme.com"
    assert row.lead.contact_role == "CTO"


def test_03_pasted_table_tab_separated_maps_correctly() -> None:
    """Test 3: pasted_table tab-separated input maps correctly."""

    content = (
        "company_name\tindustry\twebsite\tcontact_role\n"
        "Acme Corp\tSaaS\tacme.com\tCTO\n"
    )
    response = build_preview(
        IntakePreviewRequest(input_type="pasted_table", content=content)
    )

    assert response.mapped_columns == {
        "company_name": "company_name",
        "industry": "industry",
        "website": "website",
        "contact_role": "contact_role",
    }
    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.company_name == "Acme Corp"


def test_04_records_json_list_of_dicts_maps_correctly() -> None:
    """Test 4: records_json list of dicts maps correctly."""

    records = [
        {
            "company_name": "Acme Corp",
            "industry": "SaaS",
            "website": "acme.com",
            "contact_role": "CTO",
        }
    ]
    response = build_preview(
        IntakePreviewRequest(input_type="records_json", records=records)
    )

    assert response.total_rows == 1
    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.company_name == "Acme Corp"
    assert row.lead.industry == "SaaS"
    assert row.lead.website == "acme.com"
    assert row.lead.contact_role == "CTO"


def test_05_raw_text_with_all_labels_maps_correctly() -> None:
    """Test 5: raw_text with all labels present maps correctly."""

    content = (
        "Company: Acme Corp\n"
        "Website: acme.com\n"
        "Industry: SaaS\n"
        "Country: USA\n"
        "Employees: 1200\n"
        "Contact: Jane Doe\n"
        "Role: CTO\n"
        "Notes: Strong fit\n"
        "Lead_id: ext_42\n"
    )
    response = build_preview(
        IntakePreviewRequest(input_type="raw_text", content=content)
    )

    assert response.total_rows == 1
    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.company_name == "Acme Corp"
    assert row.lead.website == "acme.com"
    assert row.lead.industry == "SaaS"
    assert row.lead.country == "USA"
    assert row.lead.employee_count == 1200
    assert row.lead.contact_name == "Jane Doe"
    assert row.lead.contact_role == "CTO"
    assert row.lead.notes == "Strong fit"
    assert row.lead.lead_id == "ext_42"


def test_06_raw_text_without_company_line_returns_failed_row() -> None:
    """Test 6: raw_text without any "Company:" line → failed row."""

    content = (
        "Website: acme.com\n"
        "Industry: SaaS\n"
    )
    response = build_preview(
        IntakePreviewRequest(input_type="raw_text", content=content)
    )

    assert response.total_rows == 1
    assert response.failed_rows == 1
    row = response.normalized_leads[0]
    assert row.lead is None
    assert row.confidence is None
    assert any(issue.code == "missing_company_name" for issue in row.issues)


def test_07_row_missing_company_name_produces_error_issue_and_none_confidence() -> None:
    """Test 7: missing company_name → error code=missing_company_name, confidence=None."""

    records = [{"industry": "SaaS", "website": "acme.com"}]
    response = build_preview(
        IntakePreviewRequest(input_type="records_json", records=records)
    )

    row = response.normalized_leads[0]
    assert row.lead is None
    assert row.confidence is None
    missing = _issues_with_code(row, "missing_company_name")
    assert len(missing) == 1
    assert missing[0].severity == "error"


def test_08_row_missing_industry_is_required_field_error() -> None:
    """Test 8: missing industry -> error and invalid row."""

    records = [{"company_name": "Acme Corp", "website": "acme.com"}]
    response = build_preview(
        IntakePreviewRequest(input_type="records_json", records=records)
    )

    row = response.normalized_leads[0]
    assert row.lead is None
    assert row.status == "invalid"
    errors = _issues_with_code(row, "missing_industry")
    assert len(errors) == 1
    assert errors[0].severity == "error"
    assert row.missing_required_fields == ["industry"]
    assert response.failed_rows == 1


def test_09_employee_count_with_comma_parses_to_int() -> None:
    """Test 9: employee_count "1,400" parses to 1400."""

    records = [
        {
            "company_name": "Acme Corp",
            "industry": "SaaS",
            "website": "acme.com",
            "employee_count": "1,400",
        }
    ]
    response = build_preview(
        IntakePreviewRequest(input_type="records_json", records=records)
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.employee_count == 1400
    assert _issues_with_code(row, "invalid_employee_count") == []


def test_10_employee_count_non_numeric_produces_warning_and_none() -> None:
    """Test 10: employee_count "abc" → warning + employee_count=None."""

    records = [
        {
            "company_name": "Acme Corp",
            "industry": "SaaS",
            "website": "acme.com",
            "employee_count": "abc",
        }
    ]
    response = build_preview(
        IntakePreviewRequest(input_type="records_json", records=records)
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.employee_count is None
    warnings = _issues_with_code(row, "invalid_employee_count")
    assert len(warnings) == 1
    assert warnings[0].severity == "warning"


def test_11_missing_lead_id_generates_preview_001() -> None:
    """Test 11: missing lead_id + generate=True → preview_001 + info issue."""

    records = [
        {
            "company_name": "Acme Corp",
            "industry": "SaaS",
            "website": "acme.com",
        }
    ]
    response = build_preview(
        IntakePreviewRequest(
            input_type="records_json",
            records=records,
            options=IntakeOptions(generate_missing_lead_ids=True),
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.lead_id == "preview_001"
    info_issues = _issues_with_code(row, "generated_lead_id")
    assert len(info_issues) == 1
    assert info_issues[0].severity == "info"


def test_11b_missing_lead_id_with_generate_false_uses_empty_string() -> None:
    """Documents the Fase 4.3A compatibility behavior.

    ``LeadIn.lead_id`` is a required ``str`` (we are explicitly forbidden
    from modifying ``backend/app/schemas/lead.py`` in this phase). The
    spec states that when ``generate_missing_lead_ids=False`` and the
    lead has no id, the row must still be produced and must not error on
    that alone. The current implementation therefore surfaces the
    "missing id" as the empty string, keeping ``LeadIn`` valid. No
    ``generated_lead_id`` info issue is emitted in this case.
    """

    records = [
        {
            "company_name": "Acme Corp",
            "industry": "SaaS",
            "website": "acme.com",
        }
    ]
    response = build_preview(
        IntakePreviewRequest(
            input_type="records_json",
            records=records,
            options=IntakeOptions(generate_missing_lead_ids=False),
        )
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.lead_id == ""
    assert _issues_with_code(row, "generated_lead_id") == []
    assert _issues_with_code(row, "missing_company_name") == []
    assert response.failed_rows == 0


def test_12_unknown_column_appears_in_unmapped_columns() -> None:
    """Test 12: unknown column "Budget" appears in unmapped_columns."""

    content = (
        "company_name,industry,Budget\n"
        "Acme Corp,SaaS,50000\n"
    )
    response = build_preview(
        IntakePreviewRequest(input_type="csv_text", content=content)
    )

    assert "Budget" in response.unmapped_columns
    assert any(
        issue.code == "unmapped_column" and issue.field == "Budget"
        for issue in response.global_issues
    )


def test_missing_recommended_and_optional_fields_are_warnings() -> None:
    content = "company_name,industry\nAcme Corp,B2B SaaS\n"

    response = build_preview(
        IntakePreviewRequest(input_type="csv_text", content=content)
    )

    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.status == "warning"
    assert row.low_confidence_fields == [
        "website",
        "country",
        "employee_count",
        "contact_role",
        "notes",
    ]
    codes = {issue.code for issue in row.issues}
    assert "missing_website" in codes
    assert "missing_country" in codes
    assert "missing_employee_count" in codes
    assert "missing_contact_role" in codes
    assert "missing_notes" in codes


def test_blank_rows_are_ignored() -> None:
    content = "company_name,industry\n\nAcme Corp,SaaS\n   \n"

    response = build_preview(
        IntakePreviewRequest(input_type="csv_text", content=content)
    )

    assert response.total_rows == 1
    assert response.valid_rows == 1


def test_malformed_short_row_surfaces_missing_required_field() -> None:
    content = "company_name,industry,website\nAcme Corp\n"

    response = build_preview(
        IntakePreviewRequest(input_type="csv_text", content=content)
    )

    row = response.normalized_leads[0]
    assert row.status == "invalid"
    assert row.lead is None
    assert row.normalized_fields["company_name"] == "Acme Corp"
    assert "industry" in row.missing_required_fields


def test_mixed_valid_and_invalid_rows_keeps_valid_rows_processable() -> None:
    content = (
        "company_name,industry,website\n"
        "ValidCo,SaaS,valid.example\n"
        "NoIndustry,,missing.example\n"
        ",SaaS,missing-company.example\n"
    )

    response = build_preview(
        IntakePreviewRequest(input_type="csv_text", content=content)
    )

    assert response.total_rows == 3
    assert response.valid_rows == 1
    assert response.failed_rows == 2
    assert response.normalized_leads[0].lead is not None
    assert response.normalized_leads[1].lead is None
    assert response.normalized_leads[2].lead is None


def test_preview_exposes_max_leads_per_run() -> None:
    rows = ["company_name,industry"]
    rows.extend(f"Company {idx},SaaS" for idx in range(12))

    response = build_preview(
        IntakePreviewRequest(input_type="csv_text", content="\n".join(rows))
    )

    assert response.total_rows == 12
    assert response.max_leads_per_run == 10


def test_pasted_comma_separated_text_with_aliases_maps_expected_fields() -> None:
    content = "account,vertical,site,market,name,contact role\nAcme,SaaS,acme.example,US,Ada,VP Sales\n"

    response = build_preview(
        IntakePreviewRequest(input_type="pasted_table", content=content)
    )

    assert response.mapped_columns["account"] == "company_name"
    assert response.mapped_columns["vertical"] == "industry"
    assert response.mapped_columns["site"] == "website"
    assert response.mapped_columns["name"] == "contact_name"
    row = response.normalized_leads[0]
    assert row.lead is not None
    assert row.lead.contact_name == "Ada"
