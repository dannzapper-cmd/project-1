# Future adapters (NOT implemented in this phase):
# - csv_file: read file bytes, decode to string, then use csv_text parser
# - excel_file: use openpyxl to extract sheet as list of dicts (no pandas)
# - pdf_file: use pdfplumber or pypdf to extract text, then apply raw_text parser
# - image_file / screenshot: use multimodal API (Gemini/GPT-4V) or OCR (Tesseract)
# - scanned_document: same as image_file
# All future adapters should normalize to list[dict] and then call the
# shared column_mapping + normalization pipeline already implemented here.

"""Preview-only lead intake parsing and normalization."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from io import StringIO
from typing import Any

from app.schemas.intake import (
    CapabilityMap,
    IntakeIssue,
    IntakeOptions,
    IntakePreviewRequest,
    IntakePreviewResponse,
    NormalizedLeadRow,
)
from app.schemas.lead import LeadIn


LEAD_FIELDS = (
    "lead_id",
    "company_name",
    "website",
    "industry",
    "country",
    "employee_count",
    "contact_name",
    "contact_role",
    "notes",
)

ALIAS_GROUPS: dict[str, tuple[str, ...]] = {
    "company_name": (
        "company",
        "company_name",
        "organization",
        "account",
        "account_name",
        "company name",
        "account name",
    ),
    "website": ("website", "url", "domain", "website_url", "web"),
    "industry": ("industry", "sector", "vertical", "category"),
    "country": ("country", "location", "market", "geography"),
    "employee_count": (
        "employee_count",
        "employees",
        "headcount",
        "company_size",
        "size",
        "num_employees",
        "number_of_employees",
    ),
    "contact_name": (
        "contact",
        "contact_name",
        "full_name",
        "prospect",
        "lead_name",
        "contact name",
        "full name",
        "lead name",
    ),
    "contact_role": (
        "role",
        "title",
        "job_title",
        "contact_role",
        "position",
        "job title",
    ),
    "notes": ("notes", "note", "context", "description", "comments"),
    "lead_id": ("lead_id", "id", "lead_id", "lead id"),
}

ISSUE_MESSAGES: dict[str, str] = {
    "missing_company_name": "Row has no company_name.",
    "missing_industry": "Row has no industry.",
    "missing_website": "Row has no website.",
    "missing_contact_role": "Row has no contact_role.",
    "generated_lead_id": "lead_id was generated for preview only.",
    "invalid_employee_count": "employee_count could not be parsed as integer.",
    "unmapped_column": "Column could not be mapped to a LeadIn field.",
    "unsupported_input_type": "input_type is not implemented.",
}

RAW_TEXT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("company_name", r"(?i)^company\s*:\s*(.+)"),
    ("website", r"(?i)^website\s*:\s*(.+)"),
    ("industry", r"(?i)^industry\s*:\s*(.+)"),
    ("country", r"(?i)^country\s*:\s*(.+)"),
    ("employee_count", r"(?i)^employees?\s*:\s*(.+)"),
    ("contact_name", r"(?i)^contact\s*:\s*(.+)"),
    ("contact_role", r"(?i)^role\s*:\s*(.+)"),
    ("notes", r"(?i)^notes?\s*:\s*(.+)"),
    ("lead_id", r"(?i)^(?:lead_?id|id)\s*:\s*(.+)"),
)


@dataclass(frozen=True)
class ParsedInput:
    columns: list[str]
    records: list[dict[str, Any]]


@dataclass(frozen=True)
class ColumnMapping:
    mapped_columns: dict[str, str]
    unmapped_columns: list[str]
    field_by_column: dict[str, str]
    global_issues: list[IntakeIssue]


def build_intake_preview(request: IntakePreviewRequest) -> IntakePreviewResponse:
    """Build a preview response without side effects."""

    options = request.options or IntakeOptions()

    if request.input_type == "csv_text":
        parsed = _parse_delimited_text(
            request.content or "",
            options=options,
            auto_delimiters=(",", "\t"),
        )
    elif request.input_type == "pasted_table":
        parsed = _parse_delimited_text(
            request.content or "",
            options=options,
            auto_delimiters=("\t", ","),
        )
    elif request.input_type == "records_json":
        parsed = _parse_records_json(request.records or [])
    elif request.input_type == "raw_text":
        parsed = _parse_raw_text(request.content or "")
    else:
        return _unsupported_input_type_response(request)

    return _normalize_parsed_input(
        request=request,
        parsed=parsed,
        options=options,
    )


def _parse_delimited_text(
    content: str,
    *,
    options: IntakeOptions,
    auto_delimiters: tuple[str, str],
) -> ParsedInput:
    if options.delimiter == "auto":
        first = _read_csv_content(content, delimiter=auto_delimiters[0])
        if len(first.columns) >= 2:
            return first
        return _read_csv_content(content, delimiter=auto_delimiters[1])

    return _read_csv_content(content, delimiter=options.delimiter)


def _read_csv_content(content: str, *, delimiter: str) -> ParsedInput:
    reader = csv.reader(StringIO(content), delimiter=delimiter)
    rows = list(reader)

    if not rows:
        return ParsedInput(columns=[], records=[])

    headers = rows[0]
    records: list[dict[str, Any]] = []
    for row in rows[1:]:
        record = {
            header: row[index] if index < len(row) else None
            for index, header in enumerate(headers)
        }
        records.append(record)

    return ParsedInput(columns=headers, records=records)


def _parse_records_json(records: list[dict[str, Any]]) -> ParsedInput:
    columns: list[str] = []
    for record in records:
        for column in record:
            if column not in columns:
                columns.append(column)
    return ParsedInput(columns=columns, records=records)


def _parse_raw_text(content: str) -> ParsedInput:
    blocks = _split_raw_text_blocks(content)
    records: list[dict[str, Any]] = []
    columns: list[str] = []

    for block in blocks:
        record: dict[str, Any] = {}
        for line in block:
            for field_name, pattern in RAW_TEXT_PATTERNS:
                match = re.match(pattern, line)
                if match:
                    record[field_name] = match.group(1)
                    if field_name not in columns:
                        columns.append(field_name)
                    break
        records.append(record)

    return ParsedInput(columns=columns, records=records)


def _split_raw_text_blocks(content: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current_block: list[str] = []

    for line in content.splitlines():
        if line.strip() == "":
            if current_block:
                blocks.append(current_block)
                current_block = []
            continue
        current_block.append(line)

    if current_block:
        blocks.append(current_block)

    return blocks


def _normalize_parsed_input(
    *,
    request: IntakePreviewRequest,
    parsed: ParsedInput,
    options: IntakeOptions,
) -> IntakePreviewResponse:
    column_mapping = _map_columns(parsed.columns)
    normalized_leads: list[NormalizedLeadRow] = []
    generated_lead_id_count = 0

    for row_number, record in enumerate(parsed.records, start=1):
        normalized_row, generated = _normalize_record(
            record=record,
            row_number=row_number,
            column_mapping=column_mapping,
            options=options,
            generated_lead_id_count=generated_lead_id_count,
        )
        if generated:
            generated_lead_id_count += 1
        normalized_leads.append(normalized_row)

    valid_rows = sum(1 for row in normalized_leads if row.lead is not None)
    failed_rows = sum(1 for row in normalized_leads if row.lead is None)
    rows_with_warnings = sum(
        1
        for row in normalized_leads
        if any(issue.severity == "warning" for issue in row.issues)
    )

    return IntakePreviewResponse(
        status=_preview_status(valid_rows, failed_rows, rows_with_warnings),
        input_type=request.input_type,
        source_name=request.source_name,
        total_rows=len(parsed.records),
        valid_rows=valid_rows,
        rows_with_warnings=rows_with_warnings,
        failed_rows=failed_rows,
        mapped_columns=column_mapping.mapped_columns,
        unmapped_columns=column_mapping.unmapped_columns,
        normalized_leads=normalized_leads,
        global_issues=column_mapping.global_issues,
        capabilities=CapabilityMap(),
    )


def _map_columns(columns: list[str]) -> ColumnMapping:
    alias_to_field = _alias_to_field_map()
    mapped_columns: dict[str, str] = {}
    unmapped_columns: list[str] = []
    field_by_column: dict[str, str] = {}
    global_issues: list[IntakeIssue] = []
    used_fields: set[str] = set()

    for column in columns:
        field_name = alias_to_field.get(_normalize_header(column))
        if field_name is None or field_name in used_fields:
            unmapped_columns.append(column)
            global_issues.append(
                _issue(
                    severity="info",
                    code="unmapped_column",
                    field=column,
                )
            )
            continue

        mapped_columns[column] = field_name
        field_by_column[column] = field_name
        used_fields.add(field_name)

    return ColumnMapping(
        mapped_columns=mapped_columns,
        unmapped_columns=unmapped_columns,
        field_by_column=field_by_column,
        global_issues=global_issues,
    )


def _alias_to_field_map() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for field_name, field_aliases in ALIAS_GROUPS.items():
        for alias in field_aliases:
            aliases[_normalize_header(alias)] = field_name
    return aliases


def _normalize_header(header: str) -> str:
    return header.strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_record(
    *,
    record: dict[str, Any],
    row_number: int,
    column_mapping: ColumnMapping,
    options: IntakeOptions,
    generated_lead_id_count: int,
) -> tuple[NormalizedLeadRow, bool]:
    values: dict[str, Any] = {field_name: None for field_name in LEAD_FIELDS}
    issues: list[IntakeIssue] = []

    for column, field_name in column_mapping.field_by_column.items():
        values[field_name] = _normalize_value(
            field_name=field_name,
            value=record.get(column),
            row_number=row_number,
            issues=issues,
        )

    if values["company_name"] is None:
        issues.append(
            _issue(
                severity="error",
                code="missing_company_name",
                row_number=row_number,
                field="company_name",
            )
        )
        return (
            NormalizedLeadRow(
                row_number=row_number,
                lead=None,
                confidence=None,
                issues=issues,
            ),
            False,
        )

    generated_lead_id = False
    if values["lead_id"] is None and options.generate_missing_lead_ids:
        values["lead_id"] = f"preview_{generated_lead_id_count + 1:03d}"
        generated_lead_id = True
        issues.append(
            _issue(
                severity="info",
                code="generated_lead_id",
                row_number=row_number,
                field="lead_id",
            )
        )

    _add_missing_field_warnings(values=values, row_number=row_number, issues=issues)

    lead = LeadIn.model_construct(**values)
    return (
        NormalizedLeadRow(
            row_number=row_number,
            lead=lead,
            confidence=_confidence(values=values, issues=issues),
            issues=issues,
        ),
        generated_lead_id,
    )


def _normalize_value(
    *,
    field_name: str,
    value: Any,
    row_number: int,
    issues: list[IntakeIssue],
) -> Any:
    if field_name == "employee_count":
        return _normalize_employee_count(value=value, row_number=row_number, issues=issues)

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    return value


def _normalize_employee_count(
    *,
    value: Any,
    row_number: int,
    issues: list[IntakeIssue],
) -> int | None:
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
        value = value.replace(",", "")

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        issues.append(
            _issue(
                severity="warning",
                code="invalid_employee_count",
                row_number=row_number,
                field="employee_count",
            )
        )
        return None


def _add_missing_field_warnings(
    *,
    values: dict[str, Any],
    row_number: int,
    issues: list[IntakeIssue],
) -> None:
    for field_name, code in (
        ("industry", "missing_industry"),
        ("website", "missing_website"),
        ("contact_role", "missing_contact_role"),
    ):
        if values[field_name] is None:
            issues.append(
                _issue(
                    severity="warning",
                    code=code,
                    row_number=row_number,
                    field=field_name,
                )
            )


def _confidence(
    *,
    values: dict[str, Any],
    issues: list[IntakeIssue],
) -> str:
    has_error = any(issue.severity == "error" for issue in issues)
    if (
        values["company_name"] is not None
        and values["industry"] is not None
        and (values["website"] is not None or values["contact_role"] is not None)
        and not has_error
    ):
        return "high"

    if values["company_name"] is not None and all(
        values[field_name] is None
        for field_name in (
            "website",
            "industry",
            "country",
            "employee_count",
            "contact_name",
            "contact_role",
            "notes",
        )
    ):
        return "low"

    return "medium"


def _preview_status(
    valid_rows: int,
    failed_rows: int,
    rows_with_warnings: int,
) -> str:
    if valid_rows == 0:
        return "preview_blocked"
    if failed_rows > 0 or rows_with_warnings > 0:
        return "preview_with_warnings"
    return "preview_ready"


def _unsupported_input_type_response(
    request: IntakePreviewRequest,
) -> IntakePreviewResponse:
    return IntakePreviewResponse(
        status="preview_blocked",
        input_type=request.input_type,
        source_name=request.source_name,
        total_rows=0,
        valid_rows=0,
        rows_with_warnings=0,
        failed_rows=0,
        mapped_columns={},
        unmapped_columns=[],
        normalized_leads=[],
        global_issues=[
            _issue(
                severity="error",
                code="unsupported_input_type",
            )
        ],
        capabilities=CapabilityMap(),
    )


def _issue(
    *,
    severity: str,
    code: str,
    row_number: int | None = None,
    field: str | None = None,
) -> IntakeIssue:
    return IntakeIssue(
        severity=severity,  # type: ignore[arg-type]
        code=code,
        message=ISSUE_MESSAGES[code],
        row_number=row_number,
        field=field,
    )
