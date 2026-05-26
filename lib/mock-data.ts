import { Lead, AgentStatus, RunMetrics, LeadDetail } from './types';

export const mockLeads: Lead[] = [
  { id: 'lead-001', company: 'NovaBridge Solutions', website: 'novabridge.io', industry: 'B2B SaaS', country: 'USA', employees: '51-200', contact_name: 'Jordan Kim', contact_role: 'VP of Sales', fit_score: 91, priority: 'High', qa_score: 88, status: 'Pending Review', est_cost: '$0.043', email_subject: 'Growing revenue teams at NovaBridge — a thought', run_mode: 'Replay' },
  { id: 'lead-002', company: 'Meridian Health Group', website: 'meridianhealth.com', industry: 'Healthcare Tech', country: 'Canada', employees: '201-500', contact_name: 'Sarah Okonkwo', contact_role: 'Revenue Operations Manager', fit_score: 84, priority: 'High', qa_score: 92, status: 'Approved', est_cost: '$0.039', email_subject: 'Streamlining ops at Meridian — worth 10 minutes?', run_mode: 'Replay' },
  { id: 'lead-003', company: 'Stackline Analytics', website: 'stacklineanalytics.io', industry: 'Data Analytics', country: 'UK', employees: '11-50', contact_name: 'Marcus Webb', contact_role: 'Founder & CEO', fit_score: 78, priority: 'High', qa_score: 85, status: 'Pending Review', est_cost: '$0.041', email_subject: 'Scaling pipeline at Stackline — quick question', run_mode: 'Replay' },
  { id: 'lead-004', company: 'Cerulean Logistics', website: 'ceruleanlogistics.com', industry: 'Logistics & Supply Chain', country: 'Germany', employees: '501-1000', contact_name: 'Lena Bauer', contact_role: 'Sales Operations Lead', fit_score: 65, priority: 'Medium', qa_score: 79, status: 'Needs Edit', est_cost: '$0.038', email_subject: 'Outbound efficiency at Cerulean — a quick idea', run_mode: 'Replay' },
  { id: 'lead-005', company: 'Altair Fintech', website: 'altairfintech.io', industry: 'Fintech', country: 'Mexico', employees: '11-50', contact_name: 'Carlos Reyes', contact_role: 'Head of Growth', fit_score: 72, priority: 'Medium', qa_score: 81, status: 'Pending Review', est_cost: '$0.044', email_subject: 'Pipeline quality at Altair — one thought', run_mode: 'Replay' },
  { id: 'lead-006', company: 'Prism EdTech', website: 'prismedtech.com', industry: 'EdTech', country: 'Australia', employees: '51-200', contact_name: 'Yuki Tanaka', contact_role: 'B2B Sales Manager', fit_score: 48, priority: 'Low', qa_score: 71, status: 'Rejected', est_cost: '$0.035', email_subject: 'Outreach efficiency at Prism — quick note', run_mode: 'Replay' },
  { id: 'lead-007', company: 'OrcaCore Systems', website: 'orcacore.dev', industry: 'Infrastructure Software', country: 'USA', employees: '11-50', contact_name: 'Devon Price', contact_role: 'Co-Founder', fit_score: 88, priority: 'High', qa_score: 90, status: 'Approved', est_cost: '$0.046', email_subject: 'Sales velocity at OrcaCore — a thought worth sharing', run_mode: 'Replay' },
  { id: 'lead-008', company: 'Veridian ConsultGroup', website: 'veridiangroup.com', industry: 'Management Consulting', country: 'UK', employees: '201-500', contact_name: 'Amara Dube', contact_role: 'Director of Business Development', fit_score: 55, priority: 'Medium', qa_score: 76, status: 'Pending Review', est_cost: '$0.037', email_subject: 'Pipeline at Veridian — a quick question', run_mode: 'Replay' },
  { id: 'lead-009', company: 'Luminary HR Solutions', website: 'luminaryhr.io', industry: 'HR Tech', country: 'Spain', employees: '51-200', contact_name: 'Elena Morales', contact_role: 'VP of Partnerships', fit_score: 61, priority: 'Medium', qa_score: 82, status: 'Pending Review', est_cost: '$0.040', email_subject: 'Outbound at Luminary — worth a quick read?', run_mode: 'Replay' },
  { id: 'lead-010', company: 'Forge Manufacturing Co.', website: 'forgeco.com', industry: 'Manufacturing', country: 'USA', employees: '1000+', contact_name: 'Robert Haines', contact_role: 'Sales Director', fit_score: 33, priority: 'Low', qa_score: 64, status: 'Rejected', est_cost: '$0.032', email_subject: 'Operations efficiency at Forge Co — a quick thought', run_mode: 'Replay' },
];

export const mockRunMetrics: RunMetrics = {
  total_processed: 10,
  high_fit_leads: 4,
  avg_qa_score: 81,
  total_cost: '$0.395',
  run_timestamp: '2026-05-19 14:32 UTC',
  model_used: 'deterministic replay (no model call)',
  run_mode: 'Replay',
};

export const mockAgentStatus: AgentStatus[] = [
  {
    name: 'Intake',
    status: 'success',
    success_rate: '10/10',
    avg_latency: '0ms',
    description: 'Normalize submitted lead rows and flag missing context.',
    output_summary: '10 demo lead records loaded from the saved replay dataset.',
  },
  {
    name: 'Research',
    status: 'success',
    success_rate: '10/10',
    avg_latency: '4.2s',
    description: 'Collect company context, opportunity signals, and evidence.',
    output_summary: 'Company summaries and evidence cards are available for review.',
  },
  {
    name: 'Qualifier',
    status: 'warning',
    success_rate: '9/10',
    avg_latency: '2.1s',
    description: 'Score ICP fit and assign lead priority.',
    output_summary: 'Fit scores and priorities are present; one lead needs careful review.',
  },
  {
    name: 'Strategist',
    status: 'success',
    success_rate: '10/10',
    avg_latency: '2.8s',
    description: 'Turn fit and evidence into a sales angle.',
    output_summary: 'Pain hypotheses, core messages, and likely objections are available.',
  },
  {
    name: 'Email Drafter',
    status: 'success',
    success_rate: '10/10',
    avg_latency: '3.5s',
    description: 'Draft review-ready outreach from the available context.',
    output_summary: 'Subjects and email bodies are present for all replay leads.',
  },
  {
    name: 'QA Evaluator',
    status: 'success',
    success_rate: '10/10',
    avg_latency: '1.9s',
    description: 'Check draft quality, evidence coverage, and hallucination risk.',
    output_summary: 'QA scores and recommendations are available for review.',
  },
];

export const mockLeadDetail: LeadDetail = {
  ...mockLeads[0],
  company_summary: 'NovaBridge Solutions is a B2B SaaS company serving mid-market revenue teams. They offer a revenue intelligence platform focused on pipeline analytics and rep performance tracking. Recent signals indicate they are scaling their sales team and have been investing in RevOps tooling.',
  opportunity_signals: ['Expanding sales team (3 recent SDR job posts)', 'Investing in RevOps stack (Outreach + Clari)', 'Series B announced Q1 2026 ($18M)'],
  evidence_cards: [
    { id: 'ev-001', headline: 'Active hiring in sales and ops roles', source_type: 'Demo Context', description: 'LinkedIn shows 3 open SDR roles and 1 RevOps Analyst in the last 30 days. Indicates growth and pipeline investment.', confidence: 'High' },
    { id: 'ev-002', headline: 'Series B funding — scaling phase', source_type: 'Demo Context', description: 'NovaBridge closed an $18M Series B in Q1 2026. Companies at this stage typically prioritize sales efficiency.', confidence: 'High' },
    { id: 'ev-003', headline: 'ICP match: B2B SaaS, 51-200, VP Sales', source_type: 'Knowledge Base', description: 'Matches ICP profile exactly: SaaS company, growth stage, VP-level contact in a sales leadership role.', confidence: 'High' },
    { id: 'ev-004', headline: 'Website signals RevOps focus', source_type: 'Demo Context', description: 'Product pages reference pipeline analytics and performance tracking — tools adjacent to outbound ops challenges.', confidence: 'Medium' },
  ],
  fit_reasons: [
    'Perfect ICP match: B2B SaaS, 51-200 employees, growth stage',
    'VP of Sales is the ideal buyer persona for this product',
    'Active hiring signals pipeline scaling pressure',
    'Recent Series B indicates budget availability',
  ],
  fit_risks: [
    'No direct signal of current outbound pipeline challenges',
    'May already have a competing solution in place',
  ],
  pain_hypothesis: 'NovaBridge is likely experiencing the classic scaling pain: they are growing their sales team faster than their outbound infrastructure can support. New reps need quality pipeline immediately, but manual research and prospecting delays slow ramp time.',
  pain_confidence: 'High',
  sales_angle: 'Position LeadForge as a sales ramp accelerator — not just a lead tool, but a way to give new reps researched, qualified prospects from day one.',
  core_message: 'Cut lead research time from 45 minutes to under 2 minutes, with full traceability.',
  likely_objection: 'We already use Apollo/ZoomInfo for lead data.',
  email_body: `Hi Jordan,

Noticed NovaBridge is scaling the sales team — three SDR roles posted in the last month is a strong signal.

The challenge we see with fast-growing revenue teams isn't lead quantity — it's lead quality and ramp time. New reps spend hours on manual research before their first call, and the output is often inconsistent.

LeadForge runs a research-and-qualification pipeline on your lead list: company context, ICP fit score with reasons, and a personalized email draft — all in under 2 minutes per lead, with full traceability so you can see exactly why each lead was prioritized.

Happy to show you a 10-minute demo with your own lead list. Worth a look?

Best,
[Your name]`,
  personalization_notes: [
    'Referenced hiring signal (SDR roles) as the opening hook — anchored to a verifiable fact',
    'Pain hypothesis built on scaling friction, not generic "AI will help you" framing',
    'CTA is specific (10-minute demo, own lead list) — reduces activation energy',
  ],
  qa_scores: {
    personalization: 88,
    evidence_coverage: 92,
    cta_quality: 85,
    tone_match: 90,
    hallucination_risk: 'Low',
    recommendation: 'Recommended for approval',
  },
  est_total_latency: '12.3s',
  model_used: 'deterministic replay (no model call)',
  agent_steps: 5,
  est_tokens: 3420,
  trace: [
    { agent: 'Research', status: 'success', input_summary: 'Demo lead — NovaBridge Solutions, B2B SaaS, USA', output_summary: '4 evidence cards generated. 3 high-confidence signals. 1 medium. No invented sources.', latency: '4.1s', tokens: 890, prompt_version: 'v1.3' },
    { agent: 'Qualifier', status: 'success', input_summary: 'Lead + 4 evidence cards', output_summary: 'Fit score: 91. Priority: High. 4 reasons, 2 risks. ICP match confirmed.', latency: '2.0s', tokens: 520, prompt_version: 'v1.1' },
    { agent: 'Strategist', status: 'success', input_summary: 'Lead + research + fit score 91', output_summary: 'Pain hypothesis: scaling ops pressure. Sales angle: ramp accelerator. CTA: 10-min demo.', latency: '2.7s', tokens: 610, prompt_version: 'v1.2' },
    { agent: 'Email Drafter', status: 'success', input_summary: 'Lead + strategy + product knowledge', output_summary: 'Subject: "Growing revenue teams at NovaBridge — a thought". Body: 4 paragraphs, SDR hiring hook.', latency: '3.4s', tokens: 840, prompt_version: 'v1.4' },
    { agent: 'QA Evaluator', status: 'success', input_summary: 'Email draft + all previous outputs', output_summary: 'QA scores: avg 88. Hallucination risk: Low. Recommendation: Approved.', latency: '1.9s', tokens: 280, prompt_version: 'v1.1' },
  ],
};
