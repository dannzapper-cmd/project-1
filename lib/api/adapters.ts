/**
 * Phase 7.0 — wire-to-view-model adapters.
 *
 * Translates the backend's JSON contracts (`lib/api/types.ts`) into
 * the dashboard's existing view-model types (`lib/types.ts`) so the
 * components in `components/dashboard/*` stay unchanged in Phase
 * 7.0. The Phase 7.1 swap is a single line: replace the mock import
 * with `toRunMetrics(enriched)` / `toLeads(enriched)` etc.
 *
 * The adapters are deliberately pure and synchronous — no fetch,
 * no React. They are unit-tested against fixtures captured from
 * the real backend (`lib/api/__fixtures__/`).
 *
 * --- EvidenceSource enum (verified 2026-05-23 against
 *     backend/app/schemas/common.py) ---
 * The backend `EvidenceSource` enum is declared with the display
 * strings AS the enum values, so the JSON does not require remapping:
 *
 *   KNOWLEDGE_BASE = "Knowledge Base"
 *   PUBLIC_DATA    = "Public Data"
 *   DEMO_CONTEXT   = "Demo Context"
 *
 * The same exact-match holds for `Priority` ("High"/"Medium"/"Low"),
 * `HallucinationRisk` ("Low"/"Medium"/"High"), and `Recommendation`
 * ("Recommended for approval"/"Review carefully"/"Regenerate
 * suggested"). No enum-translation layer is needed for those.
 */

import type {
  EnrichedBatch,
  EnrichedLeadResult,
  EvidenceCard as WireEvidenceCard,
  LeadIn,
  LeadPipelineContractOutput,
  PipelineRunSummary,
  TraceEntry as WireTraceEntry,
} from "./types.ts";
import type {
  AgentStatus,
  EvidenceCard as ViewEvidenceCard,
  Lead,
  LeadDetail,
  RunMetrics,
  TraceEntry as ViewTraceEntry,
} from "../types.ts";

// --------------------------------------------------------------------------- //
// Constants                                                                   //
// --------------------------------------------------------------------------- //

/**
 * Display labels for backend snake_case agent identifiers, in
 * canonical pipeline order. The view model expects the leading
 * label form ("Research") used by the existing `TraceTimeline` /
 * `AgentStatusRow` mock data; this map is the single point of
 * truth for that translation.
 */
export const AGENT_LABELS: Readonly<Record<string, string>> = Object.freeze({
  intake_agent: "Intake",
  research_agent: "Research",
  qualifier_agent: "Qualifier",
  strategist_agent: "Strategist",
  email_drafter_agent: "Email Drafter",
  qa_evaluator_agent: "QA Evaluator",
});

const AGENT_DESCRIPTIONS: Readonly<Record<string, string>> = Object.freeze({
  intake_agent: "Normalize submitted lead rows and flag missing context.",
  research_agent: "Collect company context, opportunity signals, and evidence.",
  qualifier_agent: "Score ICP fit and assign lead priority.",
  strategist_agent: "Turn fit and evidence into a sales angle.",
  email_drafter_agent: "Draft review-ready outreach from the available context.",
  qa_evaluator_agent: "Check draft quality, evidence coverage, and hallucination risk.",
});

/** Order used when synthesising per-agent status from the trace. */
const AGENT_DISPLAY_ORDER: readonly string[] = [
  "intake_agent",
  "research_agent",
  "qualifier_agent",
  "strategist_agent",
  "email_drafter_agent",
  "qa_evaluator_agent",
];

/** UI label for `PipelineRunContractOutput.run_mode`. */
export const RUN_MODE_LABELS: Readonly<Record<string, string>> = Object.freeze({
  deterministic_pipeline: "Demo (Deterministic)",
});

/** UI label for `PipelineRunContractOutput.model_mode`. */
export const MODEL_MODE_LABELS: Readonly<Record<string, string>> = Object.freeze({
  mock: "Mock Model",
});

// --------------------------------------------------------------------------- //
// Internal helpers                                                            //
// --------------------------------------------------------------------------- //

/**
 * Convert a backend integer `employee_count` to the bucketed string
 * the dashboard's `Lead.employees` field expects. Returns "Unknown"
 * for `null` / missing values.
 */
function employeeBucket(count: number | null): string {
  if (count === null || count === undefined) return "Unknown";
  if (count <= 10) return "1-10";
  if (count <= 50) return "11-50";
  if (count <= 200) return "51-200";
  if (count <= 500) return "201-500";
  if (count <= 1000) return "501-1000";
  return "1000+";
}

/**
 * Map a backend `lead_id` to the value the existing `Lead.id` view
 * model uses. The Phase 7.0 decision is to standardize on the
 * backend's `lead_001` form (source of truth). A `lead-001` form
 * coming from older mock data is converted to `lead_001` so old
 * persisted state still matches.
 */
export function normalizeLeadId(id: string): string {
  return id.replace(/-/g, "_");
}

/** Map a backend trace agent identifier to the view-model label. */
export function toAgentLabel(agent: string): string {
  return AGENT_LABELS[agent] ?? agent;
}

// --------------------------------------------------------------------------- //
// Per-field adapters                                                          //
// --------------------------------------------------------------------------- //

function toEvidenceCard(
  card: WireEvidenceCard,
  fallbackId: string,
): ViewEvidenceCard {
  return {
    id: card.id ?? fallbackId,
    headline: card.headline,
    source_type: card.source_type,
    description: card.description,
    confidence: card.confidence,
  };
}

export function toTraceEntries(
  result: Pick<LeadPipelineContractOutput, "trace">,
): ViewTraceEntry[] {
  return result.trace.map((entry: WireTraceEntry) => ({
    agent: toAgentLabel(entry.agent),
    status: entry.status,
    input_summary: entry.input_summary,
    output_summary: entry.output_summary,
    latency: entry.latency,
    tokens: entry.tokens,
    prompt_version: entry.prompt_version,
  }));
}

/**
 * Flatten a `LeadPipelineContractOutput` (+ optional `LeadIn`) into
 * the dashboard's `Lead` view model. Tolerates missing agent slots
 * by falling back to safe defaults so a partial pipeline still
 * renders (e.g. a failed Research step shouldn't break the table).
 */
export function toLead(enriched: EnrichedLeadResult): Lead {
  const { result, lead_in } = enriched;

  const fitScore = result.qualification?.fit_score ?? 0;
  const priority = result.qualification?.priority ?? "Low";
  const qaScore = result.qa?.qa_score ?? 0;
  const emailSubject = result.email?.email_subject ?? "";

  return {
    id: normalizeLeadId(result.lead_id),
    company: lead_in?.company_name ?? result.lead_id,
    website: lead_in?.website ?? "",
    industry: lead_in?.industry ?? "",
    country: lead_in?.country ?? "",
    employees: employeeBucket(lead_in?.employee_count ?? null),
    contact_name: lead_in?.contact_name ?? "",
    contact_role: lead_in?.contact_role ?? "",
    fit_score: fitScore,
    priority,
    qa_score: qaScore,
    // Backend never assigns a human-review status; default to
    // "Pending Review" so the table renders the correct badge until
    // a future review-state phase wires this through.
    status: "Pending Review",
    // Phase 7.0 decision: show "N/A" while model_mode is "mock";
    // cost tracking belongs to a future Groq-backed phase.
    est_cost: "N/A",
    email_subject: emailSubject,
    // Frontend `RunMode` is "Live" | "Replay". The deterministic
    // pipeline is a replayable demo, so map to "Replay".
    run_mode: "Replay",
  };
}

export function toLeads(batch: EnrichedBatch): Lead[] {
  return batch.results.map(toLead);
}

/** Flatten a single enriched result into a `LeadDetail` view model. */
export function toLeadDetail(enriched: EnrichedLeadResult): LeadDetail {
  const base = toLead(enriched);
  const { result } = enriched;

  const research = result.research;
  const qualification = result.qualification;
  const strategy = result.strategy;
  const email = result.email;
  const qa = result.qa;
  const intakeWarnings = result.intake?.validation_flags ?? [];

  const evidenceCards: ViewEvidenceCard[] =
    research?.evidence_cards.map((card, idx) =>
      toEvidenceCard(card, `ev-${base.id}-${idx + 1}`),
    ) ?? [];

  const totalTokens = result.trace.reduce(
    (sum, entry) => sum + (entry.tokens ?? 0),
    0,
  );

  return {
    ...base,
    intake_warnings: intakeWarnings,
    low_evidence: intakeWarnings.some((flag) =>
      flag.toLowerCase().includes("low_evidence"),
    ),
    company_summary: research?.company_summary ?? "",
    opportunity_signals: research?.opportunity_signals ?? [],
    evidence_cards: evidenceCards,
    fit_reasons: qualification?.fit_reasons ?? [],
    fit_risks: qualification?.fit_risks ?? [],
    pain_hypothesis: strategy?.pain_hypothesis ?? "",
    pain_confidence: strategy?.pain_confidence ?? "Low",
    sales_angle: strategy?.sales_angle ?? "",
    core_message: strategy?.core_message ?? "",
    likely_objection: strategy?.likely_objection ?? "",
    email_body: email?.email_body ?? "",
    personalization_notes:
      email?.personalization_notes ??
      strategy?.personalization_notes ??
      [],
    qa_scores: qa?.qa_scores ?? {
      personalization: 0,
      evidence_coverage: 0,
      cta_quality: 0,
      tone_match: 0,
      hallucination_risk: "Low",
      recommendation: "Review carefully",
    },
    est_total_latency: result.trace.length
      ? result.trace[result.trace.length - 1].latency
      : "0ms",
    model_used:
      result.trace[0]?.model ?? qa?.result?.metadata?.model ?? "mock",
    agent_steps: result.trace.length,
    est_tokens: totalTokens,
    trace: toTraceEntries(result),
  };
}

/**
 * Build the dashboard's `RunMetrics` block from a batch summary.
 * Phase 7.0 contracts:
 *   - `avg_qa_score` is allowed to be `null` (no QA outputs) — the
 *     widened `RunMetrics` type accepts it; UI handles the null.
 *   - `model_used` and `run_mode` come from the per-batch labels;
 *     the dashboard's existing "Live"/"Replay" radio is retired in
 *     a later phase. For now we map "deterministic_pipeline" to
 *     "Replay" so `MetricsRow` keeps working.
 */
export function toRunMetrics(batch: EnrichedBatch): RunMetrics {
  const high = batch.summary.high_priority_leads;
  return {
    total_processed: batch.summary.processed_leads,
    high_fit_leads: high,
    avg_qa_score: batch.summary.average_qa_score,
    // Cost tracking is not produced by the deterministic pipeline.
    total_cost: "N/A",
    // The pipeline response carries no timestamp; the run_id is the
    // closest identifier. Phase 7.1 may add a real generated_at on
    // the backend. For now, surface the run_id so the UI still has
    // something to render in the timestamp slot.
    run_timestamp: batch.run_id,
    model_used: MODEL_MODE_LABELS[batch.model_mode] ?? batch.model_mode,
    run_mode: "Replay",
  };
}

/** Synthesise an `AgentStatus[]` row from per-lead outputs and traces. */
export function toAgentStatuses(batch: EnrichedBatch): AgentStatus[] {
  const totalLeads = batch.results.length;

  return AGENT_DISPLAY_ORDER.map((agentKey) => {
    const stage = summarizeStage(batch, agentKey);

    return {
      name: toAgentLabel(agentKey),
      status: stage.status,
      success_rate: `${stage.successes}/${totalLeads}`,
      avg_latency: stage.avgLatency,
      description: AGENT_DESCRIPTIONS[agentKey],
      output_summary: stage.outputSummary,
    };
  });
}

function summarizeStage(
  batch: EnrichedBatch,
  agentKey: string,
): {
  status: AgentStatus["status"];
  successes: number;
  avgLatency: string;
  outputSummary: string;
} {
  if (agentKey === "intake_agent") {
    const present = batch.results.filter(({ result }) => result.intake !== null);
    const warningCount = present.reduce(
      (sum, { result }) => sum + (result.intake?.validation_flags.length ?? 0),
      0,
    );
    if (present.length === 0) {
      return {
        status: "warning",
        successes: 0,
        avgLatency: "0ms",
        outputSummary:
          "No intake output is attached to this replay; using source lead rows.",
      };
    }
    return {
      status: warningCount > 0 ? "warning" : "success",
      successes: present.filter(({ result }) => result.intake?.result.success).length,
      avgLatency: averageMetadataLatency(
        present.map(({ result }) => result.intake?.result.metadata.latency),
      ),
      outputSummary:
        warningCount > 0
          ? `${present.length} leads normalized with ${warningCount} intake warning${warningCount === 1 ? "" : "s"}.`
          : `${present.length} leads normalized with no intake warnings.`,
    };
  }

  const traces = batch.results
    .map(({ result }) => result.trace.find((t) => t.agent === agentKey))
    .filter((entry): entry is WireTraceEntry => entry !== undefined);

  const outputCount = batch.results.filter(({ result }) =>
    hasStageOutput(result, agentKey),
  ).length;

  const status = aggregateTraceStatus(traces, outputCount, batch.results.length);
  const successes = traces.filter((entry) => entry.status === "success").length;

  return {
    status,
    successes,
    avgLatency: averageMetadataLatency(traces.map((entry) => entry.latency)),
    outputSummary: stageOutputSummary(batch, agentKey, outputCount),
  };
}

function hasStageOutput(
  result: LeadPipelineContractOutput,
  agentKey: string,
): boolean {
  switch (agentKey) {
    case "research_agent":
      return result.research !== null;
    case "qualifier_agent":
      return result.qualification !== null;
    case "strategist_agent":
      return result.strategy !== null;
    case "email_drafter_agent":
      return result.email !== null;
    case "qa_evaluator_agent":
      return result.qa !== null;
    default:
      return false;
  }
}

function stageOutputSummary(
  batch: EnrichedBatch,
  agentKey: string,
  outputCount: number,
): string {
  const total = batch.results.length;
  switch (agentKey) {
    case "research_agent": {
      const evidenceCount = batch.results.reduce(
        (sum, { result }) => sum + (result.research?.evidence_cards.length ?? 0),
        0,
      );
      return `${outputCount}/${total} leads have research output; ${evidenceCount} evidence cards available.`;
    }
    case "qualifier_agent":
      return `${outputCount}/${total} leads scored; ${batch.summary.high_priority_leads} high, ${batch.summary.medium_priority_leads} medium, ${batch.summary.low_priority_leads} low priority.`;
    case "strategist_agent":
      return `${outputCount}/${total} leads have sales angles and pain hypotheses.`;
    case "email_drafter_agent":
      return `${outputCount}/${total} leads have email subjects and draft bodies.`;
    case "qa_evaluator_agent":
      return `${outputCount}/${total} leads have QA scores; average QA is ${formatAverageQa(batch.summary.average_qa_score)}.`;
    default:
      return outputCount > 0
        ? `${outputCount}/${total} leads have output.`
        : "No output is available for this stage.";
  }
}

function aggregateTraceStatus(
  traces: WireTraceEntry[],
  outputCount: number,
  totalLeads: number,
): AgentStatus["status"] {
  if (totalLeads === 0) return "pending";
  if (traces.some((entry) => entry.status === "failed")) return "failed";
  if (traces.some((entry) => entry.status === "running")) return "running";
  if (traces.some((entry) => entry.status === "warning")) return "warning";
  if (traces.some((entry) => entry.status === "pending")) return "pending";
  if (traces.length === 0 || outputCount === 0) return "warning";
  if (outputCount < totalLeads || traces.length < totalLeads) return "warning";
  return "success";
}

function averageMetadataLatency(latencies: Array<string | undefined>): string {
  let totalLatencyMs = 0;
  let leadsWithLatency = 0;
  for (const latency of latencies) {
    if (!latency) continue;
    const latencyMs = parseLatencyMs(latency);
    if (latencyMs !== null) {
      totalLatencyMs += latencyMs;
      leadsWithLatency += 1;
    }
  }

  return leadsWithLatency
    ? `${(totalLatencyMs / leadsWithLatency).toFixed(0)}ms`
    : "0ms";
}

function formatAverageQa(score: number | null): string {
  if (score === null || Number.isNaN(score)) return "not available";
  return Number.isInteger(score) ? String(score) : score.toFixed(1);
}

function parseLatencyMs(latency: string): number | null {
  // Backend formats: "0ms", "123ms", "1.2s". Tolerate both units.
  const ms = latency.match(/^(-?\d+(?:\.\d+)?)\s*ms$/i);
  if (ms) return Number(ms[1]);
  const s = latency.match(/^(-?\d+(?:\.\d+)?)\s*s$/i);
  if (s) return Number(s[1]) * 1000;
  return null;
}

// --------------------------------------------------------------------------- //
// Re-exports for convenience                                                  //
// --------------------------------------------------------------------------- //

export type { EnrichedBatch, EnrichedLeadResult, LeadIn, PipelineRunSummary };
