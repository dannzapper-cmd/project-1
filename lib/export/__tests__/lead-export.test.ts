/**
 * Block 7.4 — Unit tests for the reviewed-lead CSV export helpers.
 *
 * Run with:
 *   node --experimental-strip-types --test lib/export/__tests__/lead-export.test.ts
 *
 * Uses Node 22's built-in test runner; no new dependency.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  REVIEWED_LEAD_CSV_HEADERS,
  csvEscape,
  leadCsvFilename,
  leadToCsv,
  protectCsvFormula,
  toCsvCell,
} from "../lead-export.ts";
import type { LeadDetail } from "../../types.ts";

function makeDetail(overrides: Partial<LeadDetail> = {}): LeadDetail {
  // Synthetic but RFC-4180-realistic fixture. Field values were
  // chosen to exercise every escape branch when threaded through
  // `leadToCsv`. The tests below override individual fields where
  // they need to assert a specific escape.
  return {
    id: "lead_001",
    company: "Veltrix Systems",
    website: "veltrixsystems.io",
    industry: "B2B SaaS",
    country: "United States",
    employees: "51-200",
    contact_name: "Sarah Whitmore",
    contact_role: "VP Revenue Operations",
    fit_score: 92,
    priority: "High",
    qa_score: 100,
    status: "Approved",
    est_cost: "N/A",
    email_subject: "Idea for Veltrix Systems",
    run_mode: "Replay",
    company_summary: "",
    opportunity_signals: [],
    evidence_cards: [],
    fit_reasons: [],
    fit_risks: [],
    pain_hypothesis: "",
    pain_confidence: "High",
    sales_angle: "",
    core_message: "",
    likely_objection: "",
    email_body: "Hi Sarah,\n\nWe noticed Veltrix is hiring SDRs.\n\nBest,\nLeadForge",
    personalization_notes: [],
    qa_scores: {
      personalization: 0,
      evidence_coverage: 0,
      cta_quality: 0,
      tone_match: 0,
      hallucination_risk: "Low",
      recommendation: "Review carefully",
    },
    est_total_latency: "0ms",
    model_used: "Mock Model",
    agent_steps: 5,
    est_tokens: 0,
    trace: [],
    ...overrides,
  } as LeadDetail;
}

// --------------------------------------------------------------------------- //
// protectCsvFormula                                                            //
// --------------------------------------------------------------------------- //

describe("protectCsvFormula", () => {
  it("prefixes values starting with =, +, -, @, tab, or CR", () => {
    assert.equal(protectCsvFormula("=SUM(A1:A2)"), "'=SUM(A1:A2)");
    assert.equal(protectCsvFormula("+1-555-0100"), "'+1-555-0100");
    assert.equal(protectCsvFormula("-budget"), "'-budget");
    assert.equal(protectCsvFormula("@user"), "'@user");
    assert.equal(protectCsvFormula("\ttab-led"), "'\ttab-led");
    assert.equal(protectCsvFormula("\rcarriage"), "'\rcarriage");
  });

  it("leaves safe values untouched", () => {
    assert.equal(protectCsvFormula("Veltrix Systems"), "Veltrix Systems");
    assert.equal(protectCsvFormula("$0.00"), "$0.00");
    assert.equal(protectCsvFormula("United States"), "United States");
    assert.equal(protectCsvFormula(""), "");
  });

  it("coerces non-string inputs and tolerates null/undefined", () => {
    assert.equal(protectCsvFormula(92), "92");
    assert.equal(protectCsvFormula(0), "0");
    assert.equal(protectCsvFormula(null), "");
    assert.equal(protectCsvFormula(undefined), "");
  });
});

// --------------------------------------------------------------------------- //
// csvEscape                                                                    //
// --------------------------------------------------------------------------- //

describe("csvEscape", () => {
  it("returns the input verbatim when no special characters are present", () => {
    assert.equal(csvEscape("Veltrix Systems"), "Veltrix Systems");
    assert.equal(csvEscape(""), "");
  });

  it("wraps and doubles inner quotes per RFC 4180", () => {
    assert.equal(
      csvEscape('we help teams like "Acme" grow.'),
      '"we help teams like ""Acme"" grow."',
    );
  });

  it("wraps strings containing commas", () => {
    assert.equal(csvEscape("Hi John, hope you are well."), '"Hi John, hope you are well."');
  });

  it("preserves newlines inside a quoted field (does NOT strip them)", () => {
    const value = "line one\nline two\r\nline three";
    assert.equal(csvEscape(value), `"line one\nline two\r\nline three"`);
  });
});

// --------------------------------------------------------------------------- //
// toCsvCell — composition order: formula protect then RFC 4180 wrap            //
// --------------------------------------------------------------------------- //

describe("toCsvCell", () => {
  it("applies formula protection BEFORE RFC 4180 wrapping", () => {
    // The apostrophe is inserted first; then the resulting string
    // does not need to be wrapped because none of the trigger
    // characters appear in "'=SUM(A1:A2)".
    assert.equal(toCsvCell("=SUM(A1:A2)"), "'=SUM(A1:A2)");
  });

  it("wraps after protecting when the protected value still needs wrapping", () => {
    // Value starts with '=' AND contains a comma — both branches fire.
    assert.equal(toCsvCell("=A1, B1"), `"'=A1, B1"`);
  });

  it("treats null/undefined as the empty cell", () => {
    assert.equal(toCsvCell(null), "");
    assert.equal(toCsvCell(undefined), "");
  });
});

// --------------------------------------------------------------------------- //
// leadCsvFilename                                                              //
// --------------------------------------------------------------------------- //

describe("leadCsvFilename", () => {
  it("uses the lead_id verbatim when it is filesystem-safe", () => {
    assert.equal(leadCsvFilename("lead_001"), "leadforge-lead_001-reviewed.csv");
  });

  it("sanitises path separators and other shell-unsafe characters", () => {
    // Dots and underscores are kept (they are filesystem-safe and
    // `link.download` ignores path separators anyway); only the
    // forward-slashes and the space below are remapped to '_'.
    assert.equal(
      leadCsvFilename("../../etc/passwd"),
      "leadforge-.._.._etc_passwd-reviewed.csv",
    );
    assert.equal(
      leadCsvFilename("lead 001"),
      "leadforge-lead_001-reviewed.csv",
    );
  });

  it("falls back to a default suffix only when the id is empty", () => {
    assert.equal(leadCsvFilename(""), "leadforge-lead-reviewed.csv");
    // Non-empty but entirely-sanitised ids keep their underscores
    // rather than collapsing to the default. This is fine because
    // the filename is still well-formed and the user can rename.
    assert.equal(leadCsvFilename("///"), "leadforge-___-reviewed.csv");
  });
});

// --------------------------------------------------------------------------- //
// leadToCsv — end-to-end                                                       //
// --------------------------------------------------------------------------- //

describe("leadToCsv", () => {
  it("produces exactly one header row and one value row terminated by LF", () => {
    const detail = makeDetail();
    const csv = leadToCsv(detail, "Approved");

    // RFC 4180-aware row count: walk the string and only count a
    // newline as a row terminator when we are outside a double-
    // quoted field. The fixture's email_body contains embedded
    // newlines, so a naive split("\n") would over-count.
    let rowTerminators = 0;
    let insideQuotes = false;
    for (let i = 0; i < csv.length; i++) {
      const ch = csv[i];
      if (ch === '"') {
        // RFC 4180 escapes "" as a literal quote inside a quoted
        // field; skip the next character without flipping state.
        if (insideQuotes && csv[i + 1] === '"') {
          i += 1;
          continue;
        }
        insideQuotes = !insideQuotes;
      } else if (ch === "\n" && !insideQuotes) {
        rowTerminators += 1;
      }
    }
    assert.equal(
      rowTerminators,
      2,
      "expected exactly two logical row terminators (header + value)",
    );
    assert.ok(csv.endsWith("\n"), "expected trailing LF");
  });

  it("uses the canonical header order", () => {
    const detail = makeDetail();
    const csv = leadToCsv(detail, "Approved");
    const header = csv.split("\n")[0];
    assert.equal(header, REVIEWED_LEAD_CSV_HEADERS.join(","));
  });

  it("emits the review_status passed in, not detail.status", () => {
    const detail = makeDetail({ status: "Pending Review" });
    const csv = leadToCsv(detail, "Needs Edit");
    assert.ok(csv.includes(",Needs Edit,"));
    assert.ok(!csv.includes(",Pending Review,"));
  });

  it("preserves email_body with commas, newlines, and quotes via RFC 4180", () => {
    const tricky =
      'Hi Sarah,\nWe help teams like "Acme" grow.\nBest,\nLeadForge';
    const detail = makeDetail({ email_body: tricky });
    const csv = leadToCsv(detail, "Approved");

    // Wrapped and inner quotes doubled.
    assert.ok(
      csv.includes(`"Hi Sarah,\nWe help teams like ""Acme"" grow.\nBest,\nLeadForge"`),
      "email_body should be wrapped with doubled inner quotes and newlines preserved",
    );
    // Newlines must survive inside the quoted field.
    assert.ok(csv.split("\n").length > 2, "newlines should be preserved inside the field");
  });

  it("protects formula-injection in subject and email_body", () => {
    const detail = makeDetail({
      // Subject leads with '=' (formula prefix triggers) and does NOT
      // contain comma/quote/newline, so it does not need RFC 4180
      // wrapping. The leading apostrophe is the only mutation.
      email_subject: "=cmd|' /C calc'!A1",
      // Body leads with '@' (formula prefix triggers) AND contains a
      // comma, so RFC 4180 wrapping kicks in after the apostrophe.
      email_body: "@startup() then ,",
    });
    const csv = leadToCsv(detail, "Approved");
    assert.ok(
      csv.includes("'=cmd|' /C calc'!A1"),
      "subject should carry the apostrophe prefix without being wrapped",
    );
    assert.ok(
      csv.includes(`"'@startup() then ,"`),
      "body should be apostrophe-prefixed then wrapped because of the comma",
    );
  });

  it("renders numeric cells as strings", () => {
    const detail = makeDetail({ fit_score: 92 });
    const csv = leadToCsv(detail, "Approved");
    assert.ok(csv.includes(",92,"));
  });
});
