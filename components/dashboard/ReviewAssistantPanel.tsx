"use client";

/**
 * Block 10D + Block 10G — Contextual Lead Review Assistant.
 *
 * Two coexisting modes inside one panel:
 *
 * - Deterministic mode (Block 10D, always available): the predefined
 *   question buttons synthesize an answer locally from the lead's
 *   already-loaded context. No network calls, no model. Works even
 *   when the live LLM assistant is disabled.
 *
 * - Live LLM mode (Block 10G, opt-in): an optional text input lets
 *   the reviewer ask a free-form question. Submitting POSTs the
 *   small lead-context payload to `/api/assistant/lead-question`.
 *   The backend returns a structured response (`status: ok |
 *   disabled | unavailable | rate_limited | insufficient_context |
 *   timeout | provider_error | invalid_question`). The component
 *   renders the matching state from the response shape — it never
 *   throws on a non-`ok` status.
 *
 * Hard rules baked into the UI:
 *   - The live assistant never fires on mount.
 *   - The live assistant never fires while the user is typing.
 *   - No chat history is persisted (no localStorage, no DB).
 *   - The live answer is shown alongside grounding metadata and a
 *     short "used context fields" list so the reviewer can see what
 *     the model was given.
 *   - The deterministic buttons always remain functional even when
 *     the live mode is disabled / unavailable / rate limited.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Send, Sparkles } from "lucide-react";

import {
  ApiError,
  postAssistantLeadQuestion,
} from "@/lib/api/client";
import type {
  AssistantLeadContextIn,
  AssistantLiveResearchSnippetIn,
  AssistantRequest,
  AssistantResponse,
} from "@/lib/api/types";
import type { LeadDetail } from "@/lib/types";
import {
  DEMO_ACCESS_REQUIRED_MESSAGE,
  apiDetail,
} from "@/lib/intake/intake-errors";

interface ReviewAssistantPanelProps {
  detail: LeadDetail;
  /**
   * Optional injection point for tests. Production callers leave
   * undefined and the component uses the default API client.
   */
  postAssistantQuestion?: typeof postAssistantLeadQuestion;
}

type QuestionId =
  | "evidence"
  | "priority"
  | "sales-angle"
  | "email-strength"
  | "review-check"
  | "qa-score";

interface Question {
  id: QuestionId;
  label: string;
}

interface QuestionGroup {
  lens: string;
  questions: Question[];
}

const QUESTION_GROUPS: QuestionGroup[] = [
  {
    lens: "Research",
    questions: [
      { id: "evidence", label: "What evidence supports this lead?" },
    ],
  },
  {
    lens: "Qualifier",
    questions: [{ id: "priority", label: "Why this priority?" }],
  },
  {
    lens: "Strategist",
    questions: [{ id: "sales-angle", label: "What angle should we use?" }],
  },
  {
    lens: "Email Drafter",
    questions: [{ id: "email-strength", label: "Is the email strong enough?" }],
  },
  {
    lens: "QA Evaluator",
    questions: [
      { id: "review-check", label: "What should I review before approving?" },
      { id: "qa-score", label: "What does the QA score mean?" },
    ],
  },
];

const ALL_QUESTIONS: Question[] = QUESTION_GROUPS.flatMap((g) => g.questions);

// Mirrors LLM_ASSISTANT_MAX_QUESTION_CHARS default on the backend.
// The backend re-enforces this independently — this is purely a UX
// guardrail.
const QUESTION_CHAR_LIMIT = 300;

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

function qaAvailable(detail: LeadDetail): boolean {
  return !(
    detail.qa_score <= 0 &&
    detail.qa_scores.personalization <= 0 &&
    detail.qa_scores.evidence_coverage <= 0 &&
    detail.qa_scores.cta_quality <= 0 &&
    detail.qa_scores.tone_match <= 0
  );
}

function answerEvidence(detail: LeadDetail): string {
  if (detail.evidence_cards.length === 0) {
    return "No evidence cards are in this run yet. Run the pipeline or Live Research to add company context before approving.";
  }
  const headlines = detail.evidence_cards
    .slice(0, 4)
    .map((card) => `${card.headline} (${card.confidence})`);
  return `Evidence used in this run: ${headlines.join("; ")}. Review each card in Evidence used before approving outreach.`;
}

function answerEmailStrength(detail: LeadDetail): string {
  if (!hasText(detail.email_subject) || !hasText(detail.email_body)) {
    return FALLBACK;
  }
  const parts: string[] = [
    `Subject: "${detail.email_subject}".`,
  ];
  if (qaAvailable(detail)) {
    parts.push(
      `QA Evaluator scored this draft ${detail.qa_score} with recommendation ${detail.qa_scores.recommendation}.`,
    );
  }
  if (detail.personalization_notes?.length) {
    parts.push(
      `Review notes: ${listFirst(detail.personalization_notes, 2)}.`,
    );
  }
  return parts.join(" ");
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
    case "evidence":
      return answerEvidence(detail);
    case "priority":
      return answerPriority(detail);
    case "sales-angle":
      return answerSalesAngle(detail);
    case "email-strength":
      return answerEmailStrength(detail);
    case "review-check":
      return answerReviewCheck(detail);
    case "qa-score":
      return answerQaScore(detail);
  }
}

// --------------------------------------------------------------------------- //
// Live LLM context builder                                                    //
// --------------------------------------------------------------------------- //

function buildLeadContext(detail: LeadDetail): AssistantLeadContextIn {
  const missing = missingLeadFields(detail);
  const qa = qaAvailable(detail)
    ? {
        qa_score: Number.isFinite(detail.qa_score) ? detail.qa_score : null,
        hallucination_risk: detail.qa_scores.hallucination_risk,
        recommendation: detail.qa_scores.recommendation,
        notes: [] as string[],
      }
    : null;

  return {
    company_name: detail.company || null,
    industry: detail.industry || null,
    country: detail.country || null,
    website: detail.website || null,
    employees: detail.employees || null,
    contact_role: detail.contact_role || null,

    fit_score: Number.isFinite(detail.fit_score) ? detail.fit_score : null,
    priority: detail.priority || null,
    fit_reasons: detail.fit_reasons ?? [],
    fit_risks: detail.fit_risks ?? [],

    company_summary: detail.company_summary || null,
    pain_hypothesis: detail.pain_hypothesis || null,
    pain_confidence: detail.pain_confidence || null,
    sales_angle: detail.sales_angle || null,
    core_message: detail.core_message || null,
    likely_objection: detail.likely_objection || null,

    email_subject: detail.email_subject || null,
    email_body: detail.email_body || null,

    intake_warnings: detail.intake_warnings ?? [],
    low_evidence: detail.low_evidence ?? null,
    missing_fields: missing,

    evidence_cards: (detail.evidence_cards ?? []).map((card) => ({
      headline: card.headline,
      description: card.description,
      confidence: card.confidence,
      source_type: card.source_type,
    })),

    qa,
  };
}

// --------------------------------------------------------------------------- //
// Live-mode banner styling                                                    //
// --------------------------------------------------------------------------- //

function liveStatusTone(status: AssistantResponse["status"]): string {
  if (status === "ok") {
    return "border-[--color-success]/30 bg-[--color-success-bg]/20 text-[--color-success]";
  }
  if (status === "rate_limited" || status === "timeout") {
    return "border-[--color-warning]/30 bg-[--color-warning-bg]/30 text-[--color-warning]";
  }
  if (status === "provider_error") {
    return "border-[--color-error]/30 bg-[--color-error-bg]/30 text-[--color-error]";
  }
  return "border-[--border-default] bg-[--bg-overlay] text-[--text-secondary]";
}

function modeLabel(response: AssistantResponse): string {
  switch (response.mode) {
    case "live_llm":
      return "Live assistant";
    case "deterministic":
      return "Deterministic fallback";
    case "off":
    default:
      return "Live assistant off";
  }
}

function describeAssistantTransportError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 401 || err.status === 403) {
      return DEMO_ACCESS_REQUIRED_MESSAGE;
    }
    if (err.status === 429) {
      return "The live assistant is rate limited for this public demo. Please wait a moment and try again.";
    }
    if (err.status === 503) {
      return "The live assistant is unavailable or the backend is warming up. Try again in a moment.";
    }
    const detail = apiDetail(err.body);
    return detail
      ? `Assistant request failed (HTTP ${err.status}): ${detail}`
      : `Assistant request failed (HTTP ${err.status}). Try again in a moment.`;
  }
  if (err instanceof Error) return err.message;
  return "Unexpected error contacting the assistant.";
}

// --------------------------------------------------------------------------- //
// Component                                                                   //
// --------------------------------------------------------------------------- //

export function ReviewAssistantPanel({
  detail,
  postAssistantQuestion = postAssistantLeadQuestion,
}: ReviewAssistantPanelProps) {
  const [selectedQuestion, setSelectedQuestion] = useState<QuestionId>("evidence");
  const answerRef = useRef<HTMLDivElement | null>(null);
  const [scrollAnswerIntoView, setScrollAnswerIntoView] = useState(false);
  const selected =
    ALL_QUESTIONS.find((question) => question.id === selectedQuestion) ??
    ALL_QUESTIONS[0];
  const deterministicAnswer = useMemo(
    () => buildAnswer(selectedQuestion, detail),
    [selectedQuestion, detail],
  );

  // Live LLM state.
  const [question, setQuestion] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [transportError, setTransportError] = useState<string | null>(null);

  const trimmed = question.trim();
  const overLimit = trimmed.length > QUESTION_CHAR_LIMIT;
  const submitDisabled = isLoading || trimmed.length === 0 || overLimit;

  useEffect(() => {
    if (!scrollAnswerIntoView) return;
    answerRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    setScrollAnswerIntoView(false);
  }, [deterministicAnswer, scrollAnswerIntoView]);

  const handleAsk = async () => {
    if (submitDisabled) return;
    setIsLoading(true);
    setTransportError(null);
    try {
      const payload: AssistantRequest = {
        question: trimmed,
        lead: buildLeadContext(detail),
        live_research: [] as AssistantLiveResearchSnippetIn[],
        run_mode: detail.run_mode || null,
      };
      const result = await postAssistantQuestion(payload);
      setResponse(result);
    } catch (err) {
      setTransportError(describeAssistantTransportError(err));
      setResponse(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section
      className="surface-card rounded-lg p-4"
      aria-labelledby="contextual-assistant-heading"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3
            id="contextual-assistant-heading"
            className="text-sm font-semibold text-[--text-primary]"
          >
            Ask the LeadForge agents
          </h3>
          <p className="text-xs text-[--text-muted] mt-1">
            Contextual agent assistant
          </p>
        </div>
        <span className="rounded-full border border-[--border-subtle] bg-[--bg-overlay] px-2 py-0.5 text-[10px] font-medium text-[--text-muted]">
          Grounded in this lead
        </span>
      </div>

      <p className="text-xs text-[--text-secondary] mt-3 leading-relaxed">
        Answers are grounded in this lead&apos;s available context. When live
        research has been run, available research evidence may inform the
        answer. Run Live Research first to enrich this lead&apos;s context.
        The assistant does not browse the web automatically, send email, or
        update CRM. Live LLM is off by default.
      </p>

      <div className="mt-4 space-y-4">
        {QUESTION_GROUPS.map((group) => (
          <div key={group.lens}>
            <p className="text-[10px] font-mono uppercase tracking-widest text-[--accent-primary] mb-2">
              {group.lens}
            </p>
            <div className="grid grid-cols-1 gap-2">
              {group.questions.map((q) => (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => {
                    setSelectedQuestion(q.id);
                    setScrollAnswerIntoView(true);
                  }}
                  className={`rounded-lg border px-3 py-2 text-left text-xs transition-colors ${
                    selectedQuestion === q.id
                      ? "border-[--accent-primary] bg-[--accent-primary]/10 text-[--text-primary]"
                      : "border-[--border-subtle] bg-[--bg-elevated] text-[--text-secondary] hover:text-[--text-primary]"
                  }`}
                >
                  {q.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div
        ref={answerRef}
        className="mt-4 rounded-lg border border-[--border-subtle] bg-[--bg-elevated] p-3"
      >
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs font-medium text-[--text-primary]">
            {selected.label}
          </p>
          <span className="rounded-full border border-[--border-subtle] bg-[--bg-overlay] px-2 py-0.5 text-[10px] font-medium text-[--text-muted]">
            {detail.run_mode === "Replay" ? "Replay/demo output" : "Deterministic"}
          </span>
        </div>
        <p className="text-sm text-[--text-secondary] leading-relaxed mt-2">
          {deterministicAnswer}
        </p>
      </div>

      <div className="mt-5">
        <label
          htmlFor="contextual-assistant-input"
          className="flex items-center gap-2 text-xs font-medium text-[--text-primary]"
        >
          <Sparkles className="h-3 w-3" />
          Ask the agent team a custom question
        </label>
        <p className="mt-1 text-[10px] text-[--text-muted]">
          Optional. Submit only when ready — no auto-call on load or while
          typing. Uses this lead&apos;s loaded context only.
        </p>
        <textarea
          id="contextual-assistant-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Is the email draft strong enough for this priority?"
          rows={2}
          maxLength={QUESTION_CHAR_LIMIT + 50}
          className="mt-2 w-full resize-y rounded-md border border-[--border-subtle] bg-[--bg-elevated] px-3 py-2 text-xs text-[--text-primary] placeholder:text-[--text-muted] focus:outline-none focus:ring-1 focus:ring-[--accent-primary]"
        />
        <div className="mt-2 flex items-center justify-between gap-3">
          <span
            className={`text-[10px] ${
              overLimit ? "text-[--color-error]" : "text-[--text-muted]"
            }`}
          >
            {trimmed.length}/{QUESTION_CHAR_LIMIT}
            {overLimit ? " — too long" : ""}
          </span>
          <button
            type="button"
            onClick={handleAsk}
            disabled={submitDisabled}
            className="btn-primary !px-3 !py-1.5 !text-xs disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                Asking…
              </>
            ) : (
              <>
                <Send className="h-3 w-3" />
                Ask agents
              </>
            )}
          </button>
        </div>
      </div>

      {transportError && (
        <div
          className="mt-3 rounded-lg border border-[--color-error]/30 bg-[--color-error-bg]/30 px-3 py-2 text-xs text-[--color-error]"
          role="alert"
        >
          {transportError}
        </div>
      )}

      {response && (
        <div className="mt-3 space-y-2">
          <div
            className={`rounded-lg border px-3 py-2 text-xs ${liveStatusTone(response.status)}`}
            role="status"
          >
            <span className="font-medium">{modeLabel(response)}: </span>
            {response.user_message}
          </div>

          {response.status === "ok" && response.answer && (
            <div className="rounded-lg border border-[--border-subtle] bg-[--bg-elevated] p-3">
              <p className="text-sm text-[--text-primary] whitespace-pre-line leading-relaxed">
                {response.answer}
              </p>
              {response.grounding_summary && (
                <p className="mt-2 text-[10px] text-[--text-muted] italic">
                  {response.grounding_summary}
                </p>
              )}
            </div>
          )}

          {response.status !== "ok" && response.answer && (
            <div className="rounded-lg border border-[--border-subtle] bg-[--bg-elevated] p-3">
              <p className="text-sm text-[--text-secondary] whitespace-pre-line leading-relaxed">
                {response.answer}
              </p>
            </div>
          )}

          {response.used_context_fields.length > 0 && (
            <div className="flex flex-wrap items-center gap-1">
              <span className="text-[10px] uppercase tracking-widest text-[--text-muted] font-mono mr-1">
                Used context
              </span>
              {response.used_context_fields.slice(0, 10).map((field) => (
                <span
                  key={field}
                  className="rounded-full border border-[--border-subtle] bg-[--bg-overlay] px-2 py-0.5 text-[10px] font-mono text-[--text-muted]"
                >
                  {field}
                </span>
              ))}
              {response.used_context_fields.length > 10 && (
                <span className="text-[10px] text-[--text-muted]">
                  +{response.used_context_fields.length - 10} more
                </span>
              )}
            </div>
          )}

          {response.context_truncated && (
            <p className="text-[10px] text-[--text-muted] italic">
              Lead context was long — some sections were shortened before
              sending to the assistant.
            </p>
          )}

          {response.warnings.length > 0 && (
            <ul className="space-y-1">
              {response.warnings.map((warning) => (
                <li key={warning} className="text-[10px] text-[--text-muted]">
                  · {warning}
                </li>
              ))}
            </ul>
          )}

          <div className="flex flex-wrap items-center gap-3 text-[10px] text-[--text-muted]">
            <span>
              Mode: <span className="font-mono">{response.mode}</span>
            </span>
            {response.provider && (
              <span>
                Provider:{" "}
                <span className="font-mono">{response.provider}</span>
              </span>
            )}
            {response.model && (
              <span>
                Model: <span className="font-mono">{response.model}</span>
              </span>
            )}
            {response.estimated_tokens !== null && (
              <span>
                Est. tokens:{" "}
                <span className="font-mono">
                  {response.estimated_tokens}
                </span>
              </span>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
