import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  isProcessEnabled,
  processLimitMessage,
  processableLeads,
  rowMessage,
} from "../preview-state.ts";
import type { IntakePreviewResponse, NormalizedLeadRow } from "../../api/types.ts";

function row(overrides: Partial<NormalizedLeadRow>): NormalizedLeadRow {
  return {
    row_number: 1,
    status: "valid",
    normalized_fields: {},
    lead: {
      lead_id: "preview_001",
      company_name: "Acme",
      industry: "B2B SaaS",
      website: null,
      country: null,
      employee_count: null,
      contact_name: null,
      contact_role: null,
      notes: null,
    },
    confidence: "high",
    missing_required_fields: [],
    low_confidence_fields: [],
    issues: [],
    ...overrides,
  };
}

function preview(rows: NormalizedLeadRow[]): IntakePreviewResponse {
  return {
    status: "preview_with_warnings",
    input_type: "pasted_table",
    source_name: null,
    total_rows: rows.length,
    valid_rows: rows.filter((r) => r.status !== "invalid").length,
    rows_with_warnings: rows.filter((r) => r.status === "warning").length,
    failed_rows: rows.filter((r) => r.status === "invalid").length,
    max_leads_per_run: 2,
    mapped_columns: {},
    unmapped_columns: [],
    normalized_leads: rows,
    global_issues: [],
    capabilities: {
      implemented_now: ["csv_text", "pasted_table"],
      future_adapters: [],
    },
  };
}

describe("intake preview state", () => {
  it("processes valid and warning rows, excluding invalid rows", () => {
    const result = preview([
      row({ status: "valid" }),
      row({ status: "warning", row_number: 2 }),
      row({ status: "invalid", row_number: 3, lead: null }),
    ]);

    assert.equal(processableLeads(result).length, 2);
  });

  it("requires mapping confirmation before enabling processing", () => {
    const result = preview([row({ status: "valid" })]);

    assert.equal(
      isProcessEnabled({
        preview: result,
        mappingConfirmed: false,
        processing: false,
      }),
      false,
    );
    assert.equal(
      isProcessEnabled({
        preview: result,
        mappingConfirmed: true,
        processing: false,
      }),
      true,
    );
  });

  it("surfaces max-leads messaging", () => {
    const result = preview([
      row({ row_number: 1 }),
      row({ row_number: 2 }),
      row({ row_number: 3 }),
    ]);

    assert.match(processLimitMessage(result) ?? "", /first 2 valid leads/);
  });

  it("describes validation messages for invalid and warning rows", () => {
    assert.equal(
      rowMessage(
        row({
          status: "invalid",
          lead: null,
          missing_required_fields: ["industry"],
        }),
      ),
      "Missing required: industry",
    );
    assert.match(
      rowMessage(
        row({
          status: "warning",
          issues: [
            {
              severity: "warning",
              code: "missing_website",
              message: "Missing website.",
              row_number: 1,
              field: "website",
            },
          ],
        }),
      ),
      /Missing website/,
    );
  });
});
