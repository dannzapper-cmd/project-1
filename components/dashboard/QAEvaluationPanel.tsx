"use client";

import { useState } from "react";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import type { QAScores } from "@/lib/types";

interface QAEvaluationPanelProps {
  scores: QAScores;
}

function getScoreColor(score: number) {
  if (score >= 80) return "text-[--color-success]";
  if (score >= 60) return "text-[--color-warning]";
  return "text-[--color-error]";
}

function getProgressColor(score: number) {
  if (score >= 80) return "[&>div]:bg-[--color-success]";
  if (score >= 60) return "[&>div]:bg-[--color-warning]";
  return "[&>div]:bg-[--color-error]";
}

export function QAEvaluationPanel({ scores }: QAEvaluationPanelProps) {
  const metrics = [
    { label: "Personalization", value: scores.personalization },
    { label: "Evidence Coverage", value: scores.evidence_coverage },
    { label: "CTA Quality", value: scores.cta_quality },
    { label: "Tone Match", value: scores.tone_match },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="space-y-2">
            <p className="text-xs text-[--text-muted] uppercase tracking-wider">
              {metric.label}
            </p>
            <div className="flex items-baseline gap-1">
              <span className={`text-2xl font-semibold ${getScoreColor(metric.value)}`}>
                {metric.value}
              </span>
              <span className="text-xs text-[--text-muted]">/ 100</span>
            </div>
            <Progress
              value={metric.value}
              className={`h-1.5 bg-[--bg-overlay] ${getProgressColor(metric.value)}`}
            />
          </div>
        ))}
      </div>

      <Separator className="bg-[--border-subtle]" />

      {/* Hallucination Risk */}
      <div
        className={`rounded-lg px-4 py-3 ${
          scores.hallucination_risk === "Low"
            ? "bg-[--color-success-bg] border border-[--color-success]/20"
            : scores.hallucination_risk === "Medium"
            ? "bg-[--color-warning-bg] border border-[--color-warning]/20"
            : "bg-[--color-error-bg] border border-[--color-error]/20"
        }`}
      >
        <div className="flex items-center gap-2">
          <span
            className={
              scores.hallucination_risk === "Low"
                ? "text-[--color-success]"
                : scores.hallucination_risk === "Medium"
                ? "text-[--color-warning]"
                : "text-[--color-error]"
            }
          >
            {scores.hallucination_risk === "Low" ? "✓" : scores.hallucination_risk === "Medium" ? "⚠" : "✗"}
          </span>
          <span
            className={`text-sm font-medium ${
              scores.hallucination_risk === "Low"
                ? "text-[--color-success]"
                : scores.hallucination_risk === "Medium"
                ? "text-[--color-warning]"
                : "text-[--color-error]"
            }`}
          >
            Hallucination Risk: {scores.hallucination_risk}
          </span>
          <span className="text-xs text-[--text-secondary]">
            {scores.hallucination_risk === "Low"
              ? "— No unsupported claims detected"
              : scores.hallucination_risk === "Medium"
              ? "— Review claims before sending"
              : "— Contains potentially unsupported claims"}
          </span>
        </div>
      </div>

      {/* Recommendation */}
      <p
        className={`text-sm font-medium ${
          scores.recommendation === "Recommended for approval"
            ? "text-[--color-success]"
            : scores.recommendation === "Review carefully"
            ? "text-[--color-warning]"
            : "text-[--color-error]"
        }`}
      >
        QA Recommendation: {scores.recommendation}
      </p>
    </div>
  );
}
