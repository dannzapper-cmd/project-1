export interface Lead {
  id: string;
  company: string;
  website: string;
  industry: string;
  country: string;
  employees: string;
  contact_name: string;
  contact_role: string;
  fit_score: number;
  priority: 'High' | 'Medium' | 'Low';
  qa_score: number;
  status: 'Pending Review' | 'Approved' | 'Rejected' | 'Needs Edit';
  est_cost: string;
  email_subject: string;
  run_mode: 'Live' | 'Replay';
}

export interface AgentStatus {
  name: string;
  status: 'success' | 'warning' | 'failed' | 'running' | 'pending';
  success_rate: string;
  avg_latency: string;
}

export interface RunMetrics {
  total_processed: number;
  high_fit_leads: number;
  // Phase 7.0: backend `PipelineRunSummary.average_qa_score` is
  // `float | None` (returns `null` when no QA outputs are produced),
  // so the view model is widened to accept null. The existing
  // `MetricsRow` component reads this directly; Phase 7.1 will add
  // a fallback render when null.
  avg_qa_score: number | null;
  total_cost: string;
  run_timestamp: string;
  model_used: string;
  run_mode: 'Live' | 'Replay';
}

export interface QAScores {
  personalization: number;
  evidence_coverage: number;
  cta_quality: number;
  tone_match: number;
  hallucination_risk: 'Low' | 'Medium' | 'High';
  recommendation: 'Recommended for approval' | 'Review carefully' | 'Regenerate suggested';
}

export interface TraceEntry {
  agent: string;
  // Phase 7.0: widened to match the backend `AgentRunStatus` enum
  // (`success | warning | failed | running | pending`). The Phase
  // 6.1/6.2 deterministic pipeline only emits the first three, but
  // the type must accept the full enum so a future live/streaming
  // pipeline can reuse the same view model without a type error.
  status: 'success' | 'warning' | 'failed' | 'running' | 'pending';
  input_summary: string;
  output_summary: string;
  latency: string;
  tokens: number;
  prompt_version: string;
}

export interface LeadDetail extends Lead {
  intake_warnings?: string[];
  low_evidence?: boolean;
  company_summary: string;
  opportunity_signals: string[];
  evidence_cards: EvidenceCard[];
  fit_reasons: string[];
  fit_risks: string[];
  pain_hypothesis: string;
  pain_confidence: 'High' | 'Medium' | 'Low';
  sales_angle: string;
  core_message: string;
  likely_objection: string;
  email_body: string;
  personalization_notes: string[];
  qa_scores: QAScores;
  est_total_latency: string;
  model_used: string;
  agent_steps: number;
  est_tokens: number;
  trace: TraceEntry[];
}

export interface EvidenceCard {
  id: string;
  headline: string;
  source_type: 'Knowledge Base' | 'Public Data' | 'Demo Context';
  description: string;
  confidence: 'High' | 'Medium' | 'Low';
}
