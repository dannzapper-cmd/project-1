/**
 * Block 10B — business value metric tests.
 *
 * Run with:
 *   node --experimental-strip-types --test lib/metrics/__tests__/business-value.test.ts
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  MANUAL_MINUTES_PER_LEAD_ASSUMPTION,
  computeBusinessValueMetrics,
  countReviewReadyLeads,
  priorityBreakdownFromLeads,
} from "../business-value.ts";
import type { Lead, RunMetrics } from "../../types.ts";

const baseMetrics: RunMetrics = {
  total_processed: 10,
  high_fit_leads: 4,
  avg_qa_score: 81,
  total_cost: "$0.395",
  run_timestamp: "demo",
  model_used: "replay",
  run_mode: "Replay",
};

const sampleLeads: Lead[] = [
  {
    id: "1",
    company: "A",
    website: "",
    industry: "",
    country: "",
    employees: "",
    contact_name: "",
    contact_role: "",
    fit_score: 80,
    priority: "High",
    qa_score: 85,
    status: "Pending Review",
    est_cost: "",
    email_subject: "",
    run_mode: "Replay",
  },
  {
    id: "2",
    company: "B",
    website: "",
    industry: "",
    country: "",
    employees: "",
    contact_name: "",
    contact_role: "",
    fit_score: 50,
    priority: "Low",
    qa_score: 60,
    status: "Pending Review",
    est_cost: "",
    email_subject: "",
    run_mode: "Replay",
  },
];

describe("computeBusinessValueMetrics", () => {
  it("computes high-fit ratio and manual hours saved", () => {
    const value = computeBusinessValueMetrics(baseMetrics, sampleLeads);
    assert.equal(value.highFitRatioPercent, 40);
    assert.equal(
      value.estimatedManualHoursSaved,
      Math.round(((10 * MANUAL_MINUTES_PER_LEAD_ASSUMPTION) / 60) * 10) / 10,
    );
  });

  it("parses cost per lead when total cost is present", () => {
    const value = computeBusinessValueMetrics(baseMetrics, sampleLeads);
    assert.equal(value.costPerLeadLabel, "$0.040 / lead");
  });

  it("marks replay runs without parseable cost as N/A per lead", () => {
    const value = computeBusinessValueMetrics(
      { ...baseMetrics, total_cost: "N/A" },
      sampleLeads,
    );
    assert.match(value.costPerLeadLabel, /N\/A/);
  });
});

describe("lead helpers", () => {
  it("counts review-ready leads with fit and QA thresholds", () => {
    assert.equal(countReviewReadyLeads(sampleLeads), 1);
  });

  it("builds priority breakdown from leads", () => {
    assert.deepEqual(priorityBreakdownFromLeads(sampleLeads), {
      high: 1,
      medium: 0,
      low: 1,
    });
  });
});
