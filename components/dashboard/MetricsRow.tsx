import { mockRunMetrics } from "@/lib/mock-data";
import type { RunMetrics } from "@/lib/types";

interface MetricsRowProps {
  /**
   * The run-level metrics to render. When omitted (e.g. during a
   * Phase 7.0-style mock-only render path) the component falls
   * back to `mockRunMetrics` so existing call sites keep working
   * without changes.
   */
  metrics?: RunMetrics | null;
}

function formatAverage(score: number | null): string {
  if (score === null || score === undefined || Number.isNaN(score)) {
    return "—";
  }
  return Number.isInteger(score) ? String(score) : score.toFixed(1);
}

export function MetricsRow({ metrics: metricsProp }: MetricsRowProps = {}) {
  const metrics: RunMetrics = metricsProp ?? mockRunMetrics;

  return (
    <div className="grid grid-cols-4 gap-4">
      {/* Total Processed */}
      <div className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-5 border-l-4 border-l-[--border-default]">
        <p className="text-xs text-[--text-muted] uppercase tracking-wider mb-1">
          Total Processed
        </p>
        <p className="text-3xl font-semibold text-[--text-primary]">
          {metrics.total_processed}
        </p>
        <p className="text-xs text-[--text-muted] mt-1">leads in this run</p>
      </div>

      {/* High Fit Leads */}
      <div className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-5 border-l-4 border-l-[--color-success]">
        <p className="text-xs text-[--text-muted] uppercase tracking-wider mb-1">
          High Fit Leads
        </p>
        <p className="text-3xl font-semibold text-[--color-success]">
          {metrics.high_fit_leads}
        </p>
        <p className="text-xs text-[--text-muted] mt-1">{"score >= 70"}</p>
      </div>

      {/* Avg QA Score */}
      <div className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-5 border-l-4 border-l-[--accent-primary]">
        <p className="text-xs text-[--text-muted] uppercase tracking-wider mb-1">
          Avg QA Score
        </p>
        <p className="text-3xl font-semibold text-[--accent-primary]">
          {formatAverage(metrics.avg_qa_score)}
        </p>
        <p className="text-xs text-[--text-muted] mt-1">across {metrics.total_processed} leads</p>
      </div>

      {/* Total Run Cost */}
      <div className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-5 border-l-4 border-l-[--text-muted]">
        <p className="text-xs text-[--text-muted] uppercase tracking-wider mb-1">
          Total Run Cost
        </p>
        <p className="text-3xl font-semibold font-mono text-[--text-primary]">
          {metrics.total_cost}
        </p>
        <p className="text-xs text-[--text-muted] mt-1">
          {metrics.model_used} · {metrics.run_mode}
        </p>
      </div>
    </div>
  );
}
