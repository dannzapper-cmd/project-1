/**
 * Block 10F-A — multi-format intake file client tests.
 *
 * Run with:
 *   node --experimental-strip-types --test lib/api/__tests__/intake-file-client.test.ts
 */

import { afterEach, describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  postCsvIntakePreview,
  postIntakeFilePreview,
  postIntakePreview,
} from "../client.ts";
import {
  clearStoredDemoAccessCode,
  DEMO_ACCESS_HEADER,
  setStoredDemoAccessCode,
} from "../demo-access.ts";
import type { IntakePreviewResponse } from "../types.ts";

const globalWithWindow = globalThis as typeof globalThis & { window?: Window };

function installSessionStorage(): void {
  const values = new Map<string, string>();
  const storage: Storage = {
    get length() {
      return values.size;
    },
    clear() {
      values.clear();
    },
    getItem(key: string) {
      return values.get(key) ?? null;
    },
    key(index: number) {
      return Array.from(values.keys())[index] ?? null;
    },
    removeItem(key: string) {
      values.delete(key);
    },
    setItem(key: string, value: string) {
      values.set(key, value);
    },
  };
  globalWithWindow.window = { sessionStorage: storage } as unknown as Window;
}

function installBlockedSessionStorage(): void {
  const blocked = () => {
    throw new DOMException("sessionStorage is blocked", "SecurityError");
  };
  const storage: Storage = {
    get length() {
      blocked();
      return 0;
    },
    clear: blocked,
    getItem: blocked,
    key: blocked,
    removeItem: blocked,
    setItem: blocked,
  };
  globalWithWindow.window = { sessionStorage: storage } as unknown as Window;
}

function makePreviewFetch(captured: { url: string; init?: RequestInit }): typeof fetch {
  return (async (url: string, init?: RequestInit) => {
    captured.url = url;
    captured.init = init;
    return new Response(JSON.stringify(previewResponse()), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as unknown as typeof fetch;
}

afterEach(() => {
  clearStoredDemoAccessCode();
  delete globalWithWindow.window;
});

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
    installSessionStorage();
    setStoredDemoAccessCode("demo-code");
    const captured = { url: "", init: undefined as RequestInit | undefined };
    const fakeFetch = makePreviewFetch(captured);

    const file = new File(["company_name,industry\nAcme,SaaS\n"], "leads.csv", {
      type: "text/csv",
    });
    const response = await postIntakeFilePreview(file, {
      baseUrl: "https://api.test",
      fetchImpl: fakeFetch,
    });

    assert.equal(captured.url, "https://api.test/api/intake/extract-file");
    assert.equal(captured.init?.method, "POST");
    assert.equal(
      (captured.init?.headers as Record<string, string>)[DEMO_ACCESS_HEADER],
      "demo-code",
    );
    assert.ok(captured.init?.body instanceof FormData);
    assert.equal(response.input_type, "excel_file");

    const form = captured.init.body as FormData;
    assert.equal(form.get("file"), file);
    assert.equal(form.get("generate_missing_lead_ids"), "true");
  });

  it("sends the saved demo access header for pasted intake previews", async () => {
    installBlockedSessionStorage();
    setStoredDemoAccessCode("demo-code");
    const captured = { url: "", init: undefined as RequestInit | undefined };

    await postIntakePreview(
      {
        input_type: "pasted_table",
        source_name: "dashboard_paste",
        content: "company_name\tindustry\nAcme\tSaaS",
      },
      {
        baseUrl: "https://api.test",
        fetchImpl: makePreviewFetch(captured),
      },
    );

    assert.equal(captured.url, "https://api.test/api/intake/preview");
    assert.equal(
      (captured.init?.headers as Record<string, string>)[DEMO_ACCESS_HEADER],
      "demo-code",
    );
  });

  it("sends the saved demo access header for both FormData intake previews", async () => {
    installSessionStorage();
    setStoredDemoAccessCode("demo-code");
    const csvUpload = { url: "", init: undefined as RequestInit | undefined };
    const extractUpload = { url: "", init: undefined as RequestInit | undefined };
    const file = new File(["company_name,industry\nAcme,SaaS\n"], "leads.csv", {
      type: "text/csv",
    });

    await postCsvIntakePreview(file, {
      baseUrl: "https://api.test",
      fetchImpl: makePreviewFetch(csvUpload),
    });
    await postIntakeFilePreview(file, {
      baseUrl: "https://api.test",
      fetchImpl: makePreviewFetch(extractUpload),
    });

    assert.equal(csvUpload.url, "https://api.test/api/intake/preview-file/csv");
    assert.equal(extractUpload.url, "https://api.test/api/intake/extract-file");
    assert.equal(
      (csvUpload.init?.headers as Record<string, string>)[DEMO_ACCESS_HEADER],
      "demo-code",
    );
    assert.equal(
      (extractUpload.init?.headers as Record<string, string>)[DEMO_ACCESS_HEADER],
      "demo-code",
    );
  });

  it("does not send the demo access header when no code is saved", async () => {
    const captured = { url: "", init: undefined as RequestInit | undefined };

    await postIntakePreview(
      {
        input_type: "pasted_table",
        source_name: "dashboard_paste",
        content: "company_name\tindustry\nAcme\tSaaS",
      },
      {
        baseUrl: "https://api.test",
        fetchImpl: makePreviewFetch(captured),
      },
    );

    assert.ok(
      !(DEMO_ACCESS_HEADER in (captured.init?.headers as Record<string, string>)),
    );
  });
});
