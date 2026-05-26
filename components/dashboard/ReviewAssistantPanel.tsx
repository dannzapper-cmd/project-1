"use client";

import { useMemo, useState } from "react";
import type { LeadDetail } from "@/lib/types";

interface ReviewAssistantPanelProps {
  detail: LeadDetail;
}

type QuestionId =
  | "priority"
  | "sales-angle"
  | "missing-data"
  | "confidence"
  | "review-check"
  | "qa-score";

interface Question {
  id: QuestionId;
  label: string;
}

const QUESTIONS: Question[] = [
  {
    id: "priority",
    label: "Why is this lead high / medium / low priority?",
  },
  {
    id: "sales-angle",
    label: "What is the recommended sales angle?",
  },
  {
    id: "missing-data",
    label: "What data is missing for this lead?",
  },
  {
    id: "confidence",
    label: "What would improve confidence?",
  },
  {
    id: "review-check",
    label: "What should the reviewer check before approving?",
  },
  {
    id: "qa-score",
    label: "What does the QA score mean for this lead?",
  },
];

const FALLBACK = "Not enough evidence in this run to answer that confidently.";

function hasText(value: string | null | undefined): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function listFirst(items: string[], count: number): string {
  return items.slice(0, count).join("; ");
}

function missingLeadFields(detail: LeadDetail): string[] {
  const missing: string[] = [];
  if (!hasText(detail.website)) missing.push("website");
  if (!hasText(detail.industry)) missing.push("industry");
  if (!hasText(detail.country)) missing.push("country");
  if (!hasText(detail.employees) || detail.employees === "Unknown") {
    missing.push("employee count");
  }
  if (!hasText(detail.contact_name)) missing.push("contact name");
  if (!hasText(detail.contact_role)) missing.push("contact role");
  if (!hasText(detail.company_summary)) missing.push("company summary");
  if (detail.evidence_cards.length === 0) missing.push("evidence cards");
  if (!hasText(detail.sales_angle)) missing.push("sales angle");
  if (!hasText(detail.email_subject) || !hasText(detail.email_body)) {
    missing.push("email draft");
  }
  return missing;
}

function lowConfidenceEvidence(detail: LeadDetail): string[] {
  return detail.evidence_cards
    .filter((card) => card.confidence !== "High")
    .map((card) => `${card.headline} (${card.confidence})`);
}

function qaAvailable(detail: LeadDetail): boolean {
  return !(
    detail.qa_score <= 0 &&
    detail.qa_scores.personalization <= 0 &&
    detail.qa_scores.evidence_coverage <= 0 &&
    detail.qa_scores.cta_quality <= 0 &&
    detail.qa_scores.tone_match <= 0
  );
}

function answerPriority(detail: LeadDetail): string {
  if (
    !hasText(detail.priority) ||
    !Number.isFinite(detail.fit_score) ||
    detail.fit_reasons.length === 0
  ) {
    return FALLBACK;
  }

  const risks = detail.fit_risks.length
    ? ` Risks to review: ${listFirst(detail.fit_risks, 2)}.`
    : "";

  return `${detail.company} is marked ${detail.priority} priority with a fit score of ${detail.fit_score}. The run cites: ${listFirst(detail.fit_reasons, 3)}.${risks}`;
}

function answerSalesAngle(detail: LeadDetail): string {
  if (!hasText(detail.sales_angle)) return FALLBACK;

  const support = [
    hasText(detail.pain_hypothesis)
      ? `Pain hypothesis: ${detail.pain_hypothesis}.`
      : null,
    hasText(detail.core_message) ? `Core message: ${detail.core_message}.` : null,
  ].filter(hasText);

  return support.length
    ? `${detail.sales_angle} ${support.join(" ")}`
    : detail.sales_angle;
}

function answerMissingData(detail: LeadDetail): string {
  const missing = missingLeadFields(detail);
  const warnings = detail.intake_warnings ?? [];
  const parts: string[] = [];

  if (missing.length > 0) {
    parts.push(`Missing or sparse fields: ${missing.join(", ")}.`);
  }
  if (warnings.length > 0) {
    parts.push(`Intake warnings: ${listFirst(warnings, 3)}.`);
  }
  if (detail.low_evidence) {
    parts.push("This run also flags the lead as low evidence.");
  }

  return parts.length > 0
    ? parts.join(" ")
    : "No obvious missing lead fields are flagged in this run. Reviewer should still verify the evidence before approving.";
}

function answerConfidence(detail: LeadDetail): string {
  const improvements: string[] = [];
  const lowEvidence = lowConfidenceEvidence(detail);

  if (detail.low_evidence) {
    improvements.push("more evidence for the company and buyer context");
  }
  if (lowEvidence.length > 0) {
    improvements.push(`stronger sources for ${listFirst(lowEvidence, 2)}`);
  }
  if (detail.fit_risks.length > 0) {
    improvements.push(`resolving fit risks: ${listFirst(detail.fit_risks, 2)}`);
  }
  if (detail.pain_confidence !== "High" && hasText(detail.pain_hypothesis)) {
    improvements.push(`validating the pain hypothesis (${detail.pain_confidence} confidence)`);
  }
  if (missingLeadFields(detail).length > 0) {
    improvements.push(`filling missing fields: ${missingLeadFields(detail).slice(0, 3).join(", ")}`);
  }

  return improvements.length > 0
    ? `Confidence would improve with ${improvements.join("; ")}.`
    : "Confidence is relatively strong in this run; the main improvement would be reviewer validation that the cited evidence still matches the lead before approval.";
}

function answerReviewCheck(detail: LeadDetail): string {
  const checks: string[] = [];

  if (detail.fit_risks.length > 0) {
    checks.push(`fit risks (${listFirst(detail.fit_risks, 2)})`);
  }
  if (qaAvailable(detail)) {
    checks.push(
      `QA recommendation (${detail.qa_scores.recommendation}) and hallucination risk (${detail.qa_scores.hallucination_risk})`,
    );
  }
  if (detail.evidence_cards.length > 0) {
    checks.push("the evidence cards used in the email");
  }
  if (hasText(detail.email_subject)) {
    checks.push(`draft subject "${detail.email_subject}"`);
  }
  if (hasText(detail.likely_objection)) {
    checks.push(`likely objection "${detail.likely_objection}"`);
  }

  return checks.length > 0
    ? `Before approving, check ${checks.join("; ")}.`
    : FALLBACK;
}

function answerQaScore(detail: LeadDetail): string {
  if (!qaAvailable(detail)) return FALLBACK;

  const scoreMeaning =
    detail.qa_score >= 80
      ? "a stronger review signal"
      : detail.qa_score >= 60
        ? "a moderate review signal"
        : "a weak review signal";

  return `The QA score is ${detail.qa_score}, which is ${scoreMeaning} for this lead. Subscores are personalization ${detail.qa_scores.personalization}, evidence coverage ${detail.qa_scores.evidence_coverage}, CTA quality ${detail.qa_scores.cta_quality}, and tone match ${detail.qa_scores.tone_match}. Recommendation: ${detail.qa_scores.recommendation}; hallucination risk: ${detail.qa_scores.hallucination_risk}.`;
}

function buildAnswer(questionId: QuestionId, detail: LeadDetail): string {
  switch (questionId) {
    case "priority":
      return answerPriority(detail);
    case "sales-angle":
      return answerSalesAngle(detail);
    case "missing-data":
      return answerMissingData(detail);
    case "confidence":
      return answerConfidence(detail);
    case "review-check":
      return answerReviewCheck(detail);
    case "qa-score":
      return answerQaScore(detail);
  }
}

export function ReviewAssistantPanel({ detail }: ReviewAssistantPanelProps) {
  const [selectedQuestion, setSelectedQuestion] = useState<QuestionId>("priority");
  const selected = QUESTIONS.find((question) => question.id === selectedQuestion) ?? QUESTIONS[0];
  const answer = useMemo(
    () => buildAnswer(selectedQuestion, detail),
    [selectedQuestion, detail],
  );

  return (
    <section className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-[--text-primary]">
            Review assistant
          </h3>
          <p className="text-xs text-[--text-muted] mt-1">
            Ask about this lead
          </p>
        </div>
        <span className="rounded-full border border-[--border-subtle] bg-[--bg-overlay] px-2 py-0.5 text-[10px] font-medium text-[--text-muted]">
          Grounded in this run&apos;s available context
        </span>
      </div>

      <p className="text-xs text-[--text-muted] mt-3">
        Answers are based on available context from this run only. They are not
        live research or guaranteed recommendations.
      </p>

      <div className="grid grid-cols-1 gap-2 mt-4">
        {QUESTIONS.map((question) => (
          <button
            key={question.id}
            type="button"
            onClick={() => setSelectedQuestion(question.id)}
            className={`rounded-lg border px-3 py-2 text-left text-xs transition-colors ${
              selectedQuestion === question.id
                ? "border-[--accent-primary] bg-[--accent-primary]/10 text-[--text-primary]"
                : "border-[--border-subtle] bg-[--bg-elevated] text-[--text-secondary] hover:text-[--text-primary]"
            }`}
          >
            {question.label}
          </button>
        ))}
      </div>

      <div className="mt-4 rounded-lg border border-[--border-subtle] bg-[--bg-elevated] p-3">
        <p className="text-xs font-medium text-[--text-primary]">
          {selected.label}
        </p>
        <p className="text-sm text-[--text-secondary] leading-relaxed mt-2">
          {answer}
        </p>
      </div>
    </section>
  );
}
