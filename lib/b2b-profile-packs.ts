/**
 * Block 10C — rule-based B2B profile packs for dashboard framing.
 * Frontend/config only; does not affect backend scoring or pipelines.
 */

export type B2BProfilePackId =
  | "general-b2b"
  | "b2b-saas"
  | "logistics"
  | "fintech-b2b"
  | "cybersecurity"
  | "manufacturing-b2b"
  | "professional-services"
  | "hr-tech"
  | "ecommerce-b2b";

export type MetricCopyKey =
  | "totalProcessed"
  | "highFitLeads"
  | "avgQaScore"
  | "totalRunCost";

export interface B2BProfilePack {
  id: B2BProfilePackId;
  displayName: string;
  description: string;
  targetUser: string;
  priorities: string[];
  salesAngles: string[];
  lowEvidenceWarning: string;
  metricCopyOverride?: Partial<Record<MetricCopyKey, string>>;
}

export const DEFAULT_PROFILE_PACK_ID: B2BProfilePackId = "general-b2b";

export const HONEST_FRAMING_NOTE =
  "Profile packs adjust review guidance and framing. They do not replace the core ICP scoring model.";

export const B2B_PROFILE_PACKS: B2BProfilePack[] = [
  {
    id: "general-b2b",
    displayName: "General B2B / Revenue Ops",
    description:
      "Default framing for mixed B2B pipelines where ICP fit spans industries and buying motions.",
    targetUser: "Revenue Operations Manager or Head of Sales",
    priorities: [
      "Pipeline quality and rep productivity over raw lead volume",
      "Consistent qualification signals across heterogeneous accounts",
      "Review speed for high-fit leads without skipping evidence checks",
      "Cost-per-lead visibility for batch runs",
    ],
    salesAngles: [
      "Tie outreach to measurable pipeline outcomes, not generic automation claims.",
      "Highlight how structured research reduces rep prep time per account.",
      "Position human review as a quality gate, not a bottleneck.",
    ],
    lowEvidenceWarning:
      "Sparse firmographics or missing context — validate ICP fit manually before approving outreach.",
    metricCopyOverride: {
      totalProcessed: "leads reviewed in this run",
      highFitLeads: "meeting your ICP threshold (score ≥ 70)",
      avgQaScore: "draft quality across the batch",
      totalRunCost: "estimated inference cost for this run",
    },
  },
  {
    id: "b2b-saas",
    displayName: "B2B SaaS",
    description:
      "Framing for subscription software sellers targeting growth, sales, and RevOps leaders.",
    targetUser: "VP Sales, Head of Growth, or RevOps Lead",
    priorities: [
      "ARR expansion signals and hiring in GTM roles",
      "Product-led vs sales-led motion clues in public data",
      "Champion role fit (RevOps vs AE manager vs CRO)",
      "Personalization that references stack and growth stage, not feature dumps",
    ],
    salesAngles: [
      "Anchor on pipeline velocity and forecast accuracy, not generic AI hype.",
      "Reference integration or workflow friction only when evidence supports it.",
      "Offer a low-commitment next step aligned to quarterly planning cycles.",
    ],
    lowEvidenceWarning:
      "Limited SaaS context (pricing page, integrations, GTM hiring) — confirm motion and segment before sending.",
    metricCopyOverride: {
      highFitLeads: "likely expansion or new-logo targets (score ≥ 70)",
      avgQaScore: "messaging fit for SaaS buyers",
    },
  },
  {
    id: "logistics",
    displayName: "Logistics",
    description:
      "Framing for freight, 3PL, fleet, and supply-chain operators selling into operations leaders.",
    targetUser: "Sales Operations Lead or Commercial Director",
    priorities: [
      "Network scale, lane complexity, and service-level pressures",
      "Operational efficiency and cost-per-shipment narratives",
      "Multi-site or cross-border complexity in account research",
      "Risk flags around thin margins and long sales cycles",
    ],
    salesAngles: [
      "Lead with on-time performance and cost control, not abstract digital transformation.",
      "Cite capacity, routing, or visibility pain only when evidence is present.",
      "Respect procurement-heavy buying — suggest operational discovery, not instant demos.",
    ],
    lowEvidenceWarning:
      "Thin logistics footprint in sources — verify service scope (3PL vs asset-based) before outreach.",
    metricCopyOverride: {
      totalProcessed: "accounts in this logistics batch",
      highFitLeads: "ops-heavy targets worth prioritizing (score ≥ 70)",
    },
  },
  {
    id: "fintech-b2b",
    displayName: "Fintech B2B",
    description:
      "Framing for B2B payments, banking infrastructure, and compliance-sensitive financial products.",
    targetUser: "Head of Growth, Partnerships Lead, or Sales Director",
    priorities: [
      "Regulatory and trust signals in positioning",
      "Buyer role clarity (finance vs product vs risk)",
      "Evidence-backed claims — avoid speculative compliance language",
      "Enterprise vs SMB motion fit from firmographics",
    ],
    salesAngles: [
      "Emphasize risk reduction and audit-friendly workflows, not speed alone.",
      "Reference integration or reconciliation pain only with cited evidence.",
      "Propose security-conscious discovery aligned to vendor review cycles.",
    ],
    lowEvidenceWarning:
      "Missing regulatory or product context — do not infer compliance readiness from sparse data.",
    metricCopyOverride: {
      avgQaScore: "tone and claim safety for regulated buyers",
      totalRunCost: "run cost (review high-stakes drafts carefully)",
    },
  },
  {
    id: "cybersecurity",
    displayName: "Cybersecurity",
    description:
      "Framing for security vendors selling to IT, security, and risk stakeholders.",
    targetUser: "Director of Sales or Security Solutions AE",
    priorities: [
      "Threat landscape relevance without fear-mongering",
      "Buyer persona fit (CISO vs IT manager vs SOC lead)",
      "Technical accuracy in outreach — hallucination risk is critical",
      "Evidence for stack, incidents, or compliance drivers when available",
    ],
    salesAngles: [
      "Lead with measurable risk reduction and operational burden, not buzzwords.",
      "Avoid naming specific breaches or tools unless evidence supports it.",
      "Offer technical validation steps appropriate for security procurement.",
    ],
    lowEvidenceWarning:
      "Weak security context in research — verify stack and priorities before citing threats or tools.",
    metricCopyOverride: {
      highFitLeads: "security-relevant targets (score ≥ 70)",
      avgQaScore: "factual accuracy and tone for security buyers",
    },
  },
  {
    id: "manufacturing-b2b",
    displayName: "Manufacturing B2B",
    description:
      "Framing for industrial and manufacturing sellers with long cycles and operations-led buyers.",
    targetUser: "Sales Director or Business Development Manager",
    priorities: [
      "Plant scale, production complexity, and supply-chain dependencies",
      "Operations and procurement stakeholder mapping",
      "Capital expenditure vs opex buying signals when visible",
      "Conservative tone — avoid overpromising quick wins",
    ],
    salesAngles: [
      "Connect to throughput, downtime, or quality outcomes when evidence exists.",
      "Respect long evaluation timelines — suggest plant-level discovery.",
      "Highlight integration with existing MES/ERP only if research supports it.",
    ],
    lowEvidenceWarning:
      "Limited operational detail — confirm facility scope and buyer role before technical claims.",
    metricCopyOverride: {
      totalProcessed: "manufacturing accounts in this run",
      highFitLeads: "plants or groups worth field sales focus (score ≥ 70)",
    },
  },
  {
    id: "professional-services",
    displayName: "Professional Services",
    description:
      "Framing for consulting, agencies, and advisory firms selling expertise-led engagements.",
    targetUser: "Director of Business Development or Practice Lead",
    priorities: [
      "Relationship-led selling and executive sponsor access",
      "Case-study relevance without overstating prior work",
      "Project scope clarity in outreach (assessment vs retainer vs sprint)",
      "Partner and procurement dynamics on larger accounts",
    ],
    salesAngles: [
      "Lead with a specific business outcome hypothesis, not a capabilities brochure.",
      "Offer a credible point of view tied to the prospect's industry pressures.",
      "Propose a bounded discovery conversation, not an open-ended pitch.",
    ],
    lowEvidenceWarning:
      "Sparse account narrative — validate practice fit and sponsor level before thought-leadership claims.",
    metricCopyOverride: {
      avgQaScore: "credibility and specificity for services buyers",
    },
  },
  {
    id: "hr-tech",
    displayName: "HR Tech",
    description:
      "Framing for HRIS, talent, payroll, and people-ops software selling to HR and People leaders.",
    targetUser: "VP of Partnerships or HR Tech Account Executive",
    priorities: [
      "Headcount growth, hiring velocity, and distributed workforce signals",
      "HR vs Finance vs IT buyer identification",
      "Change-management sensitivity in messaging",
      "Compliance and employee-experience themes when evidenced",
    ],
    salesAngles: [
      "Anchor on manager time saved and employee experience, not feature checklists.",
      "Reference HR stack friction only when research supports it.",
      "Align CTAs to planning cycles (open enrollment, fiscal year, hiring pushes).",
    ],
    lowEvidenceWarning:
      "Thin people-ops context — confirm HR tech maturity and buyer role before positioning.",
    metricCopyOverride: {
      highFitLeads: "HR-led opportunities worth prioritizing (score ≥ 70)",
    },
  },
  {
    id: "ecommerce-b2b",
    displayName: "Ecommerce B2B",
    description:
      "Framing for B2B commerce, wholesale, and marketplace operators selling to merchandising and ops leaders.",
    targetUser: "Head of B2B Commerce or Sales Operations Manager",
    priorities: [
      "Catalog complexity, channel mix, and order volume signals",
      "Self-serve vs rep-assisted buying motion clues",
      "Margin and fulfillment pressures in positioning",
      "Integration with ERP, PIM, or OMS when mentioned in research",
    ],
    salesAngles: [
      "Lead with order efficiency and buyer experience, not consumer-style hype.",
      "Cite catalog or fulfillment pain only with supporting evidence.",
      "Propose a pilot scoped to one segment or region when account is large.",
    ],
    lowEvidenceWarning:
      "Limited commerce stack detail — verify wholesale vs DTC-B2B motion before technical claims.",
    metricCopyOverride: {
      totalProcessed: "B2B commerce accounts in this run",
      totalRunCost: "batch cost — weigh against catalog complexity",
    },
  },
];

const PACK_BY_ID = new Map<B2BProfilePackId, B2BProfilePack>(
  B2B_PROFILE_PACKS.map((pack) => [pack.id, pack]),
);

export function getProfilePack(id: B2BProfilePackId): B2BProfilePack {
  return PACK_BY_ID.get(id) ?? PACK_BY_ID.get(DEFAULT_PROFILE_PACK_ID)!;
}

/** Keyword hints for auto-suggest only (never auto-applies). */
const INDUSTRY_HINTS: Array<{ profileId: B2BProfilePackId; patterns: RegExp[] }> = [
  { profileId: "b2b-saas", patterns: [/b2b\s*saas/i, /\bsaas\b/i, /software as a service/i] },
  {
    profileId: "logistics",
    patterns: [/logistics/i, /supply\s*chain/i, /freight/i, /3pl/i],
  },
  { profileId: "fintech-b2b", patterns: [/fintech/i, /payments/i, /banking/i] },
  {
    profileId: "cybersecurity",
    patterns: [/cyber/i, /security software/i, /infosec/i],
  },
  {
    profileId: "manufacturing-b2b",
    patterns: [/manufactur/i, /industrial/i],
  },
  {
    profileId: "professional-services",
    patterns: [/consult/i, /professional services/i, /advisory/i],
  },
  { profileId: "hr-tech", patterns: [/hr\s*tech/i, /human resources/i, /\bhris\b/i] },
  {
    profileId: "ecommerce-b2b",
    patterns: [/e-?commerce/i, /wholesale/i, /b2b commerce/i, /marketplace/i],
  },
];

/**
 * Returns a suggested profile when a batch has a dominant industry
 * match (≥50% of non-empty industries). Does not change selection.
 */
export function suggestProfileFromIndustries(
  industries: string[],
): B2BProfilePackId | null {
  const normalized = industries
    .map((i) => i.trim())
    .filter((i) => i.length > 0);
  if (normalized.length === 0) return null;

  const counts = new Map<B2BProfilePackId, number>();
  for (const industry of normalized) {
    for (const { profileId, patterns } of INDUSTRY_HINTS) {
      if (patterns.some((p) => p.test(industry))) {
        counts.set(profileId, (counts.get(profileId) ?? 0) + 1);
      }
    }
  }

  let best: B2BProfilePackId | null = null;
  let bestCount = 0;
  for (const [id, count] of counts) {
    if (count > bestCount) {
      bestCount = count;
      best = id;
    }
  }

  if (!best || bestCount / normalized.length < 0.5) return null;
  return best;
}

export function isValidProfilePackId(value: string): value is B2BProfilePackId {
  return PACK_BY_ID.has(value as B2BProfilePackId);
}
