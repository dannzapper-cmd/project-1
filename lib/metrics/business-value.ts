/**
 * Block 10B — illustrative business-value metrics from run data.
 *
 * All figures are conservative estimates for demo storytelling.
 * They are not guaranteed ROI, revenue, or conversion outcomes.
 */

import type { Lead, RunMetrics } from "@/lib/types";

/** Midpoint of 30–45 minutes manual research + qualification per lead. */
export const MANUAL_MINUTES_PER_LEAD_ASSUMPTION = 37.5;

export const MANUAL_MINUTES_RANGE_LABEL = "30–45 min";

export interface PriorityBreakdown {
  high: number;
  medium: number;
  low: number;
}

export interface BusinessValueMetrics {
  totalProcessed: number;
  highFitLeads: number;
  highFitRatioPercent: number | null;
  avgQaScore: number | null;
  totalRunCostLabel: string;
  costPerLeadLabel: string;
  estimatedManualHoursSaved: number;
  estimatedReviewReadyLeads: number;
  priorityBreakdown: PriorityBreakdown;
  pipelineQualitySummary: string;
  valueNarrative: string;
  assumptionsNote: string;
}

function parseCostUsd(totalCost: string): number | null {
  const normalized = totalCost.trim();
  if (!normalized || normalized.toUpperCase() === "N/A") return null;
  const match = normalized.match(/\$?\s*([\d.]+)/);
  if (!match) return null;
  const value = Number.parseFloat(match[1]);
  return Number.isFinite(value) ? value : null;
}

export function priorityBreakdownFromLeads(leads: Lead[]): PriorityBreakdown {
  const breakdown: PriorityBreakdown = { high: 0, medium: 0, low: 0 };
  for (const lead of leads) {
    if (lead.priority === "High") breakdown.high += 1;
    else if (lead.priority === "Medium") breakdown.medium += 1;
    else breakdown.low += 1;
  }
  return breakdown;
}

/**
 * Review-ready = high fit (score >= 70) with QA >= 70 when scores exist.
 * Conservative gate for “ready for human review” storytelling.
 */
export function countReviewReadyLeads(leads: Lead[]): number {
  return leads.filter((lead) => lead.fit_score >= 70 && lead.qa_score >= 70).length;
}

export function buildPipelineQualitySummary(
  metrics: RunMetrics,
  breakdown: PriorityBreakdown,
): string {
  const parts: string[] = [];
  if (metrics.high_fit_leads > 0) {
    parts.push(
      `${metrics.high_fit_leads} high-fit lead${metrics.high_fit_leads === 1 ? "" : "s"} (fit ≥ 70)`,
    );
  }
  if (breakdown.high > 0) {
    parts.push(`${breakdown.high} marked High priority`);
  }
  if (metrics.avg_qa_score !== null && metrics.avg_qa_score >= 75) {
    parts.push(`average QA ${metrics.avg_qa_score.toFixed(0)} supports review confidence`);
  } else if (metrics.avg_qa_score !== null) {
    parts.push(`average QA ${metrics.avg_qa_score.toFixed(0)} — spot-check lower-scoring drafts`);
  }
  if (parts.length === 0) {
    return "Run completed; open lead details to inspect fit, evidence, and QA before approving.";
  }
  return parts.join("; ") + ".";
}

export function computeBusinessValueMetrics(
  metrics: RunMetrics,
  leads: Lead[] = [],
): BusinessValueMetrics {
  const totalProcessed = metrics.total_processed;
  const highFitRatioPercent =
    totalProcessed > 0
      ? Math.round((metrics.high_fit_leads / totalProcessed) * 100)
      : null;

  const estimatedManualHoursSaved =
    Math.round(((totalProcessed * MANUAL_MINUTES_PER_LEAD_ASSUMPTION) / 60) * 10) / 10;

  const priorityBreakdown =
    leads.length > 0
      ? priorityBreakdownFromLeads(leads)
      : { high: metrics.high_fit_leads, medium: 0, low: 0 };

  const estimatedReviewReadyLeads =
    leads.length > 0 ? countReviewReadyLeads(leads) : metrics.high_fit_leads;

  const costUsd = parseCostUsd(metrics.total_cost);
  const costPerLeadLabel =
    costUsd !== null && totalProcessed > 0
      ? `$${(costUsd / totalProcessed).toFixed(3)} / lead`
      : "N/A (replay has no API cost)";

  const pipelineQualitySummary = buildPipelineQualitySummary(metrics, priorityBreakdown);

  const valueNarrative =
    totalProcessed === 0
      ? "Process leads to see illustrative time-savings and pipeline quality estimates."
      : `This run prepared ${estimatedReviewReadyLeads} review-ready lead${estimatedReviewReadyLeads === 1 ? "" : "s"} with structured research, fit rationale, and draft copy — estimated ~${estimatedManualHoursSaved}h of manual research time avoided at ${MANUAL_MINUTES_RANGE_LABEL}/lead (illustrative).`;

  const assumptionsNote =
    `Estimates assume ${MANUAL_MINUTES_RANGE_LABEL} manual research + qualification + first draft per lead. LeadForge prepares review-ready output for human approval; figures are illustrative, not guaranteed business outcomes.`;

  return {
    totalProcessed,
    highFitLeads: metrics.high_fit_leads,
    highFitRatioPercent,
    avgQaScore: metrics.avg_qa_score,
    totalRunCostLabel: metrics.total_cost,
    costPerLeadLabel,
    estimatedManualHoursSaved,
    estimatedReviewReadyLeads,
    priorityBreakdown,
    pipelineQualitySummary,
    valueNarrative,
    assumptionsNote,
  };
}
