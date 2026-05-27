"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { ExternalLink, ChevronDown, ChevronUp } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { QAEvaluationPanel } from "./QAEvaluationPanel";
import { TraceTimeline } from "./TraceTimeline";
import { HumanReviewControls } from "./HumanReviewControls";
import { ProfileSalesAnglesCard } from "./ProfileSalesAnglesCard";
import { LeadAgentActivityPanel } from "./LeadAgentActivityPanel";
import { LiveResearchPanel } from "./LiveResearchPanel";
import { ReviewAssistantPanel } from "./ReviewAssistantPanel";
import { downloadLeadCsv } from "@/lib/export/lead-export";
import type { B2BProfilePack } from "@/lib/b2b-profile-packs";
import { mockLeadDetail } from "@/lib/mock-data";
import type { Lead, LeadDetail, EvidenceCard } from "@/lib/types";

interface LeadDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  lead: Lead | null;
  /**
   * Optional pre-resolved detail for `lead`. When provided, the
   * drawer renders it directly. When `null`/`undefined`, the
   * drawer falls back to `mockLeadDetail` merged with the
   * selected `lead` — the original Phase 6.x mock-only behavior.
   * Phase 7.1 supplies this from
   * `useDashboardData().getLeadDetail(leadId)` so the drawer does
   * NOT issue a second backend fetch when DATA_SOURCE === "api".
   */
  detail?: LeadDetail | null;
  onStatusChange: (leadId: string, status: Lead["status"]) => void;
  profilePack?: B2BProfilePack;
}

function getFitScoreStyles(score: number) {
  if (score >= 70) {
    return {
      bg: "bg-[--color-success]/20",
      border: "border-[--color-success]/30",
      text: "text-[--color-success]",
      label: "HIGH FIT",
    };
  }
  if (score >= 40) {
    return {
      bg: "bg-[--color-warning]/20",
      border: "border-[--color-warning]/30",
      text: "text-[--color-warning]",
      label: "MEDIUM FIT",
    };
  }
  return {
    bg: "bg-[--color-error]/20",
    border: "border-[--color-error]/30",
    text: "text-[--color-error]",
    label: "LOW FIT",
  };
}

function getConfidenceColor(confidence: EvidenceCard["confidence"]) {
  switch (confidence) {
    case "High":
      return "text-[--color-success]";
    case "Medium":
      return "text-[--color-warning]";
    case "Low":
      return "text-[--text-muted]";
  }
}

export function LeadDetailDrawer({
  isOpen,
  onClose,
  lead,
  detail: detailProp,
  onStatusChange,
  profilePack,
}: LeadDetailDrawerProps) {
  const [showPersonalizationNotes, setShowPersonalizationNotes] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Resolution order:
  //   1. Caller-provided `detailProp` (Phase 7.1 API mode, or any
  //      consumer that has already resolved the full LeadDetail).
  //   2. Mock fallback: shallow-merge `mockLeadDetail` with the
  //      selected `lead` (the original Phase 6.x behavior).
  // The mock fallback preserves the drawer's visual output when
  // DATA_SOURCE === "mock" or when a consumer does not pass
  // `detail` at all.
  const detail: LeadDetail =
    detailProp ?? (lead ? { ...mockLeadDetail, ...lead } : mockLeadDetail);
  const fitStyles = getFitScoreStyles(detail.fit_score);
  const intakeWarnings = detail.intake_warnings ?? [];

  const handleStatusChange = (status: Lead["status"]) => {
    if (lead) {
      onStatusChange(lead.id, status);
    }
  };

  // Block 7.4: trigger a local CSV download for the currently
  // reviewed lead. The button in HumanReviewControls only invokes
  // this when status !== "Pending Review", but we also guard here
  // so a misbehaving caller cannot export an unreviewed lead.
  const handleExportLead = () => {
    if (!lead) return;
    if (lead.status === "Pending Review") return;
    downloadLeadCsv(detail, lead.status);
  };

  return (
<Sheet
  open={isOpen}
  onOpenChange={(open) => {
    if (!open) onClose();
  }}
>
  <SheetContent
    side="right"
    className="
      z-[100]
      w-full
      sm:max-w-[620px]
      border-l
      border-[--border-default]
      !bg-[--bg-elevated]
      p-0
      text-[--text-primary]
      shadow-[-8px_0_32px_rgba(15,23,42,0.12)]
      flex
      flex-col
    "
  >
        {/* Sticky Header */}
        <div className="bg-[--bg-elevated] border-b border-[--border-default] px-6 py-4 sticky top-0 z-10">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold text-[--text-primary]">{detail.company}</h2>
              <div className="flex items-center gap-1 text-xs text-[--text-muted] mt-1">
                <span>{detail.industry}</span>
                <span>·</span>
                <span>{detail.country}</span>
                <span>·</span>
                <span>{detail.employees}</span>
                <span>·</span>
                <span>{detail.contact_role}</span>
              </div>
            </div>
            <div className={`flex flex-col items-center justify-center w-20 h-20 rounded-xl ${fitStyles.bg} border ${fitStyles.border}`}>
              <span className={`text-3xl font-semibold ${fitStyles.text}`}>{detail.fit_score}</span>
              <span className={`text-[10px] font-mono uppercase ${fitStyles.text}`}>{fitStyles.label}</span>
            </div>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-6 py-6 space-y-8">
            {/* Lead Information */}
            <section>
              <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono mb-4">Lead</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-[--text-muted]">Company</p>
                  <p className="text-sm text-[--text-primary]">{detail.company}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Website</p>
                  {detail.website ? (
                    <a href={`https://${detail.website}`} target="_blank" rel="noopener noreferrer" className="text-sm text-[--accent-primary] hover:underline inline-flex items-center gap-1">
                      {detail.website}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    <p className="text-sm text-[--text-muted]">Missing website</p>
                  )}
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Industry</p>
                  <p className="text-sm text-[--text-primary]">{detail.industry}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Country</p>
                  <p className="text-sm text-[--text-primary]">{detail.country}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Employees</p>
                  <p className="text-sm text-[--text-primary]">{detail.employees}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Contact</p>
                  <p className="text-sm text-[--text-primary]">{detail.contact_name}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Role</p>
                  <p className="text-sm text-[--text-primary]">{detail.contact_role}</p>
                </div>
              </div>
            </section>

            <Separator className="bg-[--border-subtle]" />

            {intakeWarnings.length > 0 && (
              <>
                <section className="bg-[--color-warning-bg]/30 border border-[--color-warning]/30 rounded-lg p-4">
                  <h3 className="text-xs uppercase tracking-widest text-[--color-warning] font-mono mb-3">
                    Intake warnings
                  </h3>
                  <ul className="space-y-1">
                    {intakeWarnings.map((warning, idx) => (
                      <li key={idx} className="text-xs text-[--text-secondary]">
                        - {warning}
                      </li>
                    ))}
                  </ul>
                </section>
                <Separator className="bg-[--border-subtle]" />
              </>
            )}

            {detail.low_evidence && profilePack && (
              <>
                <section className="bg-[--color-warning-bg]/30 border border-[--color-warning]/30 rounded-lg p-4">
                  <h3 className="text-xs uppercase tracking-widest text-[--color-warning] font-mono mb-2">
                    Low evidence
                  </h3>
                  <p className="text-xs text-[--text-secondary]">
                    {profilePack.lowEvidenceWarning}
                  </p>
                </section>
                <Separator className="bg-[--border-subtle]" />
              </>
            )}

            {profilePack && (
              <>
                <ProfileSalesAnglesCard pack={profilePack} />
                <Separator className="bg-[--border-subtle]" />
              </>
            )}

            {/* Company Context */}
            <section>
              <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono mb-4">Company Context</h3>
              <p className="text-sm text-[--text-secondary] leading-relaxed">{detail.company_summary}</p>
              <div className="flex flex-wrap gap-2 mt-4">
                {detail.opportunity_signals.map((signal, idx) => (
                  <span key={idx} className="bg-[--bg-overlay] border border-[--border-default] rounded-full px-3 py-1 text-xs text-[--accent-secondary]">
                    {signal}
                  </span>
                ))}
              </div>
            </section>

            <Separator className="bg-[--border-subtle]" />

            {/* Evidence */}
            <section>
              <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono mb-4">Evidence used</h3>
              <div className="grid grid-cols-2 gap-3">
                {detail.evidence_cards.map((card) => (
                  <div key={card.id} className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-4 relative">
                    <span className="absolute top-3 right-3 text-[10px] text-[--text-muted] bg-[--bg-overlay] px-2 py-0.5 rounded-full">
                      {card.source_type}
                    </span>
                    <p className="text-sm font-medium text-[--text-primary] pr-20">{card.headline}</p>
                    <p className="text-xs text-[--text-secondary] mt-1">{card.description}</p>
                    <div className="flex items-center gap-1 mt-2">
                      <span className={getConfidenceColor(card.confidence)}>●</span>
                      <span className="text-xs text-[--text-muted]">{card.confidence} confidence</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <Separator className="bg-[--border-subtle]" />

            {/* Qualification */}
            <section>
              <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono mb-4">Qualification</h3>
              <div className="flex gap-6">
                <div className="flex flex-col items-center">
                  <div className={`w-24 h-24 rounded-full ${fitStyles.bg} border-4 ${fitStyles.border} flex items-center justify-center`}>
                    <span className={`text-5xl font-bold ${fitStyles.text}`}>{detail.fit_score}</span>
                  </div>
                  <span className={`mt-2 text-xs font-mono uppercase px-2 py-1 rounded-full ${fitStyles.bg} ${fitStyles.text}`}>
                    {fitStyles.label}
                  </span>
                </div>
                <div className="flex-1">
                  <p className="text-xs text-[--text-muted] mb-2">Why this score</p>
                  <ul className="space-y-1">
                    {detail.fit_reasons.map((reason, idx) => (
                      <li key={idx} className="text-sm text-[--text-secondary] flex items-start gap-2">
                        <span className="text-[--color-success]">✓</span>
                        {reason}
                      </li>
                    ))}
                  </ul>
                  <p className="text-xs text-[--text-muted] mt-4 mb-2">Risks</p>
                  <ul className="space-y-1">
                    {detail.fit_risks.map((risk, idx) => (
                      <li key={idx} className="text-sm text-[--text-secondary] flex items-start gap-2">
                        <span className="text-[--color-warning]">⚠</span>
                        {risk}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>

            <Separator className="bg-[--border-subtle]" />

            {/* Strategy */}
            <section>
              <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono mb-4">Strategy</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <p className="text-xs text-[--text-muted] mb-2">Pain Hypothesis</p>
                  <p className="text-sm text-[--text-secondary]">{detail.pain_hypothesis}</p>
                  <span className={`inline-block mt-2 text-xs px-2 py-1 rounded-full ${
                    detail.pain_confidence === "High"
                      ? "bg-[--color-success-bg] text-[--color-success]"
                      : detail.pain_confidence === "Medium"
                      ? "bg-[--color-warning-bg] text-[--color-warning]"
                      : "bg-[--bg-overlay] text-[--text-muted]"
                  }`}>
                    {detail.pain_confidence} Confidence
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium text-[--text-primary] mb-2">{detail.core_message}</p>
                  <p className="text-sm text-[--text-secondary]">{detail.sales_angle}</p>
                  <p className="text-xs text-[--text-muted] mt-3">
                    <span className="font-medium">Prepare for:</span> {detail.likely_objection}
                  </p>
                </div>
              </div>
            </section>

            <Separator className="bg-[--border-subtle]" />

            {/* Email Draft */}
            <section>
              <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono mb-4">Email Draft</h3>
              <div className="bg-[--bg-elevated] border border-[--border-default] rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-[--border-subtle]">
                  <span className="text-xs text-[--text-muted]">Subject: </span>
                  <span className="text-sm font-medium text-[--text-primary]">{detail.email_subject}</span>
                </div>
                <div className="px-4 py-4">
                  <p className="text-sm text-[--text-secondary] leading-relaxed whitespace-pre-line">
                    {detail.email_body}
                  </p>
                </div>
              </div>

              {/* Personalization Notes Toggle */}
              <button
                onClick={() => setShowPersonalizationNotes(!showPersonalizationNotes)}
                className="flex items-center gap-2 mt-3 text-xs text-[--text-muted] hover:text-[--text-secondary] transition-colors"
              >
                <span>Why this email was written this way</span>
                {showPersonalizationNotes ? (
                  <ChevronUp className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
              </button>
              {showPersonalizationNotes && (
                <ul className="mt-2 space-y-1">
                  {detail.personalization_notes.map((note, idx) => (
                    <li key={idx} className="text-xs text-[--text-muted] flex items-start gap-2">
                      <span>·</span>
                      {note}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <Separator className="bg-[--border-subtle]" />

            {/* Quality Evaluation */}
            <section>
              <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono mb-4">Quality Evaluation</h3>
              <QAEvaluationPanel scores={detail.qa_scores} />
            </section>

            <Separator className="bg-[--border-subtle]" />

            <ReviewAssistantPanel detail={detail} />

            <Separator className="bg-[--border-subtle]" />

            <LiveResearchPanel lead={detail} />

            <Separator className="bg-[--border-subtle]" />

            {/* Run Details */}
            <section>
              <h3 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono mb-4">Run Details</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-[--text-muted]">Est. Cost</p>
                  <p className="text-sm font-mono text-[--text-primary]">{detail.est_cost}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Total Latency</p>
                  <p className="text-sm font-mono text-[--text-primary]">{detail.est_total_latency}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Model Used</p>
                  <p className="text-sm font-mono text-[--text-primary]">{detail.model_used}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Run Mode</p>
                  <p className="text-sm font-mono text-[--text-primary]">{detail.run_mode}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Agent Steps</p>
                  <p className="text-sm font-mono text-[--text-primary]">{detail.agent_steps}</p>
                </div>
                <div>
                  <p className="text-xs text-[--text-muted]">Est. Tokens</p>
                  <p className="text-sm font-mono text-[--text-primary]">{detail.est_tokens.toLocaleString()}</p>
                </div>
              </div>
            </section>

            <Separator className="bg-[--border-subtle]" />

            <LeadAgentActivityPanel detail={detail} />

            <Separator className="bg-[--border-subtle]" />

            {/* Agent Trace */}
            <section>
              <TraceTimeline trace={detail.trace} />
            </section>
          </div>
        </div>

        {/* Sticky Footer */}
        <HumanReviewControls
          status={lead?.status || detail.status}
          onStatusChange={handleStatusChange}
          onExportLead={handleExportLead}
        />
      </SheetContent>
    </Sheet>
  );
}
