"use client";

import type { AgentStatus, LeadDetail, TraceEntry } from "@/lib/types";

interface LeadAgentActivityPanelProps {
  detail: LeadDetail;
}

type StageKey =
  | "intake"
  | "research"
  | "qualifier"
  | "strategist"
  | "email-drafter"
  | "qa-evaluator";

interface LeadStage {
  key: StageKey;
  name: string;
  status: AgentStatus["status"];
  description: string;
  outputSummary: string;
}

const STAGE_DESCRIPTIONS: Record<StageKey, string> = {
  intake: "Normalize submitted lead rows and flag missing context.",
  research: "Collect company context, opportunity signals, and evidence.",
  qualifier: "Score ICP fit and assign lead priority.",
  strategist: "Turn fit and evidence into a sales angle.",
  "email-drafter": "Draft review-ready outreach from the available context.",
  "qa-evaluator": "Check draft quality, evidence coverage, and hallucination risk.",
};

function getStatusStyles(status: AgentStatus["status"]) {
  switch (status) {
    case "success":
      return {
        border: "border-[--color-success]/30",
        badge: "bg-[--color-success-bg] text-[--color-success]",
        icon: "✓",
        label: "Success",
      };
    case "warning":
      return {
        border: "border-[--color-warning]/30",
        badge: "bg-[--color-warning-bg] text-[--color-warning]",
        icon: "⚠",
        label: "Warning",
      };
    case "failed":
      return {
        border: "border-[--color-error]/30",
        badge: "bg-[--color-error-bg] text-[--color-error]",
        icon: "✗",
        label: "Failed",
      };
    case "running":
      return {
        border: "border-[--accent-secondary]/30",
        badge: "bg-[--accent-secondary]/10 text-[--accent-secondary]",
        icon: "●",
        label: "Running",
      };
    case "pending":
    default:
      return {
        border: "border-[--border-subtle]",
        badge: "bg-[--bg-overlay] text-[--text-muted]",
        icon: "○",
        label: "Pending",
      };
  }
}

function traceFor(detail: LeadDetail, names: string[]): TraceEntry | undefined {
  return detail.trace.find((entry) => names.includes(entry.agent));
}

function replaySafeStatus(
  status: AgentStatus["status"],
  runMode: LeadDetail["run_mode"],
): AgentStatus["status"] {
  return runMode === "Replay" && status === "running" ? "pending" : status;
}

function withSparseWarning(
  traceStatus: AgentStatus["status"] | undefined,
  sparse: boolean,
): AgentStatus["status"] {
  if (traceStatus === "failed") return "failed";
  if (traceStatus === "running") return "running";
  if (sparse) return "warning";
  return traceStatus ?? "success";
}

function missingLeadFields(detail: LeadDetail): string[] {
  const missing: string[] = [];
  if (!detail.website) missing.push("website");
  if (!detail.industry) missing.push("industry");
  if (!detail.country) missing.push("country");
  if (!detail.employees || detail.employees === "Unknown") missing.push("employee count");
  if (!detail.contact_name) missing.push("contact name");
  if (!detail.contact_role) missing.push("contact role");
  return missing;
}

function buildStages(detail: LeadDetail): LeadStage[] {
  const intakeWarnings = detail.intake_warnings ?? [];
  const missingFields = missingLeadFields(detail);
  const researchTrace = traceFor(detail, ["Research"]);
  const qualifierTrace = traceFor(detail, ["Qualifier", "Qualify"]);
  const strategistTrace = traceFor(detail, ["Strategist", "Strategize"]);
  const emailTrace = traceFor(detail, ["Email Drafter", "Draft"]);
  const qaTrace = traceFor(detail, ["QA Evaluator", "Evaluate"]);
  const qaMissing =
    detail.qa_score <= 0 &&
    detail.qa_scores.personalization <= 0 &&
    detail.qa_scores.evidence_coverage <= 0 &&
    detail.qa_scores.cta_quality <= 0 &&
    detail.qa_scores.tone_match <= 0;

  return [
    {
      key: "intake",
      name: "Intake",
      status: intakeWarnings.length > 0 || missingFields.length > 0 ? "warning" : "success",
      description: STAGE_DESCRIPTIONS.intake,
      outputSummary:
        intakeWarnings.length > 0
          ? `${intakeWarnings.length} intake warning${intakeWarnings.length === 1 ? "" : "s"} found.`
          : missingFields.length > 0
            ? `Sparse source fields: ${missingFields.slice(0, 3).join(", ")}.`
            : "Lead source fields are present for review.",
    },
    {
      key: "research",
      name: "Research",
      status: withSparseWarning(
        researchTrace?.status,
        !detail.company_summary || detail.evidence_cards.length === 0,
      ),
      description: STAGE_DESCRIPTIONS.research,
      outputSummary:
        detail.evidence_cards.length > 0
          ? `${detail.evidence_cards.length} evidence cards and ${detail.opportunity_signals.length} opportunity signals available.`
          : "No evidence cards are available for this lead.",
    },
    {
      key: "qualifier",
      name: "Qualifier",
      status: withSparseWarning(
        qualifierTrace?.status,
        detail.fit_reasons.length === 0 || detail.low_evidence === true,
      ),
      description: STAGE_DESCRIPTIONS.qualifier,
      outputSummary:
        detail.fit_reasons.length > 0
          ? `Fit score ${detail.fit_score}; priority ${detail.priority}; ${detail.fit_risks.length} risk${detail.fit_risks.length === 1 ? "" : "s"} noted.`
          : "No fit reasons are available for this lead.",
    },
    {
      key: "strategist",
      name: "Strategist",
      status: withSparseWarning(strategistTrace?.status, !detail.sales_angle),
      description: STAGE_DESCRIPTIONS.strategist,
      outputSummary: detail.sales_angle
        ? `Sales angle: ${detail.sales_angle}`
        : "No sales angle is available for this lead.",
    },
    {
      key: "email-drafter",
      name: "Email Drafter",
      status: withSparseWarning(emailTrace?.status, !detail.email_subject || !detail.email_body),
      description: STAGE_DESCRIPTIONS["email-drafter"],
      outputSummary: detail.email_subject
        ? `Draft subject: ${detail.email_subject}`
        : "No email draft is available for this lead.",
    },
    {
      key: "qa-evaluator",
      name: "QA Evaluator",
      status: withSparseWarning(
        qaTrace?.status,
        qaMissing ||
          detail.qa_scores.hallucination_risk !== "Low" ||
          detail.qa_scores.recommendation !== "Recommended for approval",
      ),
      description: STAGE_DESCRIPTIONS["qa-evaluator"],
      outputSummary: qaMissing
        ? "No QA score is available for this lead."
        : `QA score ${detail.qa_score}; ${detail.qa_scores.recommendation}; hallucination risk ${detail.qa_scores.hallucination_risk}.`,
    },
  ];
}

export function LeadAgentActivityPanel({ detail }: LeadAgentActivityPanelProps) {
  const stages = buildStages(detail);
  const replayMode = detail.run_mode === "Replay";

  return (
    <section className="surface-card rounded-lg p-4">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono">
            Agent trace
          </h3>
          <p className="text-xs text-[--text-muted] mt-1">
            Which agent produced each result — validation, evidence, fit,
            strategy, draft, and QA for this lead.
          </p>
        </div>
        {replayMode && (
          <span className="rounded-full border border-[--color-warning]/30 bg-[--color-warning-bg] px-2 py-0.5 text-[10px] font-medium text-[--color-warning]">
            Replay/demo mode
          </span>
        )}
      </div>

      <div className="space-y-3">
        {stages.map((stage) => {
          const styles = getStatusStyles(
            replaySafeStatus(stage.status, detail.run_mode),
          );
          return (
            <div
              key={stage.key}
              className={`border ${styles.border} rounded-lg bg-[--bg-elevated] p-3`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-[--text-primary]">
                    {stage.name}
                  </p>
                  <p className="text-xs text-[--text-muted] mt-1">
                    {stage.description}
                  </p>
                </div>
                <span
                  className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${styles.badge}`}
                >
                  <span>{styles.icon}</span>
                  {styles.label}
                </span>
              </div>
              <p className="text-[10px] uppercase tracking-wide text-[--text-muted] mt-2 mb-1">
                Output summary
              </p>
              <p className="text-xs text-[--text-secondary] leading-relaxed">
                {stage.outputSummary}
              </p>
            </div>
          );
        })}
      </div>

      {replayMode && (
        <p className="text-xs text-[--text-muted] mt-3">
          Replay/demo mode: statuses describe saved outputs from this run, not
          live execution.
        </p>
      )}
    </section>
  );
}
