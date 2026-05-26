/**
 * Block 10B — run quality summary for the demo dashboard.
 */

import type { Lead, RunMetrics } from "@/lib/types";

export interface RunQualitySummary {
  runModeLabel: string;
  modelModeLabel: string;
  dataSourceLabel: string;
  leadsProcessed: number;
  avgQaScoreLabel: string;
  totalCostLabel: string;
  costPerLeadLabel: string;
  lowEvidenceNote: string | null;
  replayNote: string;
}

function formatQa(score: number | null): string {
  if (score === null || Number.isNaN(score)) return "—";
  return Number.isInteger(score) ? String(score) : score.toFixed(1);
}

function parseCostUsd(totalCost: string): number | null {
  const normalized = totalCost.trim();
  if (!normalized || normalized.toUpperCase() === "N/A") return null;
  const match = normalized.match(/\$?\s*([\d.]+)/);
  if (!match) return null;
  const value = Number.parseFloat(match[1]);
  return Number.isFinite(value) ? value : null;
}

export function computeRunQualitySummary(opts: {
  metrics: RunMetrics;
  dataSource: "mock" | "api";
  leads?: Lead[];
  lowEvidenceCount?: number;
  userBatchActive?: boolean;
}): RunQualitySummary {
  const { metrics, dataSource, lowEvidenceCount, userBatchActive } = opts;
  const costUsd = parseCostUsd(metrics.total_cost);
  const costPerLeadLabel =
    costUsd !== null && metrics.total_processed > 0
      ? `$${(costUsd / metrics.total_processed).toFixed(3)} / lead`
      : "N/A";

  const isReplay =
    metrics.run_mode === "Replay" || dataSource === "mock";

  let lowEvidenceNote: string | null = null;
  if (lowEvidenceCount !== undefined && lowEvidenceCount > 0) {
    lowEvidenceNote = `${lowEvidenceCount} lead${lowEvidenceCount === 1 ? "" : "s"} flagged with low evidence or missing context — review carefully before approving.`;
  }

  const dataSourceLabel =
    userBatchActive
      ? "API-backed user batch"
      : dataSource === "mock"
        ? "Replay demo (pre-computed)"
        : "API-backed demo dataset";

  const replayNote = isReplay
    ? "Replay/demo mode: no live model calls from this view. Sample results are safe and zero-cost."
    : "Live-backed run: costs and model usage depend on backend configuration.";

  return {
    runModeLabel: metrics.run_mode,
    modelModeLabel: metrics.model_used,
    dataSourceLabel,
    leadsProcessed: metrics.total_processed,
    avgQaScoreLabel: formatQa(metrics.avg_qa_score),
    totalCostLabel: metrics.total_cost,
    costPerLeadLabel,
    lowEvidenceNote,
    replayNote,
  };
}
