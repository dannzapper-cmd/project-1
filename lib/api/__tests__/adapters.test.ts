/**
 * Phase 7.0 — adapter unit tests.
 *
 * Run with:
 *   node --experimental-strip-types --test lib/api/__tests__/adapters.test.ts
 *
 * Node 22's built-in test runner is used deliberately so this PR
 * adds no new runtime dependency. `--experimental-strip-types`
 * (stable since Node 22.6) lets the runner load TypeScript source
 * directly without a transpiler.
 *
 * The tests run against fixtures captured from the real backend
 * routes (`GET /api/demo/pipeline/batch` and `GET /api/demo/leads`)
 * via FastAPI `TestClient`. They never hand-craft a response shape.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

import {
  AGENT_LABELS,
  toAgentStatuses,
  toLead,
  toLeadDetail,
  toLeads,
  toRunMetrics,
  toTraceEntries,
} from "../adapters.ts";
import { joinBatchWithLeads } from "../client.ts";
import type {
  LeadIn,
  PipelineRunContractOutput,
} from "../types.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const FIXTURES = resolve(HERE, "..", "__fixtures__");

function loadJson<T>(name: string): T {
  return JSON.parse(readFileSync(resolve(FIXTURES, name), "utf-8")) as T;
}

const batch = loadJson<PipelineRunContractOutput>("pipeline_batch.json");
const leads = loadJson<LeadIn[]>("demo_leads.json");
const enriched = joinBatchWithLeads(batch, leads);

describe("fixture sanity", () => {
  it("is a real PipelineRunContractOutput from the backend", () => {
    assert.equal(batch.run_mode, "deterministic_pipeline");
    assert.equal(batch.model_mode, "mock");
    assert.equal(typeof batch.run_id, "string");
    assert.ok(batch.run_id.startsWith("pipeline_batch_"));
    assert.equal(batch.results.length, batch.lead_count);
    assert.ok(batch.results.length >= 1);
  });

  it("every per-lead result has intake=null in Phase 6.1/6.2", () => {
    for (const r of batch.results) {
      assert.equal(r.intake, null);
      assert.equal(r.trace.length, 5);
    }
  });

  it("/api/demo/leads fixture has matching lead_ids", () => {
    const leadIds = new Set(leads.map((l) => l.lead_id));
    for (const r of batch.results) {
      assert.ok(
        leadIds.has(r.lead_id),
        `pipeline lead ${r.lead_id} missing from /leads`,
      );
    }
  });
});

describe("toLead", () => {
  it("flattens nested LeadPipelineContractOutput correctly", () => {
    const first = enriched.results[0];
    const lead = toLead(first);

    assert.equal(lead.id, first.result.lead_id);
    assert.equal(lead.company, first.lead_in!.company_name);
    assert.equal(lead.industry, first.lead_in!.industry);
    assert.equal(lead.country, first.lead_in!.country);
    assert.equal(lead.contact_name, first.lead_in!.contact_name);
    assert.equal(lead.contact_role, first.lead_in!.contact_role);
    assert.equal(lead.fit_score, first.result.qualification!.fit_score);
    assert.equal(lead.priority, first.result.qualification!.priority);
    assert.equal(lead.qa_score, first.result.qa!.qa_score);
    assert.equal(lead.email_subject, first.result.email!.email_subject);

    assert.equal(lead.status, "Pending Review");
    assert.equal(lead.est_cost, "N/A");
    assert.equal(lead.run_mode, "Replay");
  });

  it("handles missing fields (research=null, lead_in=null) without crashing", () => {
    const original = enriched.results[0].result;
    const degraded = {
      result: {
        ...original,
        research: null,
        qualification: null,
        strategy: null,
        email: null,
        qa: null,
      },
      lead_in: null,
    };

    const lead = toLead(degraded);
    assert.equal(lead.fit_score, 0);
    assert.equal(lead.priority, "Low");
    assert.equal(lead.qa_score, 0);
    assert.equal(lead.email_subject, "");
    assert.equal(lead.company, original.lead_id);
    assert.equal(lead.employees, "Unknown");
  });

  it("normalises lead ids: lead-001 → lead_001", () => {
    const synthetic = {
      result: {
        ...enriched.results[0].result,
        lead_id: "lead-001",
      },
      lead_in: enriched.results[0].lead_in,
    };
    const lead = toLead(synthetic);
    assert.equal(lead.id, "lead_001");
  });

  it("buckets employee_count as expected", () => {
    function bucketFor(count: number | null): string {
      const synthetic = {
        result: enriched.results[0].result,
        lead_in: {
          ...enriched.results[0].lead_in!,
          employee_count: count,
        },
      };
      return toLead(synthetic).employees;
    }

    assert.equal(bucketFor(null), "Unknown");
    assert.equal(bucketFor(5), "1-10");
    assert.equal(bucketFor(50), "11-50");
    assert.equal(bucketFor(140), "51-200");
    assert.equal(bucketFor(500), "201-500");
    assert.equal(bucketFor(900), "501-1000");
    assert.equal(bucketFor(5000), "1000+");
  });
});

describe("toLeads", () => {
  it("returns one Lead per batch result, preserving order", () => {
    const out = toLeads(enriched);
    assert.equal(out.length, enriched.results.length);
    for (let i = 0; i < out.length; i++) {
      assert.equal(out[i].id, enriched.results[i].result.lead_id);
    }
  });
});

describe("toLeadDetail", () => {
  it("flattens research/qualification/strategy/email/qa into LeadDetail", () => {
    const first = enriched.results[0];
    const detail = toLeadDetail(first);

    assert.equal(detail.company_summary, first.result.research!.company_summary);
    assert.deepEqual(
      detail.opportunity_signals,
      first.result.research!.opportunity_signals,
    );
    assert.equal(
      detail.evidence_cards.length,
      first.result.research!.evidence_cards.length,
    );
    assert.deepEqual(detail.fit_reasons, first.result.qualification!.fit_reasons);
    assert.deepEqual(detail.fit_risks, first.result.qualification!.fit_risks);
    assert.equal(detail.pain_hypothesis, first.result.strategy!.pain_hypothesis);
    assert.equal(detail.sales_angle, first.result.strategy!.sales_angle);
    assert.equal(detail.email_body, first.result.email!.email_body);
    assert.equal(detail.qa_scores.personalization, first.result.qa!.qa_scores.personalization);
    assert.equal(detail.agent_steps, 5);
    assert.equal(typeof detail.est_tokens, "number");
  });

  it("maps EvidenceSource enum strings to frontend literals 1:1 (no remap needed)", () => {
    const detail = toLeadDetail(enriched.results[0]);
    const validSources = new Set(["Knowledge Base", "Public Data", "Demo Context"]);
    assert.ok(detail.evidence_cards.length >= 1);
    for (const card of detail.evidence_cards) {
      assert.ok(
        validSources.has(card.source_type),
        `unexpected source_type: ${card.source_type}`,
      );
      assert.equal(typeof card.id, "string");
      assert.ok(card.id.length > 0);
    }
  });
});

describe("toRunMetrics", () => {
  it("derives totals from PipelineRunSummary", () => {
    const metrics = toRunMetrics(enriched);
    assert.equal(metrics.total_processed, batch.summary.processed_leads);
    assert.equal(metrics.high_fit_leads, batch.summary.high_priority_leads);
    assert.equal(metrics.avg_qa_score, batch.summary.average_qa_score);
    assert.equal(metrics.total_cost, "N/A");
    assert.equal(metrics.model_used, "Mock Model");
    assert.equal(metrics.run_mode, "Replay");
    assert.equal(metrics.run_timestamp, batch.run_id);
  });

  it("handles average_qa_score=null", () => {
    const nulled = {
      ...enriched,
      summary: { ...enriched.summary, average_qa_score: null },
    };
    const metrics = toRunMetrics(nulled);
    assert.equal(metrics.avg_qa_score, null);
  });
});

describe("toAgentStatuses", () => {
  it("returns exactly 5 entries (no Intake) in canonical order", () => {
    const rows = toAgentStatuses(enriched);
    assert.equal(rows.length, 5);
    assert.deepEqual(
      rows.map((r) => r.name),
      ["Research", "Qualify", "Strategize", "Draft", "Evaluate"],
    );
  });

  it("computes a success_rate string per agent", () => {
    const total = enriched.results.length;
    for (const row of toAgentStatuses(enriched)) {
      assert.match(row.success_rate, new RegExp(`^\\d+/${total}$`));
    }
  });
});

describe("toTraceEntries", () => {
  it("maps research_agent → 'Research' via label map", () => {
    const first = enriched.results[0].result;
    const view = toTraceEntries(first);

    assert.equal(view.length, 5);
    assert.deepEqual(
      view.map((e) => e.agent),
      ["Research", "Qualify", "Strategize", "Draft", "Evaluate"],
    );
    for (let i = 0; i < view.length; i++) {
      assert.equal(view[i].input_summary, first.trace[i].input_summary);
      assert.equal(view[i].output_summary, first.trace[i].output_summary);
      assert.equal(view[i].latency, first.trace[i].latency);
      assert.equal(view[i].tokens, first.trace[i].tokens);
      assert.equal(view[i].prompt_version, first.trace[i].prompt_version);
    }
  });

  it("AGENT_LABELS covers every snake_case agent the pipeline emits", () => {
    const seenAgents = new Set<string>();
    for (const r of batch.results) {
      for (const t of r.trace) seenAgents.add(t.agent);
    }
    for (const agent of seenAgents) {
      assert.ok(
        agent in AGENT_LABELS,
        `AGENT_LABELS missing entry for ${agent}`,
      );
    }
  });

  it("widens status enum to include 'running' | 'pending' (compile-time)", () => {
    // The view-model TraceEntry must accept all five backend statuses.
    // This assertion is structural; the literal cast would fail to
    // type-check before the Phase 7.0 widening of `lib/types.ts`.
    const view = toTraceEntries(enriched.results[0].result);
    const allowed = new Set(["success", "warning", "failed", "running", "pending"]);
    for (const entry of view) {
      assert.ok(allowed.has(entry.status), `unexpected status: ${entry.status}`);
    }

    // Construct a synthetic wide trace and confirm it round-trips.
    const synthetic = {
      trace: [
        ...enriched.results[0].result.trace,
        {
          agent: "research_agent",
          status: "running" as const,
          input_summary: "",
          output_summary: "",
          latency: "0ms",
          tokens: 0,
          prompt_version: "v0",
          model: "none",
          simulated: false,
        },
        {
          agent: "qualifier_agent",
          status: "pending" as const,
          input_summary: "",
          output_summary: "",
          latency: "0ms",
          tokens: 0,
          prompt_version: "v0",
          model: "none",
          simulated: false,
        },
      ],
    };
    const out = toTraceEntries(synthetic);
    assert.equal(out[out.length - 2].status, "running");
    assert.equal(out[out.length - 1].status, "pending");
  });
});

describe("joinBatchWithLeads", () => {
  it("pairs every batch result with its source LeadIn", () => {
    const joined = joinBatchWithLeads(batch, leads);
    assert.equal(joined.results.length, batch.results.length);
    for (const r of joined.results) {
      assert.notEqual(r.lead_in, null);
      assert.equal(r.lead_in!.lead_id, r.result.lead_id);
    }
  });

  it("falls back to lead_in=null when the join fails", () => {
    const joined = joinBatchWithLeads(batch, []);
    for (const r of joined.results) {
      assert.equal(r.lead_in, null);
    }
  });
});
