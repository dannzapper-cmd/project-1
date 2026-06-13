/**
 * Phase 7.0 — TypeScript mirrors of the backend response contracts.
 *
 * These types reflect the JSON shapes returned by the LeadForge
 * FastAPI backend (Phases 5.2 / 6.1 / 6.2). They are intentionally
 * separate from the dashboard view-model types in `lib/types.ts`:
 *
 * * `lib/api/types.ts` — wire format. Mirrors backend field names,
 *   nesting, and enum strings exactly. Optional fields use
 *   `T | null` to match Pydantic's JSON serialization of
 *   `Optional[X]` (which emits `null`, not `undefined`).
 *
 * * `lib/types.ts` — dashboard view models consumed by the existing
 *   components. `lib/api/adapters.ts` translates wire → view model.
 *
 * The string enums below use literal unions rather than TS enums so
 * the JSON parses to a typed value without a runtime mapping step.
 */

// --------------------------------------------------------------------------- //
// Shared enums (backend string literals)                                      //
// --------------------------------------------------------------------------- //

export type Priority = "High" | "Medium" | "Low";
export type Confidence = "High" | "Medium" | "Low";
export type HallucinationRisk = "Low" | "Medium" | "High";
export type Recommendation =
  | "Recommended for approval"
  | "Review carefully"
  | "Regenerate suggested";

export type AgentRunStatus =
  | "success"
  | "warning"
  | "failed"
  | "running"
  | "pending";

export type EvidenceSource =
  | "Knowledge Base"
  | "Public Data"
  | "Demo Context";

export type RunMode = "Live" | "Replay" | "simulation";

// --------------------------------------------------------------------------- //
// Per-agent envelope                                                          //
// --------------------------------------------------------------------------- //

export interface AgentError {
  code: string;
  message: string;
  recoverable: boolean;
  details: Record<string, string> | null;
}

export interface AgentExecutionMetadata {
  agent_name: string;
  run_mode: RunMode;
  model: string;
  prompt_version: string;
  latency: string;
  tokens: number;
  cost: string;
  simulated: boolean;
}

export interface AgentContractResult {
  success: boolean;
  metadata: AgentExecutionMetadata;
  error: AgentError | null;
}

// --------------------------------------------------------------------------- //
// Per-agent outputs (Phase 5.2 contract)                                      //
// --------------------------------------------------------------------------- //

export interface EvidenceCard {
  id?: string | null;
  headline: string;
  source_type: EvidenceSource;
  description: string;
  confidence: Confidence;
}

export interface QAScores {
  personalization: number;
  evidence_coverage: number;
  cta_quality: number;
  tone_match: number;
  hallucination_risk: HallucinationRisk;
  recommendation: Recommendation;
}

export interface ResearchAgentOutput {
  result: AgentContractResult;
  lead_id: string;
  company_summary: string;
  opportunity_signals: string[];
  pain_hypotheses: string[];
  evidence_cards: EvidenceCard[];
  information_risks: string[];
  confidence: Confidence;
}

export interface QualifierAgentOutput {
  result: AgentContractResult;
  lead_id: string;
  fit_score: number;
  priority: Priority;
  fit_reasons: string[];
  fit_risks: string[];
  confidence: Confidence;
}

export interface StrategistAgentOutput {
  result: AgentContractResult;
  lead_id: string;
  pain_hypothesis: string;
  pain_confidence: Confidence;
  sales_angle: string;
  core_message: string;
  likely_objection: string;
  personalization_notes: string[];
}

export interface EmailDrafterAgentOutput {
  result: AgentContractResult;
  lead_id: string;
  email_subject: string;
  email_body: string;
  personalization_notes: string[];
  confidence: Confidence;
}

export interface QAEvaluatorAgentOutput {
  result: AgentContractResult;
  lead_id: string;
  qa_score: number;
  qa_scores: QAScores;
  hallucination_risk: HallucinationRisk;
  recommendation: Recommendation;
  qa_notes: string[];
}

export interface IntakeAgentOutput {
  result: AgentContractResult;
  normalized_lead: LeadIn;
  validation_flags: string[];
  confidence: Confidence;
}

// --------------------------------------------------------------------------- //
// Block 10A — intake preview contracts                                         //
// --------------------------------------------------------------------------- //

export type IntakeInputType = "csv_text" | "pasted_table" | "records_json" | "raw_text";
export type IntakeSeverity = "info" | "warning" | "error";
export type IntakeRowStatus = "valid" | "warning" | "invalid";
export type IntakeConfidence = "high" | "medium" | "low";

export interface IntakeIssue {
  severity: IntakeSeverity;
  code: string;
  message: string;
  row_number: number | null;
  field: string | null;
}

export interface NormalizedLeadRow {
  row_number: number;
  status: IntakeRowStatus;
  normalized_fields: Record<string, unknown>;
  lead: LeadIn | null;
  confidence: IntakeConfidence | null;
  missing_required_fields: string[];
  low_confidence_fields: string[];
  issues: IntakeIssue[];
}

export interface IntakePreviewRequest {
  input_type: IntakeInputType;
  source_name?: string | null;
  content?: string | null;
  records?: Array<Record<string, unknown>> | null;
  options?: {
    has_header?: true;
    delimiter?: "auto" | "," | "\t";
    generate_missing_lead_ids?: boolean;
  };
}

export interface IntakePreviewResponse {
  status: "preview_ready" | "preview_with_warnings" | "preview_blocked";
  input_type: string;
  source_name: string | null;
  total_rows: number;
  valid_rows: number;
  rows_with_warnings: number;
  failed_rows: number;
  max_leads_per_run: number;
  mapped_columns: Record<string, string>;
  unmapped_columns: string[];
  normalized_leads: NormalizedLeadRow[];
  global_issues: IntakeIssue[];
  capabilities: {
    implemented_now: string[];
    future_adapters: string[];
  };
}

// --------------------------------------------------------------------------- //
// Trace entry (run.py schema)                                                 //
// --------------------------------------------------------------------------- //

export interface TraceEntry {
  agent: string;
  status: AgentRunStatus;
  input_summary: string;
  output_summary: string;
  latency: string;
  tokens: number;
  prompt_version: string;
  model: string;
  simulated: boolean;
}

// --------------------------------------------------------------------------- //
// LeadIn (demo dataset row)                                                   //
// --------------------------------------------------------------------------- //

export interface LeadIn {
  lead_id: string;
  company_name: string;
  website: string | null;
  industry: string | null;
  country: string | null;
  employee_count: number | null;
  contact_name: string | null;
  contact_role: string | null;
  notes: string | null;
}

// --------------------------------------------------------------------------- //
// Phase 6.1 / 6.2 pipeline contracts                                          //
// --------------------------------------------------------------------------- //

export interface LeadPipelineContractOutput {
  run_id: string;
  lead_id: string;
  intake: IntakeAgentOutput | null;
  research: ResearchAgentOutput | null;
  qualification: QualifierAgentOutput | null;
  strategy: StrategistAgentOutput | null;
  email: EmailDrafterAgentOutput | null;
  qa: QAEvaluatorAgentOutput | null;
  trace: TraceEntry[];
}

export interface PipelineRunSummary {
  total_leads: number;
  processed_leads: number;
  high_priority_leads: number;
  medium_priority_leads: number;
  low_priority_leads: number;
  average_qa_score: number | null;
}

export type PipelineRunMode = "deterministic_pipeline" | string;
export type PipelineModelMode = "mock" | "groq" | string;

export interface PipelineRunContractOutput {
  run_id: string;
  run_mode: PipelineRunMode;
  model_mode: PipelineModelMode;
  lead_count: number;
  summary: PipelineRunSummary;
  results: LeadPipelineContractOutput[];
}

// --------------------------------------------------------------------------- //
// Phase 7.0 — Enriched batch (client-side join of /pipeline/batch + /leads)   //
// --------------------------------------------------------------------------- //

/**
 * A per-lead pipeline result joined with its source LeadIn row.
 * `lead_in` is `null` when the join fails (lead_id present in one
 * endpoint but not the other) — the adapter must tolerate this so a
 * partial dataset still renders.
 */
export interface EnrichedLeadResult {
  result: LeadPipelineContractOutput;
  lead_in: LeadIn | null;
}

export interface EnrichedBatch {
  run_id: string;
  run_mode: PipelineRunMode;
  model_mode: PipelineModelMode;
  lead_count: number;
  summary: PipelineRunSummary;
  results: EnrichedLeadResult[];
}

// --------------------------------------------------------------------------- //
// Block 10E — Live Web Research MVP                                          //
//                                                                            //
// Mirrors `app/schemas/live_research.py`. The endpoint always returns        //
// HTTP 200; the component renders disabled / unavailable / rate-limited /    //
// timeout / no-evidence / error states from `status` and `user_message`.     //
// --------------------------------------------------------------------------- //

export type LiveResearchStatus =
  | "ok"
  | "disabled"
  | "unavailable"
  | "insufficient_input"
  | "timeout"
  | "rate_limited"
  | "no_evidence"
  | "provider_error";

export interface LiveResearchRequest {
  company_name: string;
  website?: string | null;
  industry?: string | null;
  country?: string | null;
  notes?: string | null;
}

export interface LiveResearchEvidenceCard {
  title: string;
  url: string;
  source_domain: string;
  snippet: string;
  source_type: "live_web";
  confidence: Confidence;
  why_it_matters: string;
}

export interface LiveResearchSource {
  url: string;
  domain: string;
  title: string | null;
}

export interface LiveResearchResponse {
  provider: "exa" | "none";
  run_mode: "live_research";
  enabled: boolean;
  status: LiveResearchStatus;
  company_name: string;
  query_used: string | null;
  evidence_cards: LiveResearchEvidenceCard[];
  information_risks: string[];
  confidence: Confidence | null;
  sources: LiveResearchSource[];
  fetched_at: string;
  warnings: string[];
  estimated_request_count: number;
  user_message: string;
}

// --------------------------------------------------------------------------- //
// Block 11C.4 — Safe backend capability status + draft regeneration           //
// --------------------------------------------------------------------------- //

export interface SystemStatusResponse {
  backend_alive: boolean;
  demo_mode_available: boolean;
  demo_access_required: boolean;
  live_research_configured: boolean;
  live_model_pipeline_configured: boolean;
  live_email_regenerate_configured: boolean;
  assistant_configured: boolean;
  rate_limit_enabled: boolean;
  max_leads_per_run: number;
  max_upload_size_mb: number;
  live_single_lead_only: boolean;
  public_live_batch_enabled: boolean;
  storage_mode: "ephemeral";
  build_sha: string;
}

export type EmailRegenerateStatus =
  | "ok"
  | "deterministic_fallback"
  | "disabled"
  | "unavailable"
  | "provider_error";

export type EmailRegenerateMode =
  | "live_groq"
  | "deterministic_fallback"
  | "off";


export interface EmailRegenerateLeadContext {
  company_name: string;
  website?: string | null;
  industry?: string | null;
  country?: string | null;
  employee_count?: number | null;
  contact_name?: string | null;
  contact_role?: string | null;
  company_summary?: string;
  pain_hypothesis?: string;
  sales_angle?: string;
  core_message?: string;
  personalization_notes?: string[];
}

export interface EmailRegenerateRequest {
  lead: EmailRegenerateLeadContext;
}

export interface EmailRegenerateResponse {
  status: EmailRegenerateStatus;
  mode: EmailRegenerateMode;
  lead_id: string;
  draft_only: boolean;
  email_subject: string;
  email_body: string;
  personalization_notes: string[];
  provider: "groq" | "none";
  model: string | null;
  latency: string | null;
  tokens: number | null;
  estimated_cost: string | null;
  user_message: string;
  warnings: string[];
}

// --------------------------------------------------------------------------- //
// Groq Live Demo Mode                                                        //
// --------------------------------------------------------------------------- //

export interface LiveDemoLimits {
  max_live_leads_per_run: number;
  max_live_runs_per_session_per_day: number;
  max_live_runs_per_ip_per_day: number;
  max_live_agent_steps_per_lead: number;
  max_live_tokens_per_lead: number;
  daily_live_demo_budget_usd: number;
  live_model_timeout_seconds: number;
  live_concurrency_limit: number;
}

export interface LiveDemoStatusResponse {
  available: boolean;
  groq_api_key_configured: boolean;
  live_mode_enabled: boolean;
  live_mode_unlocked: boolean;
  unlock_required: boolean;
  model_name: string | null;
  limits: LiveDemoLimits;
  unavailable_reasons: string[];
  session_runs_remaining_today: number | null;
  ip_runs_remaining_today: number | null;
  daily_budget_remaining_usd: number | null;
}

export interface LiveDemoUnlockResponse {
  unlocked: boolean;
  session_token: string | null;
  message: string;
}

export type LiveDemoRunMode = "replay" | "deterministic" | "groq_live" | "fallback";

export interface LiveDemoRunMetadata {
  run_mode: LiveDemoRunMode;
  model_provider: string | null;
  model_name: string | null;
  estimated_tokens: number | null;
  estimated_cost_usd: number | null;
  latency_ms: number | null;
  parse_success: boolean | null;
  fallback_used: boolean;
  warnings: string[];
  limits_applied: string[];
  live_mode_unlocked: boolean;
}

export interface LivePipelineComparison {
  fit_score_delta: number | null;
  priority_changed: boolean | null;
  qa_score_delta: number | null;
  email_subject_changed: boolean | null;
  risk_level_changed: boolean | null;
  live_summary: string | null;
  deterministic_summary: string | null;
  comparison_notes: string;
}

export interface LivePipelineResponse {
  run_id: string;
  lead_id: string;
  run_mode: string;
  live_success: boolean;
  live_model_used: string;
  fallback_used: boolean;
  fallback_reason: string | null;
  deterministic_baseline_available: boolean;
  failed_agent: string | null;
  failure_stage: string | null;
  error_code: string | null;
  deterministic_result: LeadPipelineContractOutput | null;
  live_result: LeadPipelineContractOutput | null;
  comparison: LivePipelineComparison;
}

export interface LiveDemoLeadResult {
  lead_id: string;
  pipeline: LivePipelineResponse | null;
  metadata: LiveDemoRunMetadata;
  error: string | null;
}

export interface LiveDemoRunRequest {
  lead_ids: string[];
  leads?: LeadIn[];
}

export interface LiveDemoRunResponse {
  results: LiveDemoLeadResult[];
  rejected_lead_ids: string[];
  message: string | null;
}

// --------------------------------------------------------------------------- //
// Block 10G — Contextual LLM Lead Assistant                                  //
//                                                                            //
// Mirrors `app/schemas/assistant.py`. The endpoint always returns HTTP 200;  //
// the component renders disabled / unavailable / rate-limited / timeout /   //
// insufficient-context / provider-error / invalid-question states from      //
// `status` and `user_message`.                                              //
// --------------------------------------------------------------------------- //

export type AssistantStatus =
  | "ok"
  | "deterministic_fallback"
  | "disabled"
  | "unavailable"
  | "rate_limited"
  | "insufficient_context"
  | "timeout"
  | "provider_error"
  | "invalid_question";

export type AssistantMode = "deterministic" | "live_llm" | "off";

export interface AssistantEvidenceCardIn {
  headline: string;
  description?: string | null;
  confidence?: string | null;
  source_type?: string | null;
}

export interface AssistantLiveResearchSnippetIn {
  title?: string | null;
  source_domain?: string | null;
  snippet?: string | null;
}

export interface AssistantQAContextIn {
  qa_score?: number | null;
  hallucination_risk?: string | null;
  recommendation?: string | null;
  notes?: string[];
}

export interface AssistantLeadContextIn {
  company_name?: string | null;
  industry?: string | null;
  country?: string | null;
  website?: string | null;
  employees?: string | null;
  contact_role?: string | null;

  fit_score?: number | null;
  priority?: string | null;
  fit_reasons?: string[];
  fit_risks?: string[];

  company_summary?: string | null;
  pain_hypothesis?: string | null;
  pain_confidence?: string | null;
  sales_angle?: string | null;
  core_message?: string | null;
  likely_objection?: string | null;

  email_subject?: string | null;
  email_body?: string | null;

  intake_warnings?: string[];
  low_evidence?: boolean | null;
  missing_fields?: string[];

  evidence_cards?: AssistantEvidenceCardIn[];
  qa?: AssistantQAContextIn | null;

  profile_pack_name?: string | null;
  profile_pack_focus?: string | null;
}

export interface AssistantRequest {
  question: string;
  lead: AssistantLeadContextIn;
  live_research?: AssistantLiveResearchSnippetIn[];
  run_mode?: string | null;
}

export interface AssistantResponse {
  status: AssistantStatus;
  mode: AssistantMode;
  answer: string;
  grounding_summary: string;
  used_context_fields: string[];
  unsupported_claims_blocked: boolean;
  context_truncated: boolean;
  warnings: string[];
  provider: string | null;
  model: string | null;
  estimated_tokens: number | null;
  estimated_cost_usd: number | null;
  user_message: string;
}
