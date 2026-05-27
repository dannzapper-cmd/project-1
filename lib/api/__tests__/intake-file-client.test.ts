/**
 * Block 10F-A — multi-format intake file client tests.
 *
 * Run with:
 *   node --experimental-strip-types --test lib/api/__tests__/intake-file-client.test.ts
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { postIntakeFilePreview } from "../client.ts";
import type { IntakePreviewResponse } from "../types.ts";

function previewResponse(): IntakePreviewResponse {
  return {
    status: "preview_ready",
    input_type: "excel_file",
    source_name: "leads.xlsx",
    total_rows: 1,
    valid_rows: 1,
    rows_with_warnings: 0,
    failed_rows: 0,
    max_leads_per_run: 10,
    mapped_columns: {
      company_name: "company_name",
      industry: "industry",
    },
    unmapped_columns: [],
    normalized_leads: [],
    global_issues: [],
    capabilities: {
      implemented_now: ["csv_file", "excel_file", "pdf_file"],
      future_adapters: ["image_file", "screenshot"],
    },
  };
}

describe("postIntakeFilePreview", () => {
  it("posts multipart form data to /api/intake/extract-file", async () => {
    let capturedUrl = "";
    let capturedInit: RequestInit | undefined;

    const fakeFetch = (async (url: string, init?: RequestInit) => {
      capturedUrl = url;
      capturedInit = init;
      return new Response(JSON.stringify(previewResponse()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const file = new File(["company_name,industry\nAcme,SaaS\n"], "leads.csv", {
      type: "text/csv",
    });
    const response = await postIntakeFilePreview(file, {
      baseUrl: "https://api.test",
      fetchImpl: fakeFetch,
      headers: { "X-LeadForge-Demo-Key": "demo-code" },
    });

    assert.equal(capturedUrl, "https://api.test/api/intake/extract-file");
    assert.equal(capturedInit?.method, "POST");
    assert.equal(
      (capturedInit?.headers as Record<string, string>)["X-LeadForge-Demo-Key"],
      "demo-code",
    );
    assert.ok(capturedInit?.body instanceof FormData);
    assert.equal(response.input_type, "excel_file");

    const form = capturedInit.body as FormData;
    assert.equal(form.get("file"), file);
    assert.equal(form.get("generate_missing_lead_ids"), "true");
  });
});
