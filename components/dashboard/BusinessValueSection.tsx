"use client";

import { useMemo } from "react";
import { TrendingUp } from "lucide-react";

import {
  MANUAL_MINUTES_RANGE_LABEL,
  computeBusinessValueMetrics,
} from "@/lib/metrics/business-value";
import type { Lead, RunMetrics } from "@/lib/types";

interface BusinessValueSectionProps {
  metrics: RunMetrics;
  leads?: Lead[];
}

export function BusinessValueSection({
  metrics,
  leads = [],
}: BusinessValueSectionProps) {
  const value = useMemo(
    () => computeBusinessValueMetrics(metrics, leads),
    [metrics, leads],
  );

  if (value.totalProcessed === 0) {
    return null;
  }

  return (
    <section
      aria-labelledby="business-value-heading"
      className="bg-[--bg-surface] border border-[--border-default] rounded-lg p-5 space-y-4"
    >
      <div className="flex items-start gap-3">
        <TrendingUp
          className="h-5 w-5 text-[--accent-primary] mt-0.5 shrink-0"
          aria-hidden
        />
        <div>
          <h2
            id="business-value-heading"
            className="text-lg font-semibold text-[--text-primary]"
          >
            Business value from this run
          </h2>
          <p className="text-sm text-[--text-muted] mt-1">
            Illustrative estimates from run metrics — not guaranteed ROI or revenue.
          </p>
        </div>
      </div>

      <p className="text-sm text-[--text-secondary]">{value.valueNarrative}</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          label="Est. manual time avoided"
          value={`~${value.estimatedManualHoursSaved}h`}
          hint={`At ${MANUAL_MINUTES_RANGE_LABEL} / lead`}
        />
        <MetricCard
          label="Review-ready leads"
          value={String(value.estimatedReviewReadyLeads)}
          hint="Fit ≥ 70 and QA ≥ 70"
        />
        <MetricCard
          label="High-fit ratio"
          value={
            value.highFitRatioPercent !== null
              ? `${value.highFitRatioPercent}%`
              : "—"
          }
          hint={`${value.highFitLeads} of ${value.totalProcessed} leads`}
        />
        <MetricCard
          label="Cost per lead"
          value={value.costPerLeadLabel}
          hint={`Run total: ${value.totalRunCostLabel}`}
        />
      </div>

      <div className="grid md:grid-cols-2 gap-3 text-sm">
        <div className="bg-[--bg-elevated] rounded-lg p-3 border border-[--border-subtle]">
          <p className="text-xs text-[--text-muted] uppercase tracking-wide mb-1">
            Pipeline quality
          </p>
          <p className="text-[--text-secondary]">{value.pipelineQualitySummary}</p>
        </div>
        <div className="bg-[--bg-elevated] rounded-lg p-3 border border-[--border-subtle]">
          <p className="text-xs text-[--text-muted] uppercase tracking-wide mb-1">
            Priority mix
          </p>
          <p className="text-[--text-secondary]">
            High {value.priorityBreakdown.high} · Medium{" "}
            {value.priorityBreakdown.medium} · Low {value.priorityBreakdown.low}
          </p>
          {value.avgQaScore !== null && (
            <p className="text-xs text-[--text-muted] mt-2">
              Avg QA score: {value.avgQaScore.toFixed(0)}
            </p>
          )}
        </div>
      </div>

      <p className="text-xs text-[--text-muted] border-t border-[--border-subtle] pt-3">
        {value.assumptionsNote}
      </p>
    </section>
  );
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="bg-[--bg-elevated] rounded-lg p-3 border border-[--border-subtle]">
      <p className="text-xs text-[--text-muted] uppercase tracking-wide">{label}</p>
      <p className="text-xl font-semibold text-[--text-primary] mt-1">{value}</p>
      <p className="text-xs text-[--text-muted] mt-1">{hint}</p>
    </div>
  );
}
